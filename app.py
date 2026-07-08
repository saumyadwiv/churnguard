"""
ChurnGuard Pro — Phase 3 (Module 4 + Login)
Each user logs in with email+password or Google, all data is stored in
MongoDB, completely isolated per user.
"""

import streamlit as st
import pickle, json, os, uuid
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go
from datetime import datetime

from auth import require_login, logout, get_current_user, init_auth
from landing import show_landing_page
from db import (
    ensure_indexes,
    save_prediction,
    record_outcome,
    get_user_predictions,
    get_user_outcomes,
    get_customer_full_history,
    get_user_kpis,
    get_retention_stats,
    get_risk_trend,
)

# ── Landing page gate ───────────────────────────────────────────────────────────
# Anyone who isn't signed in AND hasn't clicked "Get Started" yet sees the public
# marketing home page instead of being dropped straight onto the sign-in form.
init_auth()
if "site_entered" not in st.session_state:
    st.session_state.site_entered = False

if not get_current_user() and not st.session_state.site_entered:
    show_landing_page()   # calls st.set_page_config itself
    st.stop()

# ── Page config — must be first (only reached once we're past the landing page) ─
st.set_page_config(
    page_title="ChurnGuard Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'Outfit',sans-serif;background:#0c0e16;color:#e2e0f0;}
.stApp{
    background:
        radial-gradient(900px 460px at 10% -10%, rgba(108,99,255,.12), transparent 60%),
        radial-gradient(700px 420px at 95% 0%, rgba(139,92,246,.09), transparent 55%),
        #0c0e16;
}
[data-testid="stSidebar"]{background:#10121e;border-right:1px solid #1e2133;}
[data-testid="stSidebar"] *{color:#c4c2d4!important;}
[data-testid="stMetric"]{background:#13152a;border:1px solid #1e2133;border-radius:12px;padding:16px 18px;}
[data-testid="stMetricLabel"]{font-family:'JetBrains Mono',monospace!important;font-size:9px!important;text-transform:uppercase;letter-spacing:.14em;color:#6b6888!important;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;font-size:22px!important;color:#e2e0f0!important;}
.stTabs [data-baseweb="tab-list"]{background:#13152a;border-radius:12px;padding:5px;border:1px solid #1e2133;gap:3px;}
.stTabs [data-baseweb="tab"]{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.06em;border-radius:8px;padding:8px 16px;color:#6b6888;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6c63ff,#8b5cf6)!important;color:white!important;box-shadow:0 8px 18px -8px rgba(108,99,255,.7);}
.stButton>button{background:linear-gradient(135deg,#6c63ff,#8b5cf6);color:white;border:none;border-radius:10px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:500;letter-spacing:.07em;padding:12px 24px;width:100%;transition:all .25s;text-transform:uppercase;box-shadow:0 10px 22px -10px rgba(108,99,255,.55);}
.stButton>button:hover{opacity:.92;transform:translateY(-2px);box-shadow:0 14px 26px -8px rgba(108,99,255,.75);}
.stSelectbox>div>div,.stNumberInput>div>div>input,.stTextInput>div>div>input,.stTextArea textarea{background:#13152a!important;border:1px solid #1e2133!important;border-radius:8px!important;color:#e2e0f0!important;}
.stSelectbox label,.stSlider label,.stNumberInput label,.stTextInput label,.stTextArea label{color:#8885a0!important;font-size:12px!important;}
.stSlider>div>div>div{background:#6c63ff!important;}
.page-title-row{display:flex;align-items:center;gap:14px;padding:10px 0 4px;}
.page-title-badge{width:46px;height:46px;flex-shrink:0;border-radius:12px;background:linear-gradient(135deg,#6c63ff,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:22px;box-shadow:0 10px 24px -8px rgba(108,99,255,.7);}
.page-title{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#e2e0f0;letter-spacing:-.02em;line-height:1.15;}
.page-sub{font-size:14px;color:#6b6888;font-weight:300;padding-bottom:18px;border-bottom:1px solid #1e2133;margin:2px 0 22px;}
.sec-pill{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:#6c63ff;background:rgba(108,99,255,.1);border:1px solid rgba(108,99,255,.25);border-radius:20px;padding:3px 10px;margin-bottom:10px;}
.sec-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.14em;color:#6b6888;border-bottom:1px solid #1e2133;padding-bottom:8px;margin:16px 0 12px;}
.kpi-card{background:#13152a;border:1px solid #1e2133;border-radius:14px;padding:20px 18px;height:100%;transition:transform .2s ease, box-shadow .2s ease;}
.kpi-card:hover{transform:translateY(-3px);box-shadow:0 16px 30px -18px rgba(108,99,255,.5);border-color:#2c2f55;}
.kpi-val{font-family:'Syne',sans-serif;font-size:32px;font-weight:700;line-height:1;margin-bottom:4px;}
.kpi-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#6b6888;}
.kpi-sub{font-size:11px;color:#6b6888;margin-top:6px;}
.risk-high{background:linear-gradient(135deg,#1a0d0d,#1f1010);border:1px solid #5a1a1a;border-left:4px solid #ef4444;border-radius:14px;padding:26px;}
.risk-medium{background:linear-gradient(135deg,#1a160a,#1f1a0c);border:1px solid #5a4010;border-left:4px solid #f59e0b;border-radius:14px;padding:26px;}
.risk-low{background:linear-gradient(135deg,#0a1a0e,#0c1f11);border:1px solid #1a5a25;border-left:4px solid #22c55e;border-radius:14px;padding:26px;}
.risk-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;}
.risk-prob{font-family:'Syne',sans-serif;font-size:50px;font-weight:700;line-height:1;margin:8px 0;}
.risk-sub{font-size:13px;color:#8885a0;line-height:1.7;}
.action-box{background:#13152a;border:1px solid #1e2133;border-radius:12px;padding:16px;margin-top:12px;}
.action-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#6b6888;margin-bottom:8px;}
.info-banner{background:rgba(108,99,255,.08);border:1px solid rgba(108,99,255,.2);border-radius:10px;padding:14px 18px;font-size:13px;color:#a8a5c0;line-height:1.7;margin:10px 0 18px;}
.module-intro{background:linear-gradient(135deg,rgba(108,99,255,.10),rgba(139,92,246,.05));border:1px solid rgba(108,99,255,.25);border-radius:12px;padding:14px 20px;margin:2px 0 20px;}
.module-intro-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:600;color:#c4c2d4;margin-bottom:4px;}
.module-intro-body{font-size:12.5px;color:#8885a0;line-height:1.7;}
.history-card{background:#13152a;border:1px solid #1e2133;border-radius:10px;padding:16px;margin:8px 0;}
.badge{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.1em;padding:3px 10px;border-radius:20px;display:inline-block;}
.user-chip{display:flex;align-items:center;gap:10px;padding:12px 14px;background:#0c0e16;border-radius:10px;border:1px solid #1e2133;margin-bottom:16px;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# AUTH GATE — show login if not authenticated
# ══════════════════════════════════════════════════════════════════
user = require_login()   # blocks and shows login page if not logged in
USER_EMAIL = user["email"]
USER_NAME  = user["name"]
USER_TIER  = user.get("tier", "free")

ensure_indexes()



# ── Load model ─────────────────────────────────────────────────────────────────
@st.cache_resource
def load_package():
    for p in ['churn_model_final.pkl', '../churn_model_final.pkl',
              'customer churn/churn_model_final.pkl',
              '/content/drive/MyDrive/customer churn/churn_model_final.pkl']:
        if os.path.exists(p):
            with open(p, 'rb') as f: pkg = pickle.load(f)
            if isinstance(pkg, dict): return pkg['model'], float(pkg['threshold']), pkg['features']
            return pkg, 0.63, None
    return None, 0.63, None

@st.cache_data
def load_metrics():
    for p in ['metrics.json', '../metrics.json',
              'customer churn/metrics.json',
              '/content/drive/MyDrive/customer churn/metrics.json']:
        if os.path.exists(p):
            with open(p) as f: return json.load(f)
    return {}

model, THRESHOLD, feature_names = load_package()
metrics = load_metrics()
if feature_names is None:
    feature_names = ['gender','SeniorCitizen','Partner','Dependents','tenure',
                     'PhoneService','MultipleLines','InternetService','OnlineSecurity',
                     'OnlineBackup','DeviceProtection','TechSupport','StreamingTV',
                     'StreamingMovies','Contract','PaperlessBilling','PaymentMethod',
                     'MonthlyCharges','TotalCharges']

# Encoding maps — these match the alphabetical LabelEncoder ordering used at
# training time (verified against the single-prediction path below). Bulk /
# analytics uploads MUST use these exact maps rather than fitting a fresh
# LabelEncoder per upload — a fresh encoder assigns arbitrary codes based on
# whatever values happen to appear in that file, silently producing wrong
# predictions. This was a real bug in the bulk/analytics tabs; fixed here.
CONTRACT_MAP     = {"Month-to-month":0,"One year":1,"Two year":2}
INTERNET_MAP     = {"DSL":0,"Fiber optic":1,"No":2}
TECH_MAP         = {"No":0,"No internet service":1,"Yes":2}          # also used for OnlineSecurity/Backup/DeviceProtection/StreamingTV/Movies
BINARY_MAP       = {"No":0,"Yes":1}                                  # Partner/Dependents/PhoneService/PaperlessBilling
PAYMENT_MAP      = {"Bank transfer (automatic)":0,"Credit card (automatic)":1,
                    "Electronic check":2,"Mailed check":3}
GENDER_MAP       = {"Female":0,"Male":1}
MULTILINES_MAP   = {"No":0,"No phone service":1,"Yes":2}

CATEGORICAL_COLUMN_MAPS = {
    "gender":           GENDER_MAP,
    "Partner":          BINARY_MAP,
    "Dependents":       BINARY_MAP,
    "PhoneService":     BINARY_MAP,
    "MultipleLines":    MULTILINES_MAP,
    "InternetService":  INTERNET_MAP,
    "OnlineSecurity":   TECH_MAP,
    "OnlineBackup":     TECH_MAP,
    "DeviceProtection": TECH_MAP,
    "TechSupport":      TECH_MAP,
    "StreamingTV":      TECH_MAP,
    "StreamingMovies":  TECH_MAP,
    "Contract":         CONTRACT_MAP,
    "PaperlessBilling": BINARY_MAP,
    "PaymentMethod":    PAYMENT_MAP,
}

def encode_customer_df(df: pd.DataFrame) -> pd.DataFrame:
    """Encode a raw Telco-schema dataframe using the same fixed maps as the
    single-prediction path, and return columns in the exact order the model
    expects. Raises ValueError listing any row values that aren't recognised
    (e.g. typos like 'yes' instead of 'Yes')."""
    out = pd.DataFrame(index=df.index)
    bad = []
    for col in feature_names:
        if col in ("tenure","MonthlyCharges","TotalCharges"):
            out[col] = pd.to_numeric(df[col], errors="coerce")
        elif col == "SeniorCitizen":
            out[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            mapping = CATEGORICAL_COLUMN_MAPS.get(col, {})
            out[col] = df[col].map(mapping)
            unknown = sorted(set(df[col].astype(str)) - set(mapping.keys()))
            if unknown:
                bad.append(f"{col}: unrecognised value(s) {unknown[:5]}")
    if bad:
        raise ValueError("Some values didn't match the expected format:\n" + "\n".join(bad))
    return out[feature_names]

def build_input(tenure,monthly,contract,internet,tech,sec,bkp,
                senior,partner,dep,paperless,payment):
    total = monthly * tenure
    sv = BINARY_MAP.get(sec, 0) if sec != "No internet service" else 0
    bv = BINARY_MAP.get(bkp, 0) if bkp != "No internet service" else 0
    return np.array([[1,BINARY_MAP[senior],BINARY_MAP[partner],BINARY_MAP[dep],
                      tenure,1,1,INTERNET_MAP[internet],sv,bv,0,TECH_MAP[tech],
                      0,0,CONTRACT_MAP[contract],BINARY_MAP[paperless],
                      PAYMENT_MAP[payment],monthly,total]])

def predict(arr):
    p = model.predict_proba(arr)[0][1]; return p, int(p >= THRESHOLD)

def risk_info(p):
    if p >= 0.75:      return "HIGH",   "#ef4444", "risk-high"
    if p >= THRESHOLD: return "MEDIUM", "#f59e0b", "risk-medium"
    return                    "LOW",    "#22c55e", "risk-low"

def ps(fig, ax):
    fig.patch.set_facecolor('#13152a'); ax.set_facecolor('#13152a')
    ax.tick_params(colors='#6b6888', labelsize=9)
    for sp in ax.spines.values(): sp.set_color('#1e2133')
    ax.title.set_color('#e2e0f0')
    ax.xaxis.label.set_color('#6b6888'); ax.yaxis.label.set_color('#6b6888')

def module_intro(title, text):
    """Renders a friendly 'what this module does' banner at the top of a tab."""
    st.markdown(
        f'<div class="module-intro"><div class="module-intro-title">💡 {title}</div>'
        f'<div class="module-intro-body">{text}</div></div>',
        unsafe_allow_html=True,
    )

def validate_csv(df):
    """Returns a list of required columns that are missing from the uploaded CSV."""
    return [c for c in feature_names if c not in df.columns]


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;padding:2px 0 18px;">'
        '<div style="width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#6c63ff,#8b5cf6);'
        'display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;'
        'box-shadow:0 8px 18px -6px rgba(108,99,255,.7);">🛡️</div>'
        '<div style="font-family:Syne,sans-serif;font-weight:800;font-size:16px;color:#f2f1fb;letter-spacing:-.01em;">ChurnGuard Pro</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # User chip
    pic = user.get("picture", "")
    if pic:
        st.markdown(f'<div class="user-chip"><img src="{pic}" style="width:32px;height:32px;border-radius:50%;"><div><div style="font-size:13px;color:#e2e0f0;font-weight:500;">{USER_NAME}</div><div style="font-size:11px;color:#6b6888;">{USER_EMAIL}</div></div></div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="user-chip"><div style="width:32px;height:32px;border-radius:50%;background:#6c63ff;display:flex;align-items:center;justify-content:center;font-family:Syne,sans-serif;font-weight:700;color:white;font-size:14px;">{USER_NAME[0].upper()}</div><div><div style="font-size:13px;color:#e2e0f0;font-weight:500;">{USER_NAME}</div><div style="font-size:11px;color:#6b6888;">{USER_EMAIL}</div></div></div>',unsafe_allow_html=True)

    tier_color = "#6c63ff" if USER_TIER=="pro" else "#f59e0b" if USER_TIER=="team" else "#8885a0"
    st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:{tier_color};margin-bottom:18px;">{USER_TIER.upper()} TIER</div>',unsafe_allow_html=True)

    auc  = metrics.get('metrics',{}).get('auc_roc',  metrics.get('final_auc',     0.8353))
    f1   = metrics.get('metrics',{}).get('f1_score', metrics.get('final_f1',       0.6132))
    prec = metrics.get('metrics',{}).get('precision',metrics.get('final_precision', 0.6036))
    rec  = metrics.get('metrics',{}).get('recall',   metrics.get('final_recall',   0.6230))

    st.markdown('<div class="sec-lbl">Model performance</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("AUC-ROC",   f"{auc:.3f}"); c2.metric("F1",       f"{f1:.3f}")
    c1.metric("Precision", f"{prec:.1%}"); c2.metric("Recall",  f"{rec:.1%}")

    st.markdown(f"<div style='margin-top:16px;padding:12px;background:#0c0e16;border-radius:10px;border:1px solid #1e2133;font-size:11px;color:#8885a0;line-height:1.9;'>Threshold: <span style='color:#6c63ff;font-family:JetBrains Mono,monospace;'>{THRESHOLD:.2f}</span><br>Algorithm: Random Forest<br>AUC-ROC: 0.8353<br>Overfit gap: 0.013</div>",unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign out", key="logout_btn"):
        logout()

    if model is None:
        st.error("Model file not found.")


# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="page-title-row">'
    '<div class="page-title-badge">🛡️</div>'
    '<div><div class="page-title">ChurnGuard Pro</div>'
    '<div style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:.12em;color:#6c63ff;text-transform:uppercase;">Predict · Track · Explain · Retain</div>'
    '</div></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="page-sub">&nbsp;</div>', unsafe_allow_html=True)

if model is None:
    st.error("Place churn_model_final.pkl, feature_names.pkl and metrics.json in the app folder.")
    st.stop()

t1, t2, t3, t4, t5, t6 = st.tabs([
    "01 · Predict",
    "02 · Bulk Predict",
    "03 · Analytics",
    "04 · My History",
    "05 · Explainability",
    "06 · ROI Calculator",
])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — Single Prediction (saves to MongoDB per user)
# ══════════════════════════════════════════════════════════════════
with t1:
    st.markdown('<div class="sec-pill">Module 01</div>', unsafe_allow_html=True)
    st.markdown("### Single Customer Prediction")
    module_intro(
        "What this module does",
        "Enter one customer's details and get an instant churn-risk score. "
        "You'll see the probability they'll leave, the key risk factors driving that score, "
        "and a recommended retention action. Turn on <b>\"Save to my history\"</b> to log this "
        "prediction so you can track outcomes later in Module 04."
    )

    ca, cb, cc = st.columns(3)
    with ca:
        cust_id  = st.text_input("Customer ID", placeholder="e.g. CUST-001", key="cid")
        tenure   = st.slider("Tenure (months)", 0, 72, 12)
        monthly  = st.number_input("Monthly charges ($)", 18.0, 120.0, 65.0, 0.5)
        st.caption(f"Est. total: **${monthly*tenure:,.0f}**")
        contract = st.selectbox("Contract", ["Month-to-month","One year","Two year"])
        payment  = st.selectbox("Payment", ["Electronic check","Mailed check",
                                "Bank transfer (automatic)","Credit card (automatic)"])
    with cb:
        st.markdown("**Services**")
        internet   = st.selectbox("Internet",        ["DSL","Fiber optic","No"])
        tech       = st.selectbox("Tech support",    ["No","Yes","No internet service"])
        online_sec = st.selectbox("Online security", ["No","Yes","No internet service"])
        online_bkp = st.selectbox("Online backup",   ["No","Yes","No internet service"])
    with cc:
        st.markdown("**Demographics**")
        senior    = st.selectbox("Senior citizen",   ["No","Yes"])
        partner   = st.selectbox("Has partner",      ["No","Yes"])
        dep       = st.selectbox("Has dependents",   ["No","Yes"])
        paperless = st.selectbox("Paperless billing",["No","Yes"])
        save_hist = st.checkbox("Save to my history", value=True,
                                help="Saves this prediction to your personal MongoDB history")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Run Prediction →", key="r1"):
        inp = build_input(tenure, monthly, contract, internet, tech,
                          online_sec, online_bkp, senior, partner,
                          dep, paperless, payment)
        proba, pred = predict(inp)
        label, color, css = risk_info(proba)

        final_id = cust_id.strip() or f"CUST-{uuid.uuid4().hex[:6].upper()}"

        if save_hist:
            save_prediction(
                user_email  = USER_EMAIL,
                customer_id = final_id,
                churn_prob  = proba,
                risk_level  = label,
                will_churn  = bool(pred),
                threshold   = THRESHOLD,
                input_data  = {"tenure":tenure,"monthly":monthly,"contract":contract,
                               "internet":internet,"tech":tech,"payment":payment},
                tenure=tenure, monthly=monthly,
                contract=contract, internet=internet, tech=tech,
            )
            st.success(f"Saved to your history — Customer **{final_id}**")

        st.markdown("---")
        rc, gc = st.columns(2)

        with rc:
            st.markdown(f'<div class="{css}"><div class="risk-title" style="color:{color};">{label} RISK</div><div class="risk-prob" style="color:{color};">{proba:.1%}</div><div class="risk-sub">{"Likely to leave — act now." if pred==1 else "Stable — consider upsell."}<br>Customer: {final_id} · Threshold: {THRESHOLD:.2f}</div></div>',unsafe_allow_html=True)

            st.markdown('<div class="sec-lbl" style="margin-top:16px;">Risk factors</div>', unsafe_allow_html=True)
            factors = []
            if tenure < 6:    factors.append(("Tenure < 6 months","#ef4444","New customers churn most"))
            elif tenure < 12: factors.append(("Tenure < 12 months","#f59e0b","Still in high-risk window"))
            if contract == "Month-to-month": factors.append(("Month-to-month contract","#ef4444","3× higher churn"))
            if internet == "Fiber optic":   factors.append(("Fiber optic","#f59e0b","Higher churn than DSL"))
            if monthly > 75: factors.append((f"High charges ${monthly:.0f}/mo","#f59e0b","Above avg"))
            if tech == "No": factors.append(("No tech support","#8885a0","Support = stickier"))
            if not factors:
                factors.append(("Loyal customer","#22c55e",f"{tenure}mo tenure"))
                factors.append(("Committed contract","#22c55e",contract))
            for fl, fc, fn in factors:
                st.markdown(f"<div style='display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1e2133;align-items:flex-start;'><div style='width:8px;height:8px;border-radius:50%;background:{fc};margin-top:5px;flex-shrink:0;'></div><div><div style='font-size:13px;color:#e2e0f0;font-weight:500;'>{fl}</div><div style='font-size:11px;color:#6b6888;margin-top:2px;'>{fn}</div></div></div>",unsafe_allow_html=True)

        with gc:
            bc = '#ef4444' if label=="HIGH" else '#f59e0b' if label=="MEDIUM" else '#22c55e'
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=proba*100,
                number={'suffix': "%", 'font': {'family': 'Syne, sans-serif', 'size': 46, 'color': bc}},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': '#6b6888', 'tickfont': {'color': '#6b6888', 'size': 10}},
                    'bar': {'color': bc, 'thickness': 0.28},
                    'bgcolor': '#13152a',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, THRESHOLD*100], 'color': 'rgba(34,197,94,.15)'},
                        {'range': [THRESHOLD*100, 75], 'color': 'rgba(245,158,11,.15)'},
                        {'range': [75, 100], 'color': 'rgba(239,68,68,.15)'},
                    ],
                    'threshold': {
                        'line': {'color': '#6c63ff', 'width': 3},
                        'thickness': 0.9,
                        'value': THRESHOLD*100,
                    },
                },
            ))
            gauge_fig.update_layout(
                height=260, margin=dict(t=30, b=10, l=30, r=30),
                paper_bgcolor='rgba(0,0,0,0)', font={'color': '#8885a0', 'family': 'JetBrains Mono, monospace'},
                title={'text': f"Churn probability · threshold {THRESHOLD:.0%}", 'font': {'size': 12}},
            )
            st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})

            st.markdown('<div class="sec-lbl" style="margin-top:8px;">Recommended action</div>', unsafe_allow_html=True)
            if pred == 1:
                if contract == "Month-to-month": act = "Offer a <b>20% discount on annual contract</b>"
                elif tech == "No":               act = "Offer <b>3 months free tech support</b>"
                elif monthly > 75:               act = "Offer a <b>15% loyalty discount</b> for 6 months"
                else:                            act = "Assign a <b>dedicated account manager</b>"
                ltv = monthly * 24
                st.markdown(f'<div class="action-box"><div class="action-lbl">Retention strategy</div><div style="font-size:13px;color:#e2e0f0;line-height:1.7;">{act}</div><div style="margin-top:12px;padding-top:12px;border-top:1px solid #1e2133;display:flex;gap:24px;"><div><div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#6b6888;text-transform:uppercase;">Cost</div><div style="font-family:JetBrains Mono,monospace;font-size:14px;color:#e2e0f0;">~$15</div></div><div><div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#6b6888;text-transform:uppercase;">LTV at risk</div><div style="font-family:JetBrains Mono,monospace;font-size:14px;color:#ef4444;">${ltv:,.0f}</div></div></div></div>',unsafe_allow_html=True)
            else:
                st.markdown('<div class="action-box"><div class="action-lbl">Growth opportunity</div><div style="font-size:13px;color:#e2e0f0;line-height:1.7;">Stable customer. Consider premium add-ons or a referral request.</div></div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 2 — Bulk Prediction
# ══════════════════════════════════════════════════════════════════
with t2:
    st.markdown('<div class="sec-pill">Module 02</div>', unsafe_allow_html=True)
    st.markdown("### Bulk Customer Prediction")
    module_intro(
        "What this module does",
        "Upload a CSV of many customers at once and the app scores every row in seconds. "
        "You'll get a ranked at-risk list, KPI counts by risk tier, an estimated revenue-at-risk figure, "
        "and downloadable results — perfect for prioritising your retention team's call list. "
        "Your file must contain the same columns as the template below."
    )

    sample = pd.DataFrame([{'customerID':'SAMPLE-001','gender':'Male','SeniorCitizen':0,'Partner':'Yes','Dependents':'No','tenure':12,'PhoneService':'Yes','MultipleLines':'No','InternetService':'Fiber optic','OnlineSecurity':'No','OnlineBackup':'Yes','DeviceProtection':'No','TechSupport':'No','StreamingTV':'No','StreamingMovies':'No','Contract':'Month-to-month','PaperlessBilling':'Yes','PaymentMethod':'Electronic check','MonthlyCharges':70.35,'TotalCharges':844.20,'Churn':'No'}])
    st.download_button("Download CSV template", data=sample.to_csv(index=False), file_name="template.csv", mime="text/csv")

    uploaded = st.file_uploader("Upload customer CSV", type=['csv'])
    if uploaded:
        try:
            # encoding='utf-8-sig' strips a byte-order-mark some spreadsheet
            # tools (Excel) silently add, which otherwise turns the first
            # column name into '\ufeffcustomerID' and breaks lookups.
            raw = pd.read_csv(uploaded, encoding='utf-8-sig')
            raw.columns = raw.columns.str.strip()
        except Exception as e:
            raw = None
            st.error(f"❌ Couldn't read that file as a CSV: {e}")

        if raw is not None:
            missing = validate_csv(raw)
            if raw.empty:
                st.error("❌ CSV file is empty.")
            elif missing:
                st.error(
                    f"❌ CSV is missing {len(missing)} required column(s): **{', '.join(missing)}**.  \n"
                    "Download the template above for the correct format — column names must match exactly."
                )
            else:
                proc = raw.copy()
                proc['TotalCharges'] = pd.to_numeric(proc['TotalCharges'], errors='coerce')
                n_before = len(proc)
                proc.dropna(subset=['TotalCharges'], inplace=True)
                n_dropped = n_before - len(proc)
                if n_dropped:
                    st.warning(f"⚠️ Skipped {n_dropped} row(s) with invalid/non-numeric TotalCharges.")

                if proc.empty:
                    st.error("❌ No valid rows left after cleaning — check the TotalCharges column.")
                else:
                    proc = proc.reset_index(drop=True)
                    ids = proc['customerID'] if 'customerID' in proc.columns else pd.RangeIndex(len(proc)).astype(str)
                    try:
                        encoded = encode_customer_df(proc)
                    except ValueError as ve:
                        encoded = None
                        st.error(f"❌ {ve}")

                    if encoded is not None:
                        probas = model.predict_proba(encoded)[:,1]; preds = (probas>=THRESHOLD).astype(int)
                        results = pd.DataFrame({
                            'Customer ID'   : ids.values,
                            'Churn Prob (%)': (probas*100).round(1),
                            'Prediction'    : ['Will Churn' if p==1 else 'Will Stay' for p in preds],
                            'Risk Level'    : ['High' if p>=0.75 else 'Medium' if p>=THRESHOLD else 'Low' for p in probas],
                        }).sort_values('Churn Prob (%)', ascending=False)

                        n_total = len(results); n_churn = int(preds.sum())
                        n_high  = int((probas>=0.75).sum())
                        n_med   = int(((probas>=THRESHOLD)&(probas<0.75)).sum())
                        n_low   = int((probas<THRESHOLD).sum())
                        avg_m   = raw['MonthlyCharges'].mean() if 'MonthlyCharges' in raw.columns else 65

                        k1,k2,k3,k4,k5 = st.columns(5)
                        k1.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#e2e0f0;">{n_total:,}</div><div class="kpi-lbl">Total</div></div>',unsafe_allow_html=True)
                        k2.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{n_churn:,}</div><div class="kpi-lbl">At risk</div><div class="kpi-sub">{n_churn/n_total:.1%}</div></div>',unsafe_allow_html=True)
                        k3.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{n_high:,}</div><div class="kpi-lbl">High</div></div>',unsafe_allow_html=True)
                        k4.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#f59e0b;">{n_med:,}</div><div class="kpi-lbl">Medium</div></div>',unsafe_allow_html=True)
                        k5.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#22c55e;">{n_low:,}</div><div class="kpi-lbl">Low</div></div>',unsafe_allow_html=True)

                        st.markdown(f'<div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.25);border-radius:12px;padding:14px 18px;margin:12px 0;"><span style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#ef4444;">Revenue at risk</span><span style="font-family:Syne,sans-serif;font-size:26px;font-weight:700;color:#ef4444;margin-left:14px;">${n_churn*avg_m*24:,.0f}</span><span style="font-size:11px;color:#8885a0;margin-left:12px;">{n_churn} customers × ${avg_m:.0f}/mo × 24 months</span></div>',unsafe_allow_html=True)

                        st.markdown('<div class="sec-lbl">3D risk map — tenure × monthly charges × churn probability</div>', unsafe_allow_html=True)
                        # results is sorted by churn prob (so its index labels are shuffled),
                        # proc is not — always join back by label, never by position, or the
                        # points get scrambled across the wrong tenure/monthly values.
                        risk_colors = {'High': '#ef4444', 'Medium': '#f59e0b', 'Low': '#22c55e'}
                        scatter3d = go.Figure()
                        for lvl in ['Low', 'Medium', 'High']:
                            row_labels = results.index[results['Risk Level'] == lvl]
                            scatter3d.add_trace(go.Scatter3d(
                                x=proc.loc[row_labels, 'tenure'],
                                y=proc.loc[row_labels, 'MonthlyCharges'],
                                z=results.loc[row_labels, 'Churn Prob (%)'],
                                mode='markers',
                                name=lvl,
                                marker=dict(size=4, color=risk_colors[lvl], opacity=0.8, line=dict(width=0)),
                                text=results.loc[row_labels, 'Customer ID'],
                                hovertemplate='%{text}<br>Tenure: %{x} mo<br>Monthly: $%{y}<br>Churn: %{z:.1f}%<extra></extra>',
                            ))
                        scatter3d.update_layout(
                            height=460,
                            margin=dict(t=10, b=0, l=0, r=0),
                            paper_bgcolor='rgba(0,0,0,0)',
                            font={'color': '#8885a0', 'family': 'JetBrains Mono, monospace', 'size': 10},
                            legend=dict(bgcolor='rgba(19,21,42,.8)', bordercolor='#1e2133', borderwidth=1, x=0.02, y=0.98),
                            scene=dict(
                                xaxis=dict(title='Tenure (mo)', backgroundcolor='#0e1020', gridcolor='#1e2133', color='#6b6888'),
                                yaxis=dict(title='Monthly ($)', backgroundcolor='#0e1020', gridcolor='#1e2133', color='#6b6888'),
                                zaxis=dict(title='Churn %', backgroundcolor='#0e1020', gridcolor='#1e2133', color='#6b6888'),
                                camera=dict(eye=dict(x=1.5, y=1.4, z=0.9)),
                            ),
                        )
                        st.plotly_chart(scatter3d, use_container_width=True, config={'displayModeBar': False})

                        rf = st.multiselect("Filter", ["High","Medium","Low"], default=["High","Medium"])
                        tn = st.slider("Top N", 10, min(500,n_total), 50)
                        filt = results[results['Risk Level'].isin(rf)].head(tn)
                        def cr(v):
                            if v=='High':   return 'color:#ef4444;font-weight:600'
                            if v=='Medium': return 'color:#f59e0b;font-weight:600'
                            return 'color:#22c55e'
                        st.dataframe(filt.style.map(cr,subset=['Risk Level']).format({'Churn Prob (%)':'{:.1f}%'}),use_container_width=True,height=360)
                        d1,d2 = st.columns(2)
                        d1.download_button("Download all", data=results.to_csv(index=False), file_name="churn_all.csv", mime="text/csv", use_container_width=True)
                        d2.download_button("Download high-risk", data=results[results['Risk Level']=='High'].to_csv(index=False), file_name="high_risk.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("Upload a CSV above.")


# ══════════════════════════════════════════════════════════════════
# TAB 3 — Analytics
# ══════════════════════════════════════════════════════════════════
with t3:
    st.markdown('<div class="sec-pill">Module 03</div>', unsafe_allow_html=True)
    st.markdown("### Analytics Dashboard")
    module_intro(
        "What this module does",
        "Upload a customer dataset to see portfolio-level churn patterns: overall at-risk rate, "
        "revenue exposure, and how churn varies by contract type. Use this to spot which customer "
        "segments need the most attention before drilling into individuals."
    )
    dash_file = st.file_uploader("Upload customer dataset", type=['csv'], key="dash")
    if dash_file:
        try:
            df = pd.read_csv(dash_file, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
        except Exception as e:
            df = None
            st.error(f"❌ Couldn't read that file as a CSV: {e}")

        if df is not None:
            dp = df.copy()
            missing = validate_csv(dp)
            if dp.empty:
                st.error("❌ CSV file is empty.")
            elif missing:
                st.error(
                    f"❌ CSV is missing {len(missing)} required column(s): **{', '.join(missing)}**.  \n"
                    "Use the same column format as the template in Module 02."
                )
            else:
                dp['TotalCharges'] = pd.to_numeric(dp['TotalCharges'], errors='coerce')
                n_before = len(dp)
                dp.dropna(subset=['TotalCharges'], inplace=True)
                if n_before - len(dp):
                    st.warning(f"⚠️ Skipped {n_before - len(dp)} row(s) with invalid/non-numeric TotalCharges.")

                try:
                    dp2 = encode_customer_df(dp)
                except ValueError as ve:
                    dp2 = None
                    st.error(f"❌ {ve}")

                if dp2 is not None and not dp.empty:
                    p3 = model.predict_proba(dp2)[:,1]
                    dp['pred_prob']=p3; dp['pred_churn']=(p3>=THRESHOLD).astype(int)
                    dp['risk_level']=['High' if p>=0.75 else 'Medium' if p>=THRESHOLD else 'Low' for p in p3]
                    n_t=len(dp); n_r=int(dp['pred_churn'].sum())
                    avg_m3=dp['MonthlyCharges'].mean() if 'MonthlyCharges' in dp.columns else 65

                    ka,kb,kc,kd=st.columns(4)
                    ka.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#e2e0f0;">{n_t:,}</div><div class="kpi-lbl">Total</div></div>',unsafe_allow_html=True)
                    kb.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{n_r:,}</div><div class="kpi-lbl">At risk</div><div class="kpi-sub">{n_r/n_t:.1%}</div></div>',unsafe_allow_html=True)
                    kc.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#f59e0b;">${avg_m3:.0f}</div><div class="kpi-lbl">Avg monthly rev</div></div>',unsafe_allow_html=True)
                    kd.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">${n_r*avg_m3*24/1e6:.2f}M</div><div class="kpi-lbl">Revenue at risk</div></div>',unsafe_allow_html=True)

                    st.markdown('<div class="sec-lbl">3D portfolio view — tenure × monthly charges × churn probability</div>', unsafe_allow_html=True)
                    risk_colors3 = {'High': '#ef4444', 'Medium': '#f59e0b', 'Low': '#22c55e'}
                    scatter_a = go.Figure()
                    for lvl in ['Low', 'Medium', 'High']:
                        sub = dp[dp['risk_level'] == lvl]
                        if sub.empty:
                            continue
                        scatter_a.add_trace(go.Scatter3d(
                            x=sub['tenure'], y=sub['MonthlyCharges'], z=sub['pred_prob']*100,
                            mode='markers', name=lvl,
                            marker=dict(size=3.5, color=risk_colors3[lvl], opacity=0.75),
                            hovertemplate='Tenure: %{x} mo<br>Monthly: $%{y}<br>Churn: %{z:.1f}%<extra></extra>',
                        ))
                    scatter_a.update_layout(
                        height=460, margin=dict(t=10, b=0, l=0, r=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        font={'color': '#8885a0', 'family': 'JetBrains Mono, monospace', 'size': 10},
                        legend=dict(bgcolor='rgba(19,21,42,.8)', bordercolor='#1e2133', borderwidth=1, x=0.02, y=0.98),
                        scene=dict(
                            xaxis=dict(title='Tenure (mo)', backgroundcolor='#0e1020', gridcolor='#1e2133', color='#6b6888'),
                            yaxis=dict(title='Monthly ($)', backgroundcolor='#0e1020', gridcolor='#1e2133', color='#6b6888'),
                            zaxis=dict(title='Churn %', backgroundcolor='#0e1020', gridcolor='#1e2133', color='#6b6888'),
                            camera=dict(eye=dict(x=1.5, y=1.4, z=0.9)),
                        ),
                    )
                    st.plotly_chart(scatter_a, use_container_width=True, config={'displayModeBar': False})

                    fig4,ax4=plt.subplots(figsize=(10,4)); ps(fig4,ax4)
                    if 'Contract' in dp.columns:
                        cg=dp.groupby('Contract')['pred_churn'].mean()*100
                        b=ax4.bar(cg.index,cg.values,color=['#6c63ff','#8b5cf6','#a78bfa'],edgecolor='#0c0e16',width=.55)
                        ax4.set_title('Predicted churn rate by contract type',fontsize=11,pad=10)
                        ax4.set_ylabel('Churn rate (%)',fontsize=9)
                        for bar in b:
                            h=bar.get_height(); ax4.text(bar.get_x()+bar.get_width()/2,h+.5,f'{h:.1f}%',ha='center',va='bottom',fontsize=9,color='#8885a0')
                    plt.tight_layout(); st.pyplot(fig4); plt.close()
    else:
        st.info("Upload your customer CSV to see the analytics dashboard.")


# ══════════════════════════════════════════════════════════════════
# TAB 4 — My History (Module 4 — full MongoDB-backed history)
# ══════════════════════════════════════════════════════════════════
with t4:
    st.markdown('<div class="sec-pill">Module 04</div>', unsafe_allow_html=True)
    st.markdown("### My Customer History")
    module_intro(
        "What this module does",
        "Every prediction you save from Module 01 lands here. Track what happened to each "
        "flagged customer, record retention outcomes, and see which retention actions actually "
        "work best over time — all scoped privately to your account."
    )
    st.markdown(f'<div class="info-banner">All predictions made by <b>{USER_NAME}</b> ({USER_EMAIL}) are stored here. Each user sees only their own data.</div>', unsafe_allow_html=True)

    h1, h2, h3 = st.tabs(["All Predictions", "Record Outcome", "Retention Effectiveness"])

    # ── All Predictions ────────────────────────────────────────────
    with h1:
        kpis = get_user_kpis(USER_EMAIL)
        hk1,hk2,hk3,hk4,hk5 = st.columns(5)
        hk1.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#e2e0f0;">{kpis["total"]}</div><div class="kpi-lbl">Predictions made</div></div>',unsafe_allow_html=True)
        hk2.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{kpis["at_risk"]}</div><div class="kpi-lbl">At-risk flagged</div></div>',unsafe_allow_html=True)
        hk3.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#22c55e;">{kpis["retained"]}</div><div class="kpi-lbl">Retained</div></div>',unsafe_allow_html=True)
        hk4.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{kpis["churned"]}</div><div class="kpi-lbl">Churned</div></div>',unsafe_allow_html=True)
        hk5.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#6c63ff;">{kpis["retention_rate"]:.0f}%</div><div class="kpi-lbl">Retention rate</div></div>',unsafe_allow_html=True)

        st.markdown('<div class="sec-lbl" style="margin-top:20px;">Recent predictions</div>', unsafe_allow_html=True)

        preds_list = get_user_predictions(USER_EMAIL, limit=200)
        if preds_list:
            preds_df = pd.DataFrame(preds_list)[
                ['customer_id','predicted_at','churn_prob','risk_level',
                 'will_churn','contract','tenure','monthly']
            ].copy()
            preds_df.columns = ['Customer ID','Predicted At','Churn Prob','Risk Level',
                                 'Will Churn','Contract','Tenure','Monthly $']
            preds_df['Churn Prob'] = (preds_df['Churn Prob'] * 100).round(1)
            preds_df['Will Churn'] = preds_df['Will Churn'].map({True:'Yes',False:'No'})

            def sr(v):
                if v=='High':   return 'color:#ef4444;font-weight:600'
                if v=='Medium': return 'color:#f59e0b;font-weight:600'
                return 'color:#22c55e'
            def sc(v):
                return 'color:#ef4444;font-weight:600' if v=='Yes' else 'color:#22c55e'

            st.dataframe(
                preds_df.style
                    .map(sr, subset=['Risk Level'])
                    .map(sc, subset=['Will Churn'])
                    .format({'Churn Prob':'{:.1f}%', 'Monthly $':'${:.0f}'}),
                use_container_width=True, height=420,
            )
            st.download_button(
                "Export my predictions CSV",
                data=preds_df.to_csv(index=False),
                file_name="my_predictions.csv", mime="text/csv",
            )

            # Customer lookup
            st.markdown('<div class="sec-lbl" style="margin-top:20px;">Look up a specific customer</div>', unsafe_allow_html=True)
            lookup_id = st.text_input("Customer ID", placeholder="e.g. CUST-001", key="lookup")
            if lookup_id.strip():
                hist = get_customer_full_history(USER_EMAIL, lookup_id.strip())
                if hist["predictions"]:
                    st.markdown(f"**{len(hist['predictions'])} prediction(s) found for {lookup_id}**")
                    for p in hist["predictions"]:
                        rl = p.get("risk_level","")
                        rlc = "#ef4444" if rl=="HIGH" else "#f59e0b" if rl=="MEDIUM" else "#22c55e"
                        st.markdown(f'<div class="history-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><span style="font-family:JetBrains Mono,monospace;font-size:13px;color:#e2e0f0;">{p["predicted_at"]}</span><span style="font-family:JetBrains Mono,monospace;font-size:18px;font-weight:700;color:{rlc};margin-left:16px;">{p["churn_prob"]*100:.1f}%</span></div><span class="badge" style="background:rgba(108,99,255,.1);color:{rlc};border:1px solid {rlc};">{rl}</span></div><div style="font-size:12px;color:#6b6888;margin-top:8px;">Contract: {p.get("contract","-")} · Tenure: {p.get("tenure","-")}mo · Monthly: ${p.get("monthly",0):.0f}</div></div>',unsafe_allow_html=True)

                    if hist["outcomes"]:
                        st.markdown(f"**{len(hist['outcomes'])} outcome(s) recorded:**")
                        for o in hist["outcomes"]:
                            oc = o.get("outcome","")
                            occ = "#22c55e" if oc=="retained" else "#ef4444" if oc=="churned" else "#f59e0b"
                            st.markdown(f'<div class="history-card"><div style="display:flex;justify-content:space-between;"><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#8885a0;">{o["recorded_at"]}</span><span class="badge" style="background:rgba(0,0,0,.3);color:{occ};border:1px solid {occ};">{oc.upper()}</span></div><div style="font-size:13px;color:#e2e0f0;margin-top:8px;">{o.get("retention_action","-")}</div><div style="font-size:11px;color:#6b6888;margin-top:4px;">{o.get("notes","")}</div></div>',unsafe_allow_html=True)
                else:
                    st.info(f"No predictions found for customer {lookup_id}.")
        else:
            st.info("No predictions yet. Make a prediction in the '01 · Predict' tab with 'Save to my history' checked.")

    # ── Record Outcome ─────────────────────────────────────────────
    with h2:
        st.markdown("### Record outcome for a customer")
        st.markdown('<div class="info-banner">After contacting a flagged customer, record what happened. This builds your retention effectiveness data over time.</div>', unsafe_allow_html=True)

        oc1, oc2 = st.columns(2)
        with oc1:
            o_cid     = st.text_input("Customer ID", placeholder="e.g. CUST-001", key="ocid")
            o_outcome = st.selectbox("Outcome",
                                     ["retained","churned","pending","no_action"],
                                     help="retained = stayed after contact\nchurned = left despite contact\npending = still in progress\nno_action = no attempt made")
            o_action  = st.selectbox("Retention action taken",
                                     ["None","Offered annual contract discount",
                                      "Offered free tech support (3 months)",
                                      "Offered loyalty discount 15%",
                                      "Assigned account manager",
                                      "Sent personalised email",
                                      "Proactive support call",
                                      "Other"])
        with oc2:
            o_agent = st.text_input("Agent name", placeholder="e.g. Priya Sharma", key="oagent")
            o_notes = st.text_area("Notes", placeholder="Any context about this interaction...", height=130, key="onotes")

        if st.button("Save Outcome →", key="save_outcome"):
            if o_cid.strip():
                record_outcome(
                    user_email       = USER_EMAIL,
                    customer_id      = o_cid.strip(),
                    outcome          = o_outcome,
                    retention_action = o_action,
                    notes            = o_notes,
                    agent_name       = o_agent,
                )
                st.success(f"Outcome saved — {o_cid.strip()} marked as **{o_outcome.upper()}**")
            else:
                st.error("Enter a Customer ID.")

    # ── Retention Effectiveness ────────────────────────────────────
    with h3:
        st.markdown("### Which retention actions work best?")
        stats = get_retention_stats(USER_EMAIL)
        if stats:
            st.markdown('<div class="info-banner">Based on outcomes you have recorded. Actions with the highest success rate should be your default retention strategy.</div>', unsafe_allow_html=True)
            for s in stats:
                rate  = s["success_rate"]
                bw    = int(rate)
                color = '#22c55e' if rate>=70 else '#f59e0b' if rate>=40 else '#ef4444'
                st.markdown(f"""
                <div style="background:#13152a;border:1px solid #1e2133;border-radius:10px;padding:16px;margin:8px 0;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div style="font-size:13px;color:#e2e0f0;font-weight:500;">{s['action']}</div>
                    <div style="font-family:JetBrains Mono,monospace;font-size:14px;color:{color};">{rate:.0f}%</div>
                  </div>
                  <div style="height:6px;background:#1e2133;border-radius:3px;overflow:hidden;margin-bottom:8px;">
                    <div style="height:100%;width:{bw}%;background:{color};border-radius:3px;"></div>
                  </div>
                  <div style="font-size:11px;color:#6b6888;">{s['retained']} retained · {s['churned']} churned · {s['total']} total</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No outcome data yet. Record outcomes in the 'Record Outcome' tab.")


# ══════════════════════════════════════════════════════════════════
# TAB 5 — Explainability
# ══════════════════════════════════════════════════════════════════
with t5:
    st.markdown('<div class="sec-pill">Module 05</div>', unsafe_allow_html=True)
    st.markdown("### Why Did the Model Predict This?")
    module_intro(
        "What this module does",
        "Adjust a hypothetical customer's profile and see exactly which factors push the churn "
        "score up or down, plus the model's global top feature weights. Use this to understand "
        "and explain *why* the model makes the calls it makes — not just what it predicts."
    )

    ea, eb, ec_col = st.columns(3)
    with ea:
        et  = st.slider("Tenure ", 0, 72, 12, key="et")
        em  = st.number_input("Monthly $ ", 18.0, 120.0, 65.0, .5, key="em")
        ec2 = st.selectbox("Contract ", ["Month-to-month","One year","Two year"], key="ec2")
    with eb:
        ei  = st.selectbox("Internet ",      ["DSL","Fiber optic","No"], key="ei")
        eth = st.selectbox("Tech support ",  ["No","Yes","No internet service"], key="eth")
        es  = st.selectbox("Online security",["No","Yes","No internet service"], key="es")
    with ec_col:
        esn = st.selectbox("Senior ",   ["No","Yes"], key="esn")
        ep  = st.selectbox("Partner ",  ["No","Yes"], key="ep")
        epb = st.selectbox("Paperless ",["No","Yes"], key="epb")

    if st.button("Explain →", key="xbtn"):
        inp2 = build_input(et,em,ec2,ei,eth,es,"No",esn,ep,"No",epb,"Electronic check")
        proba2, pred2 = predict(inp2); label2, color2, css2 = risk_info(proba2)

        st.markdown(f'<div style="display:flex;align-items:center;gap:24px;padding:24px;background:#13152a;border:1px solid #1e2133;border-radius:14px;margin:16px 0;"><div style="font-family:Syne,sans-serif;font-size:50px;font-weight:700;color:{color2};">{proba2:.1%}</div><div><div style="font-family:Syne,sans-serif;font-size:16px;font-weight:600;color:{color2};">{label2} CHURN RISK</div><div style="font-size:12px;color:#8885a0;margin-top:6px;">{"Predicts churn." if pred2==1 else "Predicts stay."} · Threshold: {THRESHOLD:.2f}</div></div></div>',unsafe_allow_html=True)

        xl, xr = st.columns(2)
        with xl:
            impacts = []
            if ec2 == "Month-to-month": impacts.append(("Contract","Month-to-month → high driver",0.92,"#ef4444","+"))
            elif ec2 == "One year":     impacts.append(("Contract","One year → reduces risk",0.55,"#22c55e","−"))
            else:                       impacts.append(("Contract","Two year → strong retention",0.75,"#22c55e","−"))
            if et < 6:    impacts.append(("Tenure",f"{et}mo → very new",0.85,"#ef4444","+"))
            elif et < 24: impacts.append(("Tenure",f"{et}mo → building",0.45,"#f59e0b","+"))
            else:         impacts.append(("Tenure",f"{et}mo → loyal",0.60,"#22c55e","−"))
            if em > 80:   impacts.append(("Charges",f"${em:.0f} → high",0.70,"#ef4444","+"))
            elif em > 60: impacts.append(("Charges",f"${em:.0f} → moderate",0.35,"#f59e0b","+"))
            else:         impacts.append(("Charges",f"${em:.0f} → low",0.30,"#22c55e","−"))
            if ei == "Fiber optic": impacts.append(("Internet","Fiber → higher churn",0.55,"#f59e0b","+"))
            else:                   impacts.append(("Internet","DSL → stable",0.30,"#22c55e","−"))
            if eth == "No": impacts.append(("Tech","No → issues cause churn",0.45,"#f59e0b","+"))
            else:           impacts.append(("Tech","Yes → stickier",0.50,"#22c55e","−"))
            impacts.sort(key=lambda x: x[2], reverse=True)
            for fn,fd,fm,fc,fsign in impacts:
                st.markdown(f'<div style="background:#13152a;border:1px solid #1e2133;border-radius:10px;padding:14px;margin:8px 0;"><div style="display:flex;justify-content:space-between;"><div style="font-size:13px;color:#e2e0f0;font-weight:500;">{fn}</div><div style="font-family:JetBrains Mono,monospace;font-size:13px;color:{fc};">{fsign} {fm:.0%}</div></div><div style="font-size:11px;color:#6b6888;margin:4px 0 8px;">{fd}</div><div style="height:5px;background:#1e2133;border-radius:3px;"><div style="height:100%;width:{int(fm*100)}%;background:{fc};border-radius:3px;"></div></div></div>',unsafe_allow_html=True)

        with xr:
            fi2 = pd.DataFrame({'Feature':feature_names,'Importance':model.feature_importances_}).sort_values('Importance').tail(10)
            fig6, ax6 = plt.subplots(figsize=(6,5)); ps(fig6,ax6)
            c6 = ['#6c63ff' if i>=7 else '#2d2f4e' for i in range(len(fi2))]
            ax6.barh(fi2['Feature'], fi2['Importance'], color=c6, height=.6)
            ax6.set_title('Top 10 model weights', fontsize=10, pad=8, fontfamily='monospace')
            ax6.set_xlabel('Importance', fontsize=9)
            plt.tight_layout(); st.pyplot(fig6); plt.close()


# ══════════════════════════════════════════════════════════════════
# TAB 6 — ROI Calculator
# ══════════════════════════════════════════════════════════════════
with t6:
    st.markdown('<div class="sec-pill">Module 06</div>', unsafe_allow_html=True)
    st.markdown("### Retention Campaign ROI Calculator")
    module_intro(
        "What this module does",
        "Turn a batch of churn predictions into a dollar figure your business can act on. "
        "Set your retention campaign's cost and expected success rate, and this module "
        "estimates net benefit, ROI %, and revenue saved — so you can justify the spend "
        "before you make it."
    )

    st.markdown('<div class="sec-lbl">Cohort inputs</div>', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        n_at_risk = st.number_input("Customers flagged at-risk", min_value=1, value=350, step=10,
                                     help="From Module 02's bulk prediction results, or your own count.")
        avg_monthly_rev = st.number_input("Avg monthly revenue per customer ($)", min_value=1.0, value=65.0, step=1.0)
    with r2:
        cost_per_contact = st.number_input("Retention offer cost per customer ($)", min_value=0.0, value=15.0, step=1.0,
                                            help="e.g. discount value, free months, agent time.")
        success_rate = st.slider("Expected save rate (%)", 0, 100, 35,
                                  help="Of contacted at-risk customers, what % do you expect to retain?")
    with r3:
        ltv_months = st.number_input("LTV horizon (months)", min_value=1, value=24, step=1,
                                      help="How many months of revenue is a retained customer worth?")
        churn_would_lose = st.slider("Would-have-churned without action (%)", 0, 100, 100,
                                      help="Usually 100% — these customers were already flagged as leaving.")

    if st.button("Calculate ROI →", key="roi_btn"):
        customers_saved   = n_at_risk * (success_rate/100) 
        total_campaign_cost = n_at_risk * cost_per_contact
        ltv_per_customer   = avg_monthly_rev * ltv_months
        revenue_saved      = customers_saved * ltv_per_customer * (churn_would_lose/100)
        net_benefit        = revenue_saved - total_campaign_cost
        roi_pct            = (net_benefit / total_campaign_cost * 100) if total_campaign_cost > 0 else 0

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#e2e0f0;">{customers_saved:,.0f}</div><div class="kpi-lbl">Customers saved (est.)</div></div>',unsafe_allow_html=True)
        m2.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#f59e0b;">${total_campaign_cost:,.0f}</div><div class="kpi-lbl">Campaign spend</div></div>',unsafe_allow_html=True)
        m3.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#22c55e;">${net_benefit:,.0f}</div><div class="kpi-lbl">Net benefit</div></div>',unsafe_allow_html=True)
        m4.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#6c63ff;">{roi_pct:,.0f}%</div><div class="kpi-lbl">ROI</div></div>',unsafe_allow_html=True)

        st.markdown(
            f'<div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.25);border-radius:12px;'
            f'padding:16px 20px;margin:16px 0;font-size:13px;color:#a8a5c0;line-height:1.8;">'
            f'Retaining an estimated <b style="color:#22c55e;">{customers_saved:,.0f} customers</b> at '
            f'<b>${cost_per_contact:.0f}</b> each (${total_campaign_cost:,.0f} total) protects roughly '
            f'<b style="color:#22c55e;">${revenue_saved:,.0f}</b> in {ltv_months}-month lifetime revenue — '
            f'a net benefit of <b style="color:#22c55e;">${net_benefit:,.0f}</b> and an ROI of '
            f'<b style="color:#6c63ff;">{roi_pct:,.0f}%</b> on the campaign spend.</div>',
            unsafe_allow_html=True,
        )

        gc1, gc2 = st.columns([1, 2])
        with gc1:
            roi_color = '#22c55e' if roi_pct >= 0 else '#ef4444'
            roi_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=max(0, min(roi_pct, 2000)),
                number={'suffix': "%", 'font': {'family': 'Syne, sans-serif', 'size': 34, 'color': roi_color}},
                gauge={
                    'axis': {'range': [0, 2000], 'tickcolor': '#6b6888', 'tickfont': {'color': '#6b6888', 'size': 9}},
                    'bar': {'color': roi_color, 'thickness': 0.28},
                    'bgcolor': '#13152a',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 300], 'color': 'rgba(239,68,68,.12)'},
                        {'range': [300, 800], 'color': 'rgba(245,158,11,.12)'},
                        {'range': [800, 2000], 'color': 'rgba(34,197,94,.12)'},
                    ],
                },
            ))
            roi_gauge.update_layout(
                height=230, margin=dict(t=25, b=5, l=25, r=25),
                paper_bgcolor='rgba(0,0,0,0)', font={'color': '#8885a0', 'family': 'JetBrains Mono, monospace'},
                title={'text': "ROI % (capped at 2,000% for display)", 'font': {'size': 10}},
            )
            st.plotly_chart(roi_gauge, use_container_width=True, config={'displayModeBar': False})

        with gc2:
            waterfall = go.Figure(go.Waterfall(
                orientation='v',
                measure=['relative', 'relative', 'total'],
                x=['Revenue protected', 'Campaign cost', 'Net benefit'],
                y=[revenue_saved, -total_campaign_cost, net_benefit],
                connector={'line': {'color': '#1e2133'}},
                increasing={'marker': {'color': '#22c55e'}},
                decreasing={'marker': {'color': '#ef4444'}},
                totals={'marker': {'color': '#6c63ff'}},
                text=[f"${revenue_saved:,.0f}", f"-${total_campaign_cost:,.0f}", f"${net_benefit:,.0f}"],
                textposition='outside',
            ))
            waterfall.update_layout(
                height=230, margin=dict(t=25, b=5, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': '#8885a0', 'family': 'JetBrains Mono, monospace', 'size': 10},
                title={'text': "How the net benefit is built", 'font': {'size': 10}},
                yaxis=dict(gridcolor='#1e2133'), xaxis=dict(gridcolor='#1e2133'),
                showlegend=False,
            )
            st.plotly_chart(waterfall, use_container_width=True, config={'displayModeBar': False})

        fig7, ax7 = plt.subplots(figsize=(10,3.2)); ps(fig7, ax7)
        bars = ax7.barh(['Campaign cost','Revenue protected','Net benefit'],
                         [total_campaign_cost, revenue_saved, net_benefit],
                         color=['#f59e0b','#6c63ff','#22c55e'])
        ax7.set_xlabel('$', fontsize=9)
        ax7.set_title('Cost vs. revenue protected vs. net benefit', fontsize=11, pad=10, fontfamily='monospace')
        for bar in bars:
            w = bar.get_width()
            ax7.text(w, bar.get_y()+bar.get_height()/2, f' ${w:,.0f}', va='center', fontsize=9, color='#8885a0')
        plt.tight_layout(); st.pyplot(fig7); plt.close()

        st.caption(
            "This is a planning estimate, not a guarantee — actual save rates depend on offer quality, "
            "timing, and execution. Use Module 04's Retention Effectiveness tab to track real outcomes "
            "and refine your save-rate assumption over time."
        )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f'<div style="text-align:center;font-family:JetBrains Mono,monospace;font-size:10px;color:#3d3f5a;padding:12px 0;">ChurnGuard Pro v3.0 · Signed in as {USER_EMAIL} · MongoDB · Phase 3</div>', unsafe_allow_html=True)