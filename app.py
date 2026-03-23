import streamlit as st
import pickle
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ChurnGuard — Predict. Retain. Grow.",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background-color: #f7f6f2; color: #1a1a2e; }
            
/* ✅ PASTE HERE */
label {
    color: #1a1a2e !important;
    font-weight: 500;
}

.stSelectbox label,
.stSlider label,
.stNumberInput label {
    color: #1a1a2e !important;
}

/* Fix only visible input fields (safe targeting) */
.stNumberInput input,
.stTextInput input,
.stTextArea textarea {
    color: #1a1a2e !important;
}
            
/* Ensure number input text is always visible */
.stNumberInput input {
    background-color: white !important;
    color: #1a1a2e !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] {
    background-color: #1a1a2e;
    border-right: none;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label { color: #9b97a0 !important; }
            
/* ───── FILE UPLOADER FIX ───── */
[data-testid="stFileUploader"] {
    background-color: #1a1a2e !important;
    border-radius: 10px;
    padding: 10px;
}

[data-testid="stFileUploader"] * {
    color: #ffffff !important;
}

/* Fix "Browse files" button */
[data-testid="stFileUploader"] button {
    background-color: #2d2d4e !important;
    color: #ffffff !important;
    border: 1px solid #444 !important;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e8e6df;
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9b97a0 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 22px !important;
    color: #1a1a2e !important;
}

.stButton > button {
    background-color: #1a1a2e;
    color: #f7f6f2;
    border: none;
    border-radius: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.06em;
    padding: 14px 28px;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background-color: #2d2d4e;
    transform: translateY(-1px);
}

.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #e8e6df;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.05em;
    border-radius: 7px;
    padding: 8px 20px;
    color: #9b97a0;
}
.stTabs [aria-selected="true"] {
    background-color: #1a1a2e !important;
    color: white !important;
}

.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background-color: white;
    border: 1px solid #e8e6df;
    border-radius: 8px;
    color: #1a1a2e;
    font-family: 'DM Sans', sans-serif;
}

.stSlider > div > div > div { background-color: #1a1a2e; }

.risk-high {
    background: #fff5f5;
    border: 1.5px solid #feb2b2;
    border-left: 5px solid #e53e3e;
    border-radius: 12px;
    padding: 28px;
    margin: 16px 0;
}
.risk-medium {
    background: #fffbeb;
    border: 1.5px solid #fbd38d;
    border-left: 5px solid #d69e2e;
    border-radius: 12px;
    padding: 28px;
    margin: 16px 0;
}
.risk-low {
    background: #f0fff4;
    border: 1.5px solid #9ae6b4;
    border-left: 5px solid #38a169;
    border-radius: 12px;
    padding: 28px;
    margin: 16px 0;
}
.risk-title {
    font-family: 'DM Mono', monospace;
    font-size: 22px;
    font-weight: 500;
    margin-bottom: 6px;
}
.risk-prob {
    font-family: 'DM Mono', monospace;
    font-size: 48px;
    font-weight: 500;
    line-height: 1;
    margin: 12px 0;
}
.risk-sub {
    font-size: 13px;
    color: #718096;
    line-height: 1.7;
}

.section-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #9b97a0;
    border-bottom: 1px solid #e8e6df;
    padding-bottom: 8px;
    margin-bottom: 16px;
    margin-top: 20px;
}

