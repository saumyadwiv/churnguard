"""
mongo.py — MongoDB operations for ChurnGuard Module 4
Handles all database reads and writes for customer history,
predictions, outcomes, and retention effectiveness.
"""

import os
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/churnguard")
DB_NAME   = os.getenv("DB_NAME", "churnguard")

# ── Connection ─────────────────────────────────────────────────────────────────
_client = None
_offline_mode = False

def get_db():
    """Return database connection. Reuses existing connection. Returns None if offline."""
    global _client, _offline_mode
    if _client is None:
        try:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            _client.admin.command("ping")  # Test connection
        except Exception as e:
            print(f"⚠️  MongoDB unavailable ({type(e).__name__}). Running in offline mode.")
            _offline_mode = True
            _client = None
    return _client[DB_NAME] if _client is not None else None


def test_connection() -> bool:
    """Returns True if MongoDB connection works, False otherwise."""
    try:
        db = get_db()
        if db is None:
            return False
        db.command("ping")
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════
# PREDICTION OPERATIONS
# ══════════════════════════════════════════════════════════════════

def save_prediction(customer_id: str,
                    churn_prob: float,
                    risk_level: str,
                    will_churn: bool,
                    threshold: float,
                    input_data: dict) -> str:
    """
    Save a prediction to MongoDB.
    Returns the inserted document ID as string.
    In offline mode, returns empty string (data not persisted).

    input_data should contain the raw customer values:
    tenure, monthly_charges, contract, internet, tech_support etc.
    """
    db  = get_db()
    if db is None:
        return ""  # offline mode
    
    doc = {
        "customer_id"  : customer_id.strip(),
        "predicted_at" : datetime.utcnow(),
        "churn_prob"   : round(churn_prob, 4),
        "risk_level"   : risk_level,         # High / Medium / Low
        "will_churn"   : bool(will_churn),
        "threshold"    : float(threshold),
        "input_data"   : input_data,         # raw customer fields
        "outcome"      : None,               # filled in after team acts
        "action_taken" : None,               # what retention offer was given
        "agent_name"   : None,               # who made the call
        "notes"        : None,               # free-text notes
        "outcome_at"   : None,               # when outcome was recorded
    }
    result = db.predictions.insert_one(doc)
    return str(result.inserted_id)


def get_all_predictions(limit: int = 1000) -> list:
    """
    Get all predictions, newest first.
    Returns list of dicts with string _id.
    Returns empty list in offline mode.
    """
    db   = get_db()
    if db is None:
        return []  # offline mode
    
    docs = db.predictions.find(
        {},
        sort=[("predicted_at", DESCENDING)],
        limit=limit
    )
    results = []
    for d in docs:
        d["_id"] = str(d["_id"])
        results.append(d)
    return results


def get_customer_history(customer_id: str) -> list:
    """Get all prediction records for a single customer, newest first.
    Returns empty list in offline mode.
    """
    db   = get_db()
    if db is None:
        return []  # offline mode
    
    docs = list(db.predictions.find(
        {"customer_id": customer_id.strip()},
        sort=[("predicted_at", DESCENDING)]
    ))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


def customer_exists(customer_id: str) -> bool:
    """Check if a customer_id has any predictions saved.
    Returns False in offline mode.
    """
    db = get_db()
    if db is None:
        return False  # offline mode
    
    return db.predictions.count_documents(
        {"customer_id": customer_id.strip()}
    ) > 0


# ══════════════════════════════════════════════════════════════════
# OUTCOME OPERATIONS
# ══════════════════════════════════════════════════════════════════

VALID_OUTCOMES = ["retained", "churned", "pending", "no_action"]

RETENTION_ACTIONS = [
    "None / no action taken",
    "Offered annual contract discount",
    "Offered 3 months free tech support",
    "Offered loyalty discount on monthly charges",
    "Assigned dedicated account manager",
    "Sent personalised retention email",
    "Proactive support call",
    "Offered device protection plan",
    "Offered streaming bundle upgrade",
    "Other",
]


def record_outcome(customer_id: str,
                   outcome: str,
                   action_taken: str = "",
                   agent_name: str   = "",
                   notes: str        = "") -> bool:
    """
    Record the outcome for a customer after a retention attempt.

    Updates the most recent prediction document for this customer
    AND inserts a separate outcome document for history tracking.

    outcome must be one of: retained | churned | pending | no_action
    Returns True if successful, False otherwise.
    Returns False in offline mode (data not persisted).
    """
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {VALID_OUTCOMES}")

    db  = get_db()
    if db is None:
        return False  # offline mode
    
    now = datetime.utcnow()

    update_fields = {
        "outcome"    : outcome,
        "action_taken": action_taken,
        "agent_name" : agent_name,
        "notes"      : notes,
        "outcome_at" : now,
    }

    # Update the most recent prediction for this customer
    result = db.predictions.update_one(
        {"customer_id": customer_id.strip()},
        {"$set": update_fields},
        sort=[("predicted_at", DESCENDING)]  # target the newest prediction
    )

    # Also save a standalone outcome record for audit trail
    db.outcomes.insert_one({
        "customer_id" : customer_id.strip(),
        "recorded_at" : now,
        "outcome"     : outcome,
        "action_taken": action_taken,
        "agent_name"  : agent_name,
        "notes"       : notes,
    })

    return result.modified_count > 0


