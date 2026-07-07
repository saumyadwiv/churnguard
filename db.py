"""
db.py — MongoDB database layer for ChurnGuard Pro
Each user's data is completely isolated by their account email.
Users can authenticate with an email+password or with Google OAuth;
both paths resolve to a single `users` document keyed on `email`.
"""

from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from datetime import datetime
from typing import Optional
import os
import bcrypt
import streamlit as st


# ── Connection ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    """
    Connect to MongoDB Atlas.
    URI is read from st.secrets["MONGO_URI"] or environment variable.
    Returns None if connection fails (app will work in offline mode).
    """
    try:
        uri = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI", "")
        if not uri:
            print("⚠️  MongoDB URI not set. Running in offline dev mode.")
            return None
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")          # verify connection
        return client["churnguard"]           # database name
    except Exception as e:
        # Catch all connection errors (DNS, timeout, auth, etc.)
        print(f"⚠️  MongoDB connection unavailable: {type(e).__name__}")
        print("✓ Running in offline dev mode. Data will not persist.")
        return None


def get_collection(name: str):
    db = get_db()
    return db[name] if db is not None else None


# ── Indexes (run once on startup) ──────────────────────────────────────────────
def ensure_indexes():
    """Create indexes for fast queries. Safe to call multiple times."""
    try:
        users = get_collection("users")
        if users is not None:
            users.create_index("email", unique=True)

        preds = get_collection("predictions")
        if preds is not None:
            preds.create_index([("user_email", 1), ("predicted_at", DESCENDING)])
            preds.create_index("customer_id")

        outcomes = get_collection("outcomes")
        if outcomes is not None:
            outcomes.create_index([("user_email", 1), ("customer_id", 1)])
    except Exception:
        pass   # indexes already exist or DB not connected


# ══════════════════════════════════════════════════════════════════
# USER OPERATIONS
# ══════════════════════════════════════════════════════════════════

def upsert_user(email: str, name: str, picture: str = "") -> dict:
    """
    Create or update a user on login.
    Returns the user document.
    In offline mode, returns a mock user document.
    """
    users = get_collection("users")
    if users is None:
        # Offline mode: return a mock user document
        return {
            "email"      : email,
            "name"       : name,
            "picture"    : picture,
            "tier"       : "free",
            "pred_count" : 0,
            "created_at" : datetime.utcnow(),
            "last_login" : datetime.utcnow(),
            "_offline"   : True,  # flag indicating this is a mock document
        }
    
    now = datetime.utcnow()
    users.update_one(
        {"email": email},
        {
            "$set" : {"name": name, "picture": picture, "last_login": now},
            "$setOnInsert": {
                "email"      : email,
                "created_at" : now,
                "tier"       : "free",
                "pred_count" : 0,
            },
        },
        upsert=True,
    )
    return users.find_one({"email": email})


def get_user(email: str) -> Optional[dict]:
    users = get_collection("users")
    return users.find_one({"email": email}) if users is not None else None


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt. Returns a UTF-8 string safe to store."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_user_with_password(email: str, name: str, password_hash: str) -> Optional[dict]:
    """
    Create a brand-new email+password account, OR attach a password to an
    existing Google-only account that has no password_hash yet (so the same
    email always maps to exactly one account regardless of how it was created).

    Returns the user document on success, or None if an account with a
    password already exists for this email (caller should treat this as a
    duplicate-account error).
    """
    users = get_collection("users")
    now = datetime.utcnow()

    if users is None:
        # Offline mode: return a mock user document
        return {
            "email"         : email,
            "name"          : name,
            "picture"       : "",
            "tier"          : "free",
            "pred_count"    : 0,
            "password_hash" : password_hash,
            "created_at"    : now,
            "last_login"    : now,
            "_offline"      : True,
        }

    existing = users.find_one({"email": email})
    if existing is not None and existing.get("password_hash"):
        return None  # duplicate account — a password is already set

    users.update_one(
        {"email": email},
        {
            "$set": {
                "name"          : name,
                "password_hash" : password_hash,
                "last_login"    : now,
            },
            "$setOnInsert": {
                "email"      : email,
                "picture"    : "",
                "tier"       : "free",
                "pred_count" : 0,
                "created_at" : now,
            },
        },
        upsert=True,
    )
    return users.find_one({"email": email})


def verify_password(email: str, password: str) -> Optional[dict]:
    """
    Check email + password against the stored bcrypt hash.
    Returns the user document if valid, otherwise None (also None if this
    account has no password set, e.g. it was created via Google sign-in).
    """
    users = get_collection("users")
    if users is None:
        return None

    user = users.find_one({"email": email})
    if user is None or not user.get("password_hash"):
        return None

    try:
        stored_hash = user["password_hash"].encode("utf-8")
    except (AttributeError, UnicodeEncodeError):
        return None

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return None

    users.update_one({"email": email}, {"$set": {"last_login": datetime.utcnow()}})
    return user


def increment_pred_count(email: str):
    users = get_collection("users")
    if users is not None:
        users.update_one({"email": email}, {"$inc": {"pred_count": 1}})


# ══════════════════════════════════════════════════════════════════
# PREDICTION OPERATIONS
# ══════════════════════════════════════════════════════════════════

def save_prediction(
    user_email    : str,
    customer_id   : str,
    churn_prob    : float,
    risk_level    : str,
    will_churn    : bool,
    threshold     : float,
    input_data    : dict,
    tenure        : int   = 0,
    monthly       : float = 0.0,
    contract      : str   = "",
    internet      : str   = "",
    tech          : str   = "",
) -> str:
    """Save a prediction. Returns the inserted document ID."""
    preds = get_collection("predictions")
    if preds is None:
        return ""
    doc = {
        "user_email"    : user_email,
        "customer_id"   : customer_id,
        "predicted_at"  : datetime.utcnow(),
        "churn_prob"    : round(churn_prob, 4),
        "risk_level"    : risk_level,
        "will_churn"    : will_churn,
        "threshold"     : threshold,
        "input_data"    : input_data,
        "tenure"        : tenure,
        "monthly"       : monthly,
        "contract"      : contract,
        "internet"      : internet,
        "tech"          : tech,
    }
    result = preds.insert_one(doc)
    increment_pred_count(user_email)
    return str(result.inserted_id)


def get_user_predictions(user_email: str, limit: int = 100) -> list:
    """Get recent predictions for a user, sorted newest first."""
    preds = get_collection("predictions")
    if preds is None:
        return []
    cursor = preds.find(
        {"user_email": user_email},
        sort=[("predicted_at", DESCENDING)],
        limit=limit,
    )
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("predicted_at"), datetime):
            doc["predicted_at"] = doc["predicted_at"].strftime("%Y-%m-%d %H:%M")
        results.append(doc)
    return results


def get_prediction_by_customer(user_email: str, customer_id: str) -> list:
    """Get all predictions for a specific customer (belonging to this user)."""
    preds = get_collection("predictions")
    if preds is None:
        return []
    cursor = preds.find(
        {"user_email": user_email, "customer_id": customer_id},
        sort=[("predicted_at", DESCENDING)],
    )
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("predicted_at"), datetime):
            doc["predicted_at"] = doc["predicted_at"].strftime("%Y-%m-%d %H:%M")
        results.append(doc)
    return results


# ══════════════════════════════════════════════════════════════════
# OUTCOME OPERATIONS
# ══════════════════════════════════════════════════════════════════

def record_outcome(
    user_email       : str,
    customer_id      : str,
    outcome          : str,
    retention_action : str = "",
    notes            : str = "",
    agent_name       : str = "",
) -> str:
    """Record what happened after a prediction."""
    outcomes = get_collection("outcomes")
    if outcomes is None:
        return ""
    doc = {
        "user_email"       : user_email,
        "customer_id"      : customer_id,
        "recorded_at"      : datetime.utcnow(),
        "outcome"          : outcome,
        "retention_action" : retention_action,
        "notes"            : notes,
        "agent_name"       : agent_name,
    }
    result = outcomes.insert_one(doc)
    return str(result.inserted_id)


def get_user_outcomes(user_email: str) -> list:
    """Get all outcomes recorded by this user."""
    outcomes = get_collection("outcomes")
    if outcomes is None:
        return []
    cursor = outcomes.find(
        {"user_email": user_email},
        sort=[("recorded_at", DESCENDING)],
    )
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("recorded_at"), datetime):
            doc["recorded_at"] = doc["recorded_at"].strftime("%Y-%m-%d %H:%M")
        results.append(doc)
    return results


def get_customer_full_history(user_email: str, customer_id: str) -> dict:
    """Get all predictions + outcomes for one customer (this user's data only)."""
    return {
        "predictions": get_prediction_by_customer(user_email, customer_id),
        "outcomes"   : [
            o for o in get_user_outcomes(user_email)
            if o["customer_id"] == customer_id
        ],
    }


# ══════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ══════════════════════════════════════════════════════════════════

def get_user_kpis(user_email: str) -> dict:
    """Top-level KPIs for the history dashboard."""
    preds    = get_collection("predictions")
    outcomes = get_collection("outcomes")

    if preds is None:
        return {"total": 0, "at_risk": 0, "retained": 0,
                "churned": 0, "pending": 0, "retention_rate": 0}

    total   = preds.count_documents({"user_email": user_email})
    at_risk = preds.count_documents({"user_email": user_email, "will_churn": True})

    ret_col = outcomes if outcomes is not None else get_collection("outcomes")

    if ret_col is not None:
        retained = ret_col.count_documents({"user_email": user_email, "outcome": "retained"})
        churned  = ret_col.count_documents({"user_email": user_email, "outcome": "churned"})
        pending  = ret_col.count_documents({"user_email": user_email, "outcome": "pending"})
    else:
        retained = churned = pending = 0

    rate = round(retained / max(retained + churned, 1) * 100, 1)
    return {
        "total"          : total,
        "at_risk"        : at_risk,
        "retained"       : retained,
        "churned"        : churned,
        "pending"        : pending,
        "retention_rate" : rate,
    }


def get_retention_stats(user_email: str) -> list:
    """Which retention actions are most effective for this user's data."""
    outcomes = get_collection("outcomes")
    if outcomes is None:
        return []
    pipeline = [
        {"$match": {
            "user_email": user_email,
            "retention_action": {"$ne": ""},
            "outcome": {"$in": ["retained", "churned"]},
        }},
        {"$group": {
            "_id"     : "$retention_action",
            "total"   : {"$sum": 1},
            "retained": {"$sum": {"$cond": [{"$eq": ["$outcome", "retained"]}, 1, 0]}},
            "churned" : {"$sum": {"$cond": [{"$eq": ["$outcome", "churned"]},  1, 0]}},
        }},
        {"$sort": {"total": -1}},
    ]
    results = []
    for doc in outcomes.aggregate(pipeline):
        rate = round(doc["retained"] / max(doc["total"], 1) * 100, 1)
        results.append({
            "action"      : doc["_id"],
            "total"       : doc["total"],
            "retained"    : doc["retained"],
            "churned"     : doc["churned"],
            "success_rate": rate,
        })
    return sorted(results, key=lambda x: x["success_rate"], reverse=True)


def get_risk_trend(user_email: str) -> list:
    """
    Returns daily prediction counts by risk level for the last 30 days.
    Used for the trend chart in the dashboard.
    """
    preds = get_collection("predictions")
    if preds is None:
        return []
    pipeline = [
        {"$match": {"user_email": user_email}},
        {"$group": {
            "_id": {
                "date"      : {"$dateToString": {"format": "%Y-%m-%d", "date": "$predicted_at"}},
                "risk_level": "$risk_level",
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.date": 1}},
    ]
    return list(preds.aggregate(pipeline))  