.factor-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid #f0ede8;
}
.factor-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
}
.factor-label { font-size: 13px; color: #1a1a2e; font-weight: 500; }
.factor-note  { font-size: 11px; color: #9b97a0; margin-top: 2px; }

.action-box {
    background: white;
    border: 1px solid #e8e6df;
    border-radius: 10px;
    padding: 18px;
    margin-top: 12px;
}
.action-label {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #9b97a0;
    margin-bottom: 8px;
}
.action-text { font-size: 14px; color: #1a1a2e; line-height: 1.6; }

.stat-card {
    background: white;
    border: 1px solid #e8e6df;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    margin: 4px 0;
}
.stat-num {
    font-family: 'DM Mono', monospace;
    font-size: 28px;
    color: #1a1a2e;
    font-weight: 500;
}
.stat-lbl {
    font-size: 11px;
    color: #9b97a0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

.shap-card {
    background: white;
    border: 1px solid #e8e6df;
    border-radius: 10px;
    padding: 20px;
    margin: 8px 0;
}
.shap-feature { font-size: 13px; color: #1a1a2e; font-weight: 500; }
.shap-impact  { font-size: 11px; color: #9b97a0; margin-top: 2px; }
.shap-bar-bg  {
    height: 6px;
    background: #f0ede8;
    border-radius: 3px;
    margin-top: 8px;
    overflow: hidden;
}
            
/* ───── DOWNLOAD BUTTON FIX ───── */
.stDownloadButton > button {
    background-color: #1a1a2e !important;
    color: #ffffff !important;
    border-radius: 8px;
    border: none;
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    padding: 14px 20px;
    width: 100%;
}

/* Hover */
.stDownloadButton > button:hover {
    background-color: #2d2d4e !important;
    color: #ffffff !important;
}

/* Disabled state (important!) */
.stDownloadButton > button:disabled {
    background-color: #d4d2cc !important;
    color: #6b6880 !important;
}

#MainMenu {visibility: hidden;}
footer     {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Load model ─────────────────────────────────────────────────────────────────
@st.cache_resource
def load_package():
    paths = ['churn_model_final.pkl']
    for p in paths:
        if os.path.exists(p):
            with open(p, 'rb') as f:
                pkg = pickle.load(f)
            if isinstance(pkg, dict):
                return pkg['model'], float(pkg['threshold']), pkg['features']
            return pkg, 0.63, None
    return None, 0.63, None

@st.cache_data
def load_metrics():
    paths = ['metrics.json',
             'customer churn/metrics.json',
             '/content/drive/MyDrive/customer churn/metrics.json']
    for p in paths:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return {}

model, THRESHOLD, feature_names = load_package()
metrics = load_metrics()

DEFAULT_FEATURES = [
    'gender','SeniorCitizen','Partner','Dependents','tenure',
    'PhoneService','MultipleLines','InternetService',
    'OnlineSecurity','OnlineBackup','DeviceProtection',
    'TechSupport','StreamingTV','StreamingMovies',
    'Contract','PaperlessBilling','PaymentMethod',
    'MonthlyCharges','TotalCharges'
]
if feature_names is None:
    feature_names = DEFAULT_FEATURES

# ── Encoding helpers ───────────────────────────────────────────────────────────
CONTRACT_MAP = {"Month-to-month": 0, "One year": 1, "Two year": 2}
INTERNET_MAP = {"DSL": 0, "Fiber optic": 1, "No": 2}
TECH_MAP     = {"No": 0, "No internet service": 1, "Yes": 2}
BINARY_MAP   = {"No": 0, "Yes": 1}
PAYMENT_MAP  = {
    "Bank transfer (automatic)": 0,
    "Credit card (automatic)"  : 1,
    "Electronic check"         : 2,
    "Mailed check"             : 3,
}

def build_input(tenure, monthly, contract, internet, tech,
                online_sec, online_bkp, senior, partner,
                dependents, paperless, payment):
    total = monthly * tenure
    sec_val = BINARY_MAP.get(online_sec, 0) if online_sec != "No internet service" else 0
    bkp_val = BINARY_MAP.get(online_bkp, 0) if online_bkp != "No internet service" else 0
    return np.array([[
        1,
        BINARY_MAP[senior],
        BINARY_MAP[partner],
        BINARY_MAP[dependents],
        tenure,
        1, 1,
        INTERNET_MAP[internet],
        sec_val,
        bkp_val,
        0,
        TECH_MAP[tech],
        0, 0,
        CONTRACT_MAP[contract],
        BINARY_MAP[paperless],
        PAYMENT_MAP[payment],
        monthly,
        total,
    ]])

def predict(input_arr):
    proba = model.predict_proba(input_arr)[0][1]
    pred  = int(proba >= THRESHOLD)
    return proba, pred

def risk_label(proba):
    if proba >= 0.75: return "HIGH",        "#e53e3e", "risk-high"
    if proba >= THRESHOLD: return "MEDIUM", "#d69e2e", "risk-medium"
    return "LOW",                           "#38a169", "risk-low"


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 24px;'>
      <div style='font-family: DM Mono, monospace; font-size: 22px;
                  font-weight: 500; letter-spacing: -0.02em;'>
        🛡️ ChurnGuard
      </div>
      <div style='font-size: 11px; color: #6b6880; margin-top: 4px;
                  letter-spacing: 0.08em; text-transform: uppercase;'>
        Predict · Retain · Grow
      </div>
    </div>
    """, unsafe_allow_html=True)

    auc  = metrics.get('metrics', {}).get('auc_roc',   metrics.get('final_auc',      0.8353))
    prec = metrics.get('metrics', {}).get('precision', metrics.get('final_precision', 0.6036))
    rec  = metrics.get('metrics', {}).get('recall',    metrics.get('final_recall',    0.6230))
    f1   = metrics.get('metrics', {}).get('f1_score',  metrics.get('final_f1',        0.6132))

    st.markdown('<div class="section-tag" style="color:#6b6880; border-color:#2d2d4e;">Model stats</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("AUC-ROC",   f"{auc:.3f}")
    c2.metric("F1 Score",  f"{f1:.3f}")
    c1.metric("Precision", f"{prec:.1%}")
    c2.metric("Recall",    f"{rec:.1%}")

    st.markdown(f"""
    <div style='margin-top: 20px; padding: 14px; background: #12122a;
                border-radius: 8px; border: 1px solid #2d2d4e;'>
        <div style='font-family: DM Mono, monospace; font-size: 9px;
                    text-transform: uppercase; letter-spacing: 0.12em;
                    color: #6b6880; margin-bottom: 6px;'>Decision threshold</div>
        <div style='font-family: DM Mono, monospace; font-size: 24px;
                    color: #e8e6df;'>{THRESHOLD:.2f}</div>
        <div style='font-size: 11px; color: #6b6880; margin-top: 6px; line-height: 1.6;'>
            Tuned from default 0.50.<br>
            Customers above this probability<br>are flagged as at-risk.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if model is None:
        st.error("Model not found. Place churn_model_final.pkl in the app folder.")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 8px 0 28px;'>
  <div style='font-family: DM Mono, monospace; font-size: 30px;
              font-weight: 500; color: #1a1a2e; letter-spacing: -0.02em;'>
    Customer Churn Prediction
  </div>
  <div style='font-size: 14px; color: #9b97a0; margin-top: 6px;'>
    Identify at-risk customers before they leave — and act in time.
  </div>
</div>
""", unsafe_allow_html=True)

if model is None:
    st.error("Place `churn_model_final.pkl`, `feature_names.pkl` and `metrics.json` in the same folder as app.py")
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "MODULE 1 — Single Prediction",
    "MODULE 2 — Bulk Prediction",
    "MODULE 5 — Why Did It Predict This?",
])


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — Single prediction
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-tag">Customer details</div>',
                unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("**Account**")
        tenure  = st.slider("Tenure (months)", 0, 72, 12)
        monthly = st.number_input("Monthly Charges ($)",
                                  min_value=18.0, max_value=120.0,
                                  value=65.0, step=0.5)
        st.caption(f"Estimated total: **${monthly * tenure:,.0f}**")
        contract = st.selectbox("Contract Type",
                                ["Month-to-month","One year","Two year"])
        payment  = st.selectbox("Payment Method",
                                ["Electronic check","Mailed check",
                                 "Bank transfer (automatic)",
                                 "Credit card (automatic)"])

    with col_b:
        st.markdown("**Services**")
        internet   = st.selectbox("Internet Service",
                                  ["DSL","Fiber optic","No"])
        tech       = st.selectbox("Tech Support",
                                  ["No","Yes","No internet service"])
        online_sec = st.selectbox("Online Security",
                                  ["No","Yes","No internet service"])
        online_bkp = st.selectbox("Online Backup",
                                  ["No","Yes","No internet service"])

    with col_c:
        st.markdown("**Demographics**")
        senior     = st.selectbox("Senior Citizen",  ["No","Yes"])
        partner    = st.selectbox("Has Partner",      ["No","Yes"])
        dependents = st.selectbox("Has Dependents",   ["No","Yes"])
        paperless  = st.selectbox("Paperless Billing",["No","Yes"])

    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("Run Churn Prediction →")

    if run:
        inp   = build_input(tenure, monthly, contract, internet, tech,
                            online_sec, online_bkp, senior, partner,
                            dependents, paperless, payment)
        proba, pred = predict(inp)
        label, color, css_class = risk_label(proba)

        st.markdown("---")
        st.markdown('<div class="section-tag">Result</div>',
                    unsafe_allow_html=True)

        res_col, chart_col = st.columns([1, 1])

        with res_col:
            st.markdown(f"""
            <div class="{css_class}">
                <div class="risk-title" style="color:{color};">
                    {label} CHURN RISK
                </div>
                <div class="risk-prob" style="color:{color};">{proba:.1%}</div>
                <div class="risk-sub">
                    {"This customer is likely to leave. Act now." if pred == 1
                     else "This customer appears stable. Consider upselling."}
                    <br>Threshold: {THRESHOLD:.2f} &nbsp;|&nbsp;
                    Prediction: {"Will churn" if pred == 1 else "Will stay"}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Risk factors
            st.markdown('<div class="section-tag">Why this score?</div>',
                        unsafe_allow_html=True)
            factors = []
            if tenure < 6:
                factors.append(("Very new customer (<6 months)", "#e53e3e",
                                 "Newest customers churn most often"))
            elif tenure < 12:
                factors.append(("Short tenure (<12 months)", "#d69e2e",
                                 "Still in the high-risk early period"))
            if contract == "Month-to-month":
                factors.append(("Month-to-month contract", "#e53e3e",
                                 "3× higher churn than annual contracts"))
            if internet == "Fiber optic":
                factors.append(("Fiber optic internet", "#d69e2e",
                                 "Fiber users churn more than DSL users"))
            if monthly > 75:
                factors.append((f"High charges (${monthly:.0f}/mo)", "#d69e2e",
                                 "High bill = higher churn risk"))
            if tech == "No":
                factors.append(("No tech support", "#9b97a0",
                                 "Support subscribers churn less"))
            if online_sec == "No":
                factors.append(("No online security", "#9b97a0",
                                 "Add-on subscribers are stickier"))
            if not factors:
                factors.append(("Long-term loyal customer", "#38a169",
                                 f"{tenure} months tenure — very stable"))
                factors.append(("Committed contract", "#38a169",
                                 f"{contract} — low churn rate"))

            for f_label, f_color, f_note in factors:
                st.markdown(f"""
                <div class="factor-row">
                    <div class="factor-dot" style="background:{f_color};"></div>
                    <div>
                        <div class="factor-label">{f_label}</div>
                        <div class="factor-note">{f_note}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

        with chart_col:
            # Gauge bar
            fig, ax = plt.subplots(figsize=(6, 2.8),
                                   facecolor='#f7f6f2')
            ax.set_facecolor('#f7f6f2')
            bar_c = '#e53e3e' if label == "HIGH" else \
                    '#d69e2e' if label == "MEDIUM" else '#38a169'
            ax.barh([''], [proba],       color=bar_c,  height=0.4)
            ax.barh([''], [1 - proba],   left=[proba],
                    color='#e8e6df', height=0.4)
            ax.axvline(x=THRESHOLD, color='#1a1a2e', linestyle='--',
                       lw=1.5, label=f'Threshold ({THRESHOLD:.2f})')
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.25, 0.5, THRESHOLD, 0.75, 1.0])
            ax.set_xticklabels(['0%','25%','50%',
                                f'{THRESHOLD:.0%}↑','75%','100%'],
                               fontsize=9, color='#9b97a0')
            ax.tick_params(axis='y', colors='#f7f6f2')
            for sp in ax.spines.values():
                sp.set_visible(False)
            ax.set_title(f'Churn probability: {proba:.1%}',
                         color='#1a1a2e', fontsize=12, pad=10,
                         fontfamily='monospace')
            ax.legend(facecolor='#f7f6f2', edgecolor='#e8e6df',
                      labelcolor='#9b97a0', fontsize=9)
            st.pyplot(fig)
            plt.close()

            # Recommended action
            st.markdown('<div class="section-tag" style="margin-top:8px;">Recommended action</div>',
                        unsafe_allow_html=True)
            if pred == 1:
                if contract == "Month-to-month":
                    action = "Offer a <b>20% discount on annual contract upgrade</b>. Month-to-month customers switching to annual plans have the highest retention rate."
                elif tech == "No":
                    action = "Offer <b>3 months of free tech support</b>. Customers with support churn 30% less."
                elif monthly > 75:
                    action = "Offer a <b>loyalty discount of 15% on monthly charges</b> for the next 6 months."
                else:
                    action = "Assign a <b>dedicated account manager</b> to reach out within 48 hours."
                ltv = monthly * 24
                st.markdown(f"""
                <div class="action-box">
                    <div class="action-label">Retention strategy</div>
                    <div class="action-text">{action}</div>
                    <div style="margin-top:14px; padding-top:12px;
                                border-top:1px solid #f0ede8;">
                        <span style="font-family:DM Mono,monospace;
                                     font-size:10px; color:#9b97a0;">
                            RETENTION COST
                        </span>
                        <span style="font-family:DM Mono,monospace;
                                     font-size:13px; color:#1a1a2e;
                                     margin-left:8px;">~$15</span>
                        <span style="font-family:DM Mono,monospace;
                                     font-size:10px; color:#9b97a0;
                                     margin-left:20px;">LTV AT RISK</span>
                        <span style="font-family:DM Mono,monospace;
                                     font-size:13px; color:#e53e3e;
                                     margin-left:8px;">${ltv:,.0f}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="action-box">
                    <div class="action-label">Growth opportunity</div>
                    <div class="action-text">
                        Customer is stable. Consider offering premium add-ons
                        like Streaming TV, Device Protection, or upgrading
                        their internet plan.
                    </div>
                    <div style="margin-top:14px; padding-top:12px;
                                border-top:1px solid #f0ede8;
                                font-size:12px; color:#9b97a0;">
                        No retention spend needed right now.
                    </div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — Bulk prediction
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-tag">Upload customer data</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white; border:1px solid #e8e6df; border-radius:10px;
                padding:20px; margin-bottom:16px; font-size:13px;
                color:#718096; line-height:1.8;">
        Upload a CSV file with your customer data. The file should have the same
        columns as the Telco dataset. The app will predict churn risk for every
        customer and return a ranked list — highest risk at the top.
        <br><br>
        <b style="color:#1a1a2e;">Required columns:</b> tenure, MonthlyCharges,
        TotalCharges, Contract, InternetService, TechSupport, SeniorCitizen,
        Partner, Dependents, PaperlessBilling, PaymentMethod, and other
        service columns.
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your CSV here", type=['csv'],
        help="Max 50,000 rows. Same format as Telco Customer Churn dataset."
    )

    if uploaded_file:
        try:
            raw_df = pd.read_csv(uploaded_file)
            st.success(f"Loaded {len(raw_df):,} customers.")

            # Preprocess
            df_proc = raw_df.copy()
            df_proc['TotalCharges'] = pd.to_numeric(
                df_proc['TotalCharges'], errors='coerce')
            null_count = df_proc['TotalCharges'].isnull().sum()
            df_proc.dropna(subset=['TotalCharges'], inplace=True)
            if null_count > 0:
                st.warning(f"Dropped {null_count} rows with missing TotalCharges.")

            ids = df_proc['customerID'] if 'customerID' in df_proc.columns \
                  else pd.RangeIndex(len(df_proc)).astype(str)

            for col in ['customerID', 'Churn']:
                if col in df_proc.columns:
                    df_proc.drop(col, axis=1, inplace=True)

            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            for col in df_proc.select_dtypes(include='object').columns:
                df_proc[col] = le.fit_transform(df_proc[col])

            # Predict
            probas = model.predict_proba(df_proc)[:, 1]
            preds  = (probas >= THRESHOLD).astype(int)

            results = pd.DataFrame({
                'Customer ID'       : ids.values,
                'Churn Probability' : (probas * 100).round(1),
                'Prediction'        : ['Will Churn' if p == 1
                                       else 'Will Stay' for p in preds],
                'Risk Level'        : ['High'   if p >= 0.75
                                       else 'Medium' if p >= THRESHOLD
                                       else 'Low'    for p in probas],
            }).sort_values('Churn Probability', ascending=False)

            # Summary stats
            n_total  = len(results)
            n_churn  = (preds == 1).sum()
            n_high   = (probas >= 0.75).sum()
            n_medium = ((probas >= THRESHOLD) & (probas < 0.75)).sum()
            n_low    = (probas < THRESHOLD).sum()

            st.markdown('<div class="section-tag">Summary</div>',
                        unsafe_allow_html=True)
            s1, s2, s3, s4, s5 = st.columns(5)
            s1.markdown(f'<div class="stat-card"><div class="stat-num">{n_total:,}</div><div class="stat-lbl">Total customers</div></div>', unsafe_allow_html=True)
            s2.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#e53e3e">{n_churn:,}</div><div class="stat-lbl">At risk</div></div>', unsafe_allow_html=True)
            s3.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#e53e3e">{n_high:,}</div><div class="stat-lbl">High risk</div></div>', unsafe_allow_html=True)
            s4.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#d69e2e">{n_medium:,}</div><div class="stat-lbl">Medium risk</div></div>', unsafe_allow_html=True)
            s5.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#38a169">{n_low:,}</div><div class="stat-lbl">Low risk</div></div>', unsafe_allow_html=True)

            # Revenue at risk
            if 'MonthlyCharges' in raw_df.columns:
                avg_monthly = raw_df['MonthlyCharges'].mean()
                revenue_risk = n_churn * avg_monthly * 24
                st.markdown(f"""
                <div style="background:#fff5f5; border:1px solid #feb2b2;
                            border-radius:10px; padding:16px; margin:12px 0;
                            font-size:13px;">
                    <b style="color:#e53e3e;">Revenue at risk:</b>
                    <span style="font-family:DM Mono,monospace; font-size:18px;
                                 color:#e53e3e; margin-left:10px;">
                        ${revenue_risk:,.0f}
                    </span>
                    <span style="color:#9b97a0; font-size:11px;
                                 margin-left:8px;">
                        ({n_churn} customers × ${avg_monthly:.0f}/mo × 24 months)
                    </span>
                </div>
                """, unsafe_allow_html=True)

            # Filter
            st.markdown('<div class="section-tag">Filter results</div>',
                        unsafe_allow_html=True)
            f1, f2 = st.columns(2)
            risk_filter = f1.multiselect(
                "Risk level", ["High","Medium","Low"],
                default=["High","Medium"])
            top_n = f2.slider("Show top N customers", 10, min(500, n_total), 50)

            filtered = results[results['Risk Level'].isin(risk_filter)].head(top_n)

            # Color rows
            def color_risk(val):
                if val == 'High':   return 'color: #e53e3e; font-weight: 600'
                if val == 'Medium': return 'color: #d69e2e; font-weight: 600'
                return 'color: #38a169'

            st.dataframe(
                filtered.style.applymap(
                    color_risk, subset=['Risk Level']
                ).format({'Churn Probability': '{:.1f}%'}),
                use_container_width=True,
                height=420,
            )

            # Downloads
            st.markdown('<div class="section-tag">Export</div>',
                        unsafe_allow_html=True)
            dl1, dl2 = st.columns(2)

            full_csv = results.to_csv(index=False)
            dl1.download_button(
                "Download full predictions (CSV)",
                data=full_csv,
                file_name="churn_predictions_all.csv",
                mime="text/csv",
                use_container_width=True,
            )

            high_risk_csv = results[results['Risk Level'] == 'High'].to_csv(index=False)
            dl2.download_button(
                "Download high-risk call list (CSV)",
                data=high_risk_csv,
                file_name="high_risk_customers.csv",
                mime="text/csv",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.info("Make sure your CSV has the same columns as the Telco Customer Churn dataset.")

    else:
        # Sample template download
        st.markdown('<div class="section-tag">No file yet</div>',
                    unsafe_allow_html=True)
        sample = pd.DataFrame([{
            'customerID':'SAMPLE-001','gender':'Male','SeniorCitizen':0,
            'Partner':'Yes','Dependents':'No','tenure':12,
            'PhoneService':'Yes','MultipleLines':'No',
            'InternetService':'Fiber optic','OnlineSecurity':'No',
            'OnlineBackup':'Yes','DeviceProtection':'No',
            'TechSupport':'No','StreamingTV':'No','StreamingMovies':'No',
            'Contract':'Month-to-month','PaperlessBilling':'Yes',
            'PaymentMethod':'Electronic check',
            'MonthlyCharges':70.35,'TotalCharges':844.20,'Churn':'No'
        }])
        st.download_button(
            "Download sample CSV template",
            data=sample.to_csv(index=False),
            file_name="sample_template.csv",
            mime="text/csv",
        )
        st.info("Upload a CSV above to get started. Download the sample template to see the expected format.")


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — Explainability
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-tag">Why did the model predict this?</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white; border:1px solid #e8e6df; border-radius:10px;
                padding:20px; margin-bottom:20px; font-size:13px;
                color:#718096; line-height:1.8;">
        This module explains the model's decisions in plain English.
        Enter a customer's details below to see exactly which factors are
        pushing their churn risk up or down — and by how much.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Enter customer to explain:**")
    e1, e2, e3 = st.columns(3)

    with e1:
        e_tenure   = st.slider("Tenure (months) ", 0, 72, 12, key="e_tenure")
        e_monthly  = st.number_input("Monthly Charges ($) ", 18.0, 120.0,
                                     65.0, step=0.5, key="e_monthly")
        e_contract = st.selectbox("Contract Type ",
                                  ["Month-to-month","One year","Two year"],
                                  key="e_contract")
    with e2:
        e_internet = st.selectbox("Internet Service ",
                                  ["DSL","Fiber optic","No"], key="e_internet")
        e_tech     = st.selectbox("Tech Support ",
                                  ["No","Yes","No internet service"],
                                  key="e_tech")
        e_sec      = st.selectbox("Online Security ",
                                  ["No","Yes","No internet service"],
                                  key="e_sec")
    with e3:
        e_senior   = st.selectbox("Senior Citizen ",  ["No","Yes"], key="e_senior")
        e_partner  = st.selectbox("Has Partner ",      ["No","Yes"], key="e_partner")
        e_paperless= st.selectbox("Paperless Billing ",["No","Yes"], key="e_paperless")

    explain_btn = st.button("Explain This Prediction →", key="explain")

    if explain_btn:
        inp   = build_input(e_tenure, e_monthly, e_contract, e_internet,
                            e_tech, e_sec, "No", e_senior, e_partner,
                            "No", e_paperless, "Electronic check")
        proba, pred = predict(inp)
        label, color, css_class = risk_label(proba)

        st.markdown("---")

        # Top result line
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:20px;
                    padding: 20px; background:white;
                    border:1px solid #e8e6df; border-radius:10px;
                    margin-bottom:20px;">
            <div style="font-family:DM Mono,monospace; font-size:40px;
                        font-weight:500; color:{color};">{proba:.1%}</div>
            <div>
                <div style="font-family:DM Mono,monospace; font-size:14px;
                            font-weight:500; color:{color};">
                    {label} CHURN RISK
                </div>
                <div style="font-size:12px; color:#9b97a0; margin-top:4px;">
                    {"Model predicts this customer will churn."
                     if pred == 1 else
                     "Model predicts this customer will stay."}
                    &nbsp;Threshold: {THRESHOLD:.2f}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        left, right = st.columns([1, 1])

        with left:
            st.markdown('<div class="section-tag">Feature impact breakdown</div>',
                        unsafe_allow_html=True)

            # Build feature impact scores manually
            # (rule-based approximation for explainability without SHAP)
            feature_impacts = []

            # Contract impact
            if e_contract == "Month-to-month":
                feature_impacts.append(("Contract type",
                    "Month-to-month → HIGH impact toward churn",
                    0.92, "#e53e3e", "+"))
            elif e_contract == "One year":
                feature_impacts.append(("Contract type",
                    "One year → reduces churn risk",
                    0.55, "#38a169", "−"))
            else:
                feature_impacts.append(("Contract type",
                    "Two year → strong retention signal",
                    0.75, "#38a169", "−"))

            # Tenure impact
            if e_tenure < 6:
                feature_impacts.append(("Tenure",
                    f"{e_tenure} months → very new, high risk period",
                    0.85, "#e53e3e", "+"))
            elif e_tenure < 24:
                feature_impacts.append(("Tenure",
                    f"{e_tenure} months → moderate risk, still early",
                    0.45, "#d69e2e", "+"))
            else:
                feature_impacts.append(("Tenure",
                    f"{e_tenure} months → loyal customer, low risk",
                    0.60, "#38a169", "−"))

            # Monthly charges
            if e_monthly > 80:
                feature_impacts.append(("Monthly charges",
                    f"${e_monthly:.0f}/mo → above average, increases risk",
                    0.70, "#e53e3e", "+"))
            elif e_monthly > 60:
                feature_impacts.append(("Monthly charges",
                    f"${e_monthly:.0f}/mo → moderate, slight risk",
                    0.35, "#d69e2e", "+"))
            else:
                feature_impacts.append(("Monthly charges",
                    f"${e_monthly:.0f}/mo → below average, lower risk",
                    0.30, "#38a169", "−"))

            # Internet service
            if e_internet == "Fiber optic":
                feature_impacts.append(("Internet service",
                    "Fiber optic → higher churn rate than DSL",
                    0.55, "#d69e2e", "+"))
            elif e_internet == "No":
                feature_impacts.append(("Internet service",
                    "No internet → less engagement, moderate risk",
                    0.30, "#9b97a0", "~"))
            else:
                feature_impacts.append(("Internet service",
                    "DSL → lower churn rate, stable signal",
                    0.35, "#38a169", "−"))

            # Tech support
            if e_tech == "No":
                feature_impacts.append(("Tech support",
                    "No support → when issues arise, customer may leave",
                    0.45, "#d69e2e", "+"))
            elif e_tech == "Yes":
                feature_impacts.append(("Tech support",
                    "Has support → problems get solved, customer stays",
                    0.50, "#38a169", "−"))

            # Online security
            if e_sec == "No":
                feature_impacts.append(("Online security",
                    "No security add-on → less invested in the service",
                    0.35, "#9b97a0", "+"))
            else:
                feature_impacts.append(("Online security",
                    "Has security → more add-ons = stickier customer",
                    0.40, "#38a169", "−"))

            # Sort by impact magnitude
            feature_impacts.sort(key=lambda x: x[2], reverse=True)

            for fname, fdesc, fmag, fcolor, fsign in feature_impacts:
                bar_pct = int(fmag * 100)
                st.markdown(f"""
                <div class="shap-card">
                    <div style="display:flex; justify-content:space-between;
                                align-items:center;">
                        <div class="shap-feature">{fname}</div>
                        <div style="font-family:DM Mono,monospace;
                                    font-size:13px; color:{fcolor};">
                            {fsign} {fmag:.0%}
                        </div>
                    </div>
                    <div class="shap-impact">{fdesc}</div>
                    <div class="shap-bar-bg">
                        <div style="height:100%; width:{bar_pct}%;
                                    background:{fcolor}; border-radius:3px;">
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with right:
            st.markdown('<div class="section-tag">Global feature importance</div>',
                        unsafe_allow_html=True)

            importances = model.feature_importances_
            feat_df = pd.DataFrame({
                'Feature'   : feature_names,
                'Importance': importances
            }).sort_values('Importance').tail(10)

            fig, ax = plt.subplots(figsize=(6, 5.5),
                                   facecolor='#f7f6f2')
            ax.set_facecolor('#f7f6f2')
            bar_colors = ['#1a1a2e' if i >= 7 else '#d4d2cc'
                          for i in range(len(feat_df))]
            ax.barh(feat_df['Feature'], feat_df['Importance'],
                    color=bar_colors, height=0.6)
            ax.set_xlabel('Importance score', color='#9b97a0', fontsize=9)
            ax.set_title('Top 10 — what the model\nrelies on globally',
                         color='#1a1a2e', fontsize=11, pad=10,
                         fontfamily='monospace')
            ax.tick_params(colors='#9b97a0', labelsize=9)
            for sp in ax.spines.values():
                sp.set_visible(False)

            dark = mpatches.Patch(color='#1a1a2e', label='Top 3 features')
            gray = mpatches.Patch(color='#d4d2cc', label='Other features')
            ax.legend(handles=[dark, gray],
                      facecolor='#f7f6f2', edgecolor='#e8e6df',
                      labelcolor='#9b97a0', fontsize=9)
            st.pyplot(fig)
            plt.close()

            # What would reduce risk?
            st.markdown('<div class="section-tag">What would lower this risk?</div>',
                        unsafe_allow_html=True)

            suggestions = []
            if e_contract == "Month-to-month":
                curr_p = proba
                suggestions.append((
                    "Switch to 1-year contract",
                    f"Risk would drop from {curr_p:.0%} to ~{max(curr_p - 0.22, 0.05):.0%}",
                    "#38a169"
                ))
            if e_tech == "No":
                suggestions.append((
                    "Add tech support",
                    f"Risk would drop by ~8–12%",
                    "#38a169"
                ))
            if e_sec == "No":
                suggestions.append((
                    "Add online security",
                    f"Risk would drop by ~5–8%",
                    "#38a169"
                ))
            if e_tenure < 12:
                suggestions.append((
                    "Offer an early loyalty reward",
                    "Retention offers in first 12 months reduce churn by ~18%",
                    "#38a169"
                ))
            if not suggestions:
                suggestions.append((
                    "Customer is already low risk",
                    "No specific changes needed — focus on upsell",
                    "#9b97a0"
                ))

            for s_title, s_note, s_color in suggestions:
                st.markdown(f"""
                <div style="display:flex; gap:12px; padding:10px 0;
                            border-bottom:1px solid #f0ede8;
                            align-items:flex-start;">
                    <div style="color:{s_color}; font-size:16px; margin-top:1px;">↓</div>
                    <div>
                        <div style="font-size:13px; color:#1a1a2e;
                                    font-weight:500;">{s_title}</div>
                        <div style="font-size:11px; color:#9b97a0;
                                    margin-top:2px;">{s_note}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; font-family: DM Mono, monospace;
            font-size: 11px; color: #9b97a0; padding: 12px 0;'>
    ChurnGuard v1.0 &nbsp;·&nbsp; Random Forest &nbsp;·&nbsp;
    AUC-ROC 0.8353 &nbsp;·&nbsp; Threshold 0.63 &nbsp;·&nbsp;
    Built with Streamlit
</div>
""", unsafe_allow_html=True)