# ══════════════════════════════════════════════════════════════════
# ANALYTICS & EFFECTIVENESS
# ══════════════════════════════════════════════════════════════════

def get_retention_effectiveness() -> list:
    """
    Which retention actions have the highest success rate?

    Returns list of dicts sorted by success_rate descending.
    Each dict has: action, total, retained, churned, success_rate
    Uses MongoDB aggregation pipeline for efficiency.
    Returns empty list in offline mode.
    """
    db = get_db()
    if db is None:
        return []  # offline mode

    pipeline = [
        # Only include records that have an outcome AND an action
        {"$match": {
            "outcome"     : {"$in": ["retained", "churned"]},
            "action_taken": {"$exists": True, "$ne": None, "$ne": "", "$ne": "None / no action taken"},
        }},
        # Group by action and count outcomes
        {"$group": {
            "_id"     : "$action_taken",
            "total"   : {"$sum": 1},
            "retained": {"$sum": {
                "$cond": [{"$eq": ["$outcome", "retained"]}, 1, 0]
            }},
            "churned" : {"$sum": {
                "$cond": [{"$eq": ["$outcome", "churned"]}, 1, 0]
            }},
        }},
        # Calculate success rate
        {"$project": {
            "action"      : "$_id",
            "total"       : 1,
            "retained"    : 1,
            "churned"     : 1,
            "success_rate": {
                "$round": [
                    {"$multiply": [
                        {"$divide": ["$retained", "$total"]}, 100
                    ]}, 1
                ]
            },
        }},
        {"$sort": {"success_rate": -1}},
    ]

    results = list(db.outcomes.aggregate(pipeline))
    for r in results:
        r["_id"] = str(r.get("_id", ""))
    return results


def get_dashboard_kpis() -> dict:
    """
    Top-level numbers for the Module 4 dashboard header.
    All counts come from a single MongoDB query each for speed.
    Returns default zeros in offline mode.
    """
    db = get_db()
    if db is None:
        return {
            "total_tracked"  : 0,
            "at_risk"        : 0,
            "retained"       : 0,
            "churned"        : 0,
            "pending"        : 0,
            "retention_rate" : 0.0,
        }  # offline mode

    total    = db.predictions.count_documents({})
    at_risk  = db.predictions.count_documents({"will_churn": True})
    retained = db.outcomes.count_documents({"outcome": "retained"})
    churned  = db.outcomes.count_documents({"outcome": "churned"})
    pending  = db.outcomes.count_documents({"outcome": "pending"})

    total_actioned  = retained + churned
    retention_rate  = round(retained / max(total_actioned, 1) * 100, 1)

    return {
        "total_tracked"  : total,
        "at_risk"        : at_risk,
        "retained"       : retained,
        "churned"        : churned,
        "pending"        : pending,
        "retention_rate" : retention_rate,
    }


def get_predictions_as_df() -> pd.DataFrame:
    """
    Return all predictions as a clean pandas DataFrame
    ready for display in Streamlit.
    """
    docs = get_all_predictions()
    if not docs:
        return pd.DataFrame()

    rows = []
    for d in docs:
        inp = d.get("input_data", {})
        rows.append({
            "Customer ID"    : d.get("customer_id", ""),
            "Predicted At"   : d.get("predicted_at", ""),
            "Churn Prob (%)" : round(d.get("churn_prob", 0) * 100, 1),
            "Risk Level"     : d.get("risk_level", ""),
            "Will Churn"     : "Yes" if d.get("will_churn") else "No",
            "Contract"       : inp.get("contract", ""),
            "Tenure (mo)"    : inp.get("tenure", ""),
            "Monthly ($)"    : inp.get("monthly_charges", ""),
            "Outcome"        : d.get("outcome") or "—",
            "Action Taken"   : d.get("action_taken") or "—",
            "Agent"          : d.get("agent_name") or "—",
            "Notes"          : d.get("notes") or "—",
        })

    df = pd.DataFrame(rows)

    # Format datetime
    if "Predicted At" in df.columns:
        df["Predicted At"] = pd.to_datetime(
            df["Predicted At"]
        ).dt.strftime("%Y-%m-%d %H:%M")

    return df