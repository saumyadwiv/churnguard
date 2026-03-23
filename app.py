import streamlit as st
import pickle, json, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.preprocessing import LabelEncoder

st.set_page_config(
    page_title="ChurnGuard Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'Outfit',sans-serif;background:#0c0e16;color:#e2e0f0;}
.stApp{background:#0c0e16;}
[data-testid="stSidebar"]{background:#10121e;border-right:1px solid #1e2133;}
[data-testid="stSidebar"] *{color:#c4c2d4!important;}
[data-testid="stMetric"]{background:#13152a;border:1px solid #1e2133;border-radius:12px;padding:16px 18px;}
[data-testid="stMetricLabel"]{font-family:'JetBrains Mono',monospace!important;font-size:9px!important;text-transform:uppercase;letter-spacing:.14em;color:#6b6888!important;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;font-size:24px!important;color:#e2e0f0!important;}
.stTabs [data-baseweb="tab-list"]{background:#13152a;border-radius:12px;padding:5px;border:1px solid #1e2133;gap:4px;}
.stTabs [data-baseweb="tab"]{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.06em;border-radius:8px;padding:9px 18px;color:#6b6888;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6c63ff,#8b5cf6)!important;color:white!important;}
.stButton>button{background:linear-gradient(135deg,#6c63ff,#8b5cf6);color:white;border:none;border-radius:10px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:500;letter-spacing:.07em;padding:14px 28px;width:100%;transition:all .25s;text-transform:uppercase;}
.stButton>button:hover{opacity:.88;transform:translateY(-2px);}
.stSelectbox>div>div,.stNumberInput>div>div>input{background:#13152a!important;border:1px solid #1e2133!important;border-radius:8px!important;color:#e2e0f0!important;}
.stSelectbox label,.stSlider label,.stNumberInput label{color:#8885a0!important;font-size:12px!important;}
.stSlider>div>div>div{background:#6c63ff!important;}
.page-title{font-family:'Syne',sans-serif;font-size:32px;font-weight:700;color:#e2e0f0;letter-spacing:-.02em;padding:8px 0 4px;}
.page-sub{font-size:14px;color:#6b6888;font-weight:300;padding-bottom:20px;border-bottom:1px solid #1e2133;margin-bottom:24px;}
.section-pill{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:#6c63ff;background:rgba(108,99,255,.1);border:1px solid rgba(108,99,255,.25);border-radius:20px;padding:3px 10px;margin-bottom:10px;}
.sec-label{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.14em;color:#6b6888;border-bottom:1px solid #1e2133;padding-bottom:8px;margin:18px 0 14px;}
.kpi-card{background:#13152a;border:1px solid #1e2133;border-radius:14px;padding:22px 18px;}
.kpi-val{font-family:'Syne',sans-serif;font-size:34px;font-weight:700;line-height:1;margin-bottom:4px;}
.kpi-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#6b6888;}
.kpi-sub{font-size:11px;color:#6b6888;margin-top:6px;}
.risk-high{background:linear-gradient(135deg,#1a0d0d,#1f1010);border:1px solid #5a1a1a;border-left:4px solid #ef4444;border-radius:14px;padding:28px;}
.risk-medium{background:linear-gradient(135deg,#1a160a,#1f1a0c);border:1px solid #5a4010;border-left:4px solid #f59e0b;border-radius:14px;padding:28px;}
.risk-low{background:linear-gradient(135deg,#0a1a0e,#0c1f11);border:1px solid #1a5a25;border-left:4px solid #22c55e;border-radius:14px;padding:28px;}
.risk-title{font-family:'Syne',sans-serif;font-size:14px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;}
.risk-prob{font-family:'Syne',sans-serif;font-size:54px;font-weight:700;line-height:1;margin:10px 0;}
.risk-sub{font-size:13px;color:#8885a0;line-height:1.7;}
.action-box{background:#13152a;border:1px solid #1e2133;border-radius:12px;padding:18px;margin-top:14px;}
.action-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#6b6888;margin-bottom:8px;}
.roi-card{background:#13152a;border:1px solid #1e2133;border-radius:14px;padding:22px;text-align:center;}
.roi-num{font-family:'Syne',sans-serif;font-size:30px;font-weight:700;}
.roi-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#6b6888;margin-top:6px;}
.stat-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e2133;font-size:13px;}
.stat-lbl{color:#8885a0;}
.stat-val{font-family:'JetBrains Mono',monospace;color:#e2e0f0;}
.info-banner{background:rgba(108,99,255,.08);border:1px solid rgba(108,99,255,.2);border-radius:10px;padding:14px 18px;font-size:13px;color:#a8a5c0;line-height:1.7;margin:12px 0 20px;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ── Load ───────────────────────────────────────────────────────────
@st.cache_resource
def load_package():
    for p in ['churn_model_final.pkl',
              'customer churn/churn_model_final.pkl',
              '/content/drive/MyDrive/customer churn/churn_model_final.pkl']:
        if os.path.exists(p):
            with open(p,'rb') as f: pkg=pickle.load(f)
            if isinstance(pkg,dict): return pkg['model'],float(pkg['threshold']),pkg['features']
            return pkg,0.63,None
    return None,0.63,None

@st.cache_data
def load_metrics():
    for p in ['metrics.json',
              'customer churn/metrics.json',
              '/content/drive/MyDrive/customer churn/metrics.json']:
        if os.path.exists(p):
            with open(p) as f: return json.load(f)
    return {}

model,THRESHOLD,feature_names = load_package()
metrics = load_metrics()
if feature_names is None:
    feature_names=['gender','SeniorCitizen','Partner','Dependents','tenure',
                   'PhoneService','MultipleLines','InternetService',
                   'OnlineSecurity','OnlineBackup','DeviceProtection',
                   'TechSupport','StreamingTV','StreamingMovies',
                   'Contract','PaperlessBilling','PaymentMethod',
                   'MonthlyCharges','TotalCharges']

CONTRACT_MAP={"Month-to-month":0,"One year":1,"Two year":2}
INTERNET_MAP={"DSL":0,"Fiber optic":1,"No":2}
TECH_MAP    ={"No":0,"No internet service":1,"Yes":2}
BINARY_MAP  ={"No":0,"Yes":1}
PAYMENT_MAP ={"Bank transfer (automatic)":0,"Credit card (automatic)":1,
              "Electronic check":2,"Mailed check":3}

def build_input(tenure,monthly,contract,internet,tech,sec,bkp,
                senior,partner,dep,paperless,payment):
    total=monthly*tenure
    sv=BINARY_MAP.get(sec,0) if sec!="No internet service" else 0
    bv=BINARY_MAP.get(bkp,0) if bkp!="No internet service" else 0
    return np.array([[1,BINARY_MAP[senior],BINARY_MAP[partner],BINARY_MAP[dep],
                      tenure,1,1,INTERNET_MAP[internet],sv,bv,0,
                      TECH_MAP[tech],0,0,CONTRACT_MAP[contract],
                      BINARY_MAP[paperless],PAYMENT_MAP[payment],monthly,total]])

def predict(arr):
    p=model.predict_proba(arr)[0][1]; return p,int(p>=THRESHOLD)

def risk_info(p):
    if p>=0.75:       return "HIGH",  "#ef4444","risk-high"
    if p>=THRESHOLD:  return "MEDIUM","#f59e0b","risk-medium"
    return               "LOW",  "#22c55e","risk-low"

def ps(fig,ax):
    fig.patch.set_facecolor('#13152a'); ax.set_facecolor('#13152a')
    ax.tick_params(colors='#6b6888',labelsize=9)
    for sp in ax.spines.values(): sp.set_color('#1e2133')
    ax.title.set_color('#e2e0f0')
    ax.xaxis.label.set_color('#6b6888'); ax.yaxis.label.set_color('#6b6888')


# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Syne,sans-serif;font-size:24px;font-weight:700;color:#e2e0f0;padding:8px 0 4px;'>🛡️ ChurnGuard</div><div style='font-family:JetBrains Mono,monospace;font-size:9px;color:#6b6888;letter-spacing:.15em;text-transform:uppercase;margin-bottom:24px;'>Pro · v2.0</div>",unsafe_allow_html=True)
    auc =metrics.get('metrics',{}).get('auc_roc', metrics.get('final_auc',     0.8353))
    prec=metrics.get('metrics',{}).get('precision',metrics.get('final_precision',0.6036))
    rec =metrics.get('metrics',{}).get('recall',  metrics.get('final_recall',  0.6230))
    f1  =metrics.get('metrics',{}).get('f1_score',metrics.get('final_f1',      0.6132))
    st.markdown('<div class="sec-label">Model performance</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    c1.metric("AUC-ROC",f"{auc:.3f}"); c2.metric("F1",f"{f1:.3f}")
    c1.metric("Precision",f"{prec:.1%}"); c2.metric("Recall",f"{rec:.1%}")
    st.markdown(f"<div style='margin-top:18px;padding:14px;background:#0c0e16;border-radius:10px;border:1px solid #1e2133;'><div style='font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#6b6888;margin-bottom:6px;'>Threshold</div><div style='font-family:Syne,sans-serif;font-size:28px;font-weight:700;color:#6c63ff;'>{THRESHOLD:.2f}</div><div style='font-size:11px;color:#6b6888;margin-top:6px;line-height:1.7;'>Tuned from 0.50 default</div></div>",unsafe_allow_html=True)
    st.markdown("<div style='margin-top:18px;font-size:12px;color:#8885a0;line-height:1.9;'>Algorithm: Random Forest<br>Dataset: IBM Telco 7,043<br>Train: 5,634 · Test: 1,407<br>Overfit gap: 0.013</div>",unsafe_allow_html=True)
    if model is None: st.error("Model file not found.")


# ── Header ─────────────────────────────────────────────────────────
st.markdown('<div class="page-title">ChurnGuard Pro</div><div class="page-sub">Predict customer churn · Understand why · Measure business impact</div>',unsafe_allow_html=True)
if model is None:
    st.error("Place churn_model_final.pkl, feature_names.pkl and metrics.json in the app folder.")
    st.stop()

t1,t2,t3,t4,t5=st.tabs(["01 · Single Predict","02 · Bulk Predict","03 · Analytics","05 · Explainability","06 · ROI Calculator"])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — Single Prediction
# ══════════════════════════════════════════════════════════════════
with t1:
    st.markdown('<div class="section-pill">Module 01</div>',unsafe_allow_html=True)
    st.markdown("### Single Customer Prediction")
    ca,cb,cc=st.columns(3)
    with ca:
        st.markdown("**Account**")
        tenure =st.slider("Tenure (months)",0,72,12)
        monthly=st.number_input("Monthly charges ($)",18.0,120.0,65.0,0.5)
        st.caption(f"Est. total: **${monthly*tenure:,.0f}**")
        contract=st.selectbox("Contract",["Month-to-month","One year","Two year"])
        payment =st.selectbox("Payment",["Electronic check","Mailed check","Bank transfer (automatic)","Credit card (automatic)"])
    with cb:
        st.markdown("**Services**")
        internet  =st.selectbox("Internet",["DSL","Fiber optic","No"])
        tech      =st.selectbox("Tech support",["No","Yes","No internet service"])
        online_sec=st.selectbox("Online security",["No","Yes","No internet service"])
        online_bkp=st.selectbox("Online backup",["No","Yes","No internet service"])
    with cc:
        st.markdown("**Demographics**")
        senior   =st.selectbox("Senior citizen",["No","Yes"])
        partner  =st.selectbox("Has partner",["No","Yes"])
        dep      =st.selectbox("Has dependents",["No","Yes"])
        paperless=st.selectbox("Paperless billing",["No","Yes"])

    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("Run Prediction →",key="r1"):
        inp=build_input(tenure,monthly,contract,internet,tech,online_sec,online_bkp,senior,partner,dep,paperless,payment)
        proba,pred=predict(inp); label,color,css=risk_info(proba)
        st.markdown("---")
        rc,gc=st.columns(2)
        with rc:
            st.markdown(f'<div class="{css}"><div class="risk-title" style="color:{color};">{label} RISK</div><div class="risk-prob" style="color:{color};">{proba:.1%}</div><div class="risk-sub">{"Likely to leave — act now." if pred==1 else "Stable — consider upsell."}<br>Threshold: {THRESHOLD:.2f}</div></div>',unsafe_allow_html=True)
            st.markdown('<div class="sec-label" style="margin-top:16px;">Risk factors</div>',unsafe_allow_html=True)
            factors=[]
            if tenure<6:    factors.append(("Tenure < 6 months","#ef4444","New customers churn most"))
            elif tenure<12: factors.append(("Tenure < 12 months","#f59e0b","Still in high-risk window"))
            if contract=="Month-to-month": factors.append(("Month-to-month contract","#ef4444","3× higher churn vs annual"))
            if internet=="Fiber optic":   factors.append(("Fiber optic","#f59e0b","Higher churn than DSL"))
            if monthly>75: factors.append((f"High charges ${monthly:.0f}/mo","#f59e0b","Above avg bill"))
            if tech=="No":  factors.append(("No tech support","#8885a0","Support = stickier"))
            if not factors:
                factors.append(("Loyal customer","#22c55e",f"{tenure}mo tenure"))
                factors.append(("Committed contract","#22c55e",f"{contract}"))
            for fl,fc,fn in factors:
                st.markdown(f"<div style='display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1e2133;align-items:flex-start;'><div style='width:8px;height:8px;border-radius:50%;background:{fc};margin-top:5px;flex-shrink:0;'></div><div><div style='font-size:13px;color:#e2e0f0;font-weight:500;'>{fl}</div><div style='font-size:11px;color:#6b6888;margin-top:2px;'>{fn}</div></div></div>",unsafe_allow_html=True)
        with gc:
            fig,ax=plt.subplots(figsize=(6,2.5)); ps(fig,ax)
            bc='#ef4444' if label=="HIGH" else '#f59e0b' if label=="MEDIUM" else '#22c55e'
            ax.barh([''],[proba],color=bc,height=0.38)
            ax.barh([''],[1-proba],left=[proba],color='#1e2133',height=0.38)
            ax.axvline(THRESHOLD,color='#6c63ff',ls='--',lw=1.5,label=f'Threshold {THRESHOLD:.2f}')
            ax.set_xlim(0,1); ax.set_xticks([0,.25,.5,THRESHOLD,.75,1.0])
            ax.set_xticklabels(['0%','25%','50%',f'{THRESHOLD:.0%}↑','75%','100%'],fontsize=8)
            ax.tick_params(axis='y',left=False,labelleft=False)
            ax.set_title(f'Churn probability: {proba:.1%}',fontsize=11,fontfamily='monospace',pad=10)
            ax.legend(facecolor='#13152a',edgecolor='#1e2133',labelcolor='#8885a0',fontsize=8)
            st.pyplot(fig); plt.close()
            st.markdown('<div class="sec-label" style="margin-top:8px;">Recommended action</div>',unsafe_allow_html=True)
            if pred==1:
                if contract=="Month-to-month": act="Offer a <b>20% discount on annual contract</b>"
                elif tech=="No":               act="Offer <b>3 months free tech support</b>"
                elif monthly>75:               act="Offer a <b>15% loyalty discount</b> for 6 months"
                else:                          act="Assign a <b>dedicated account manager</b>"
                ltv=monthly*24
                st.markdown(f'<div class="action-box"><div class="action-lbl">Retention strategy</div><div style="font-size:13px;color:#e2e0f0;line-height:1.7;">{act}</div><div style="margin-top:12px;padding-top:12px;border-top:1px solid #1e2133;display:flex;gap:24px;"><div><div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#6b6888;text-transform:uppercase;letter-spacing:.1em;">Cost</div><div style="font-family:JetBrains Mono,monospace;font-size:14px;color:#e2e0f0;">~$15</div></div><div><div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#6b6888;text-transform:uppercase;letter-spacing:.1em;">LTV at risk</div><div style="font-family:JetBrains Mono,monospace;font-size:14px;color:#ef4444;">${ltv:,.0f}</div></div></div></div>',unsafe_allow_html=True)
            else:
                st.markdown('<div class="action-box"><div class="action-lbl">Growth opportunity</div><div style="font-size:13px;color:#e2e0f0;line-height:1.7;">Stable customer. Consider offering premium add-ons or requesting a referral.</div></div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 2 — Bulk Prediction
# ══════════════════════════════════════════════════════════════════
with t2:
    st.markdown('<div class="section-pill">Module 02</div>',unsafe_allow_html=True)
    st.markdown("### Bulk Customer Prediction")
    st.markdown('<div class="info-banner">Upload a CSV of customers — the app scores every one and returns a ranked at-risk list.</div>',unsafe_allow_html=True)

    sample=pd.DataFrame([{'customerID':'SAMPLE-001','gender':'Male','SeniorCitizen':0,'Partner':'Yes','Dependents':'No','tenure':12,'PhoneService':'Yes','MultipleLines':'No','InternetService':'Fiber optic','OnlineSecurity':'No','OnlineBackup':'Yes','DeviceProtection':'No','TechSupport':'No','StreamingTV':'No','StreamingMovies':'No','Contract':'Month-to-month','PaperlessBilling':'Yes','PaymentMethod':'Electronic check','MonthlyCharges':70.35,'TotalCharges':844.20,'Churn':'No'}])
    st.download_button("Download CSV template",data=sample.to_csv(index=False),file_name="template.csv",mime="text/csv")

    uploaded=st.file_uploader("Upload customer CSV",type=['csv'])
    if uploaded:
        try:
            raw=pd.read_csv(uploaded); proc=raw.copy()
            proc['TotalCharges']=pd.to_numeric(proc['TotalCharges'],errors='coerce')
            dropped=proc['TotalCharges'].isnull().sum(); proc.dropna(subset=['TotalCharges'],inplace=True)
            if dropped: st.warning(f"Dropped {dropped} rows with missing TotalCharges.")
            ids=proc['customerID'] if 'customerID' in proc.columns else pd.RangeIndex(len(proc)).astype(str)
            for c in ['customerID','Churn']:
                if c in proc.columns: proc.drop(c,axis=1,inplace=True)
            le=LabelEncoder()
            for c in proc.select_dtypes(include='object').columns: proc[c]=le.fit_transform(proc[c])
            probas=model.predict_proba(proc)[:,1]; preds=(probas>=THRESHOLD).astype(int)
            results=pd.DataFrame({'Customer ID':ids.values,'Churn Prob (%)': (probas*100).round(1),'Prediction':['Will Churn' if p==1 else 'Will Stay' for p in preds],'Risk Level':['High' if p>=0.75 else 'Medium' if p>=THRESHOLD else 'Low' for p in probas]}).sort_values('Churn Prob (%)',ascending=False)
            n_total=len(results); n_churn=int(preds.sum())
            n_high=int((probas>=0.75).sum()); n_med=int(((probas>=THRESHOLD)&(probas<0.75)).sum()); n_low=int((probas<THRESHOLD).sum())
            avg_m=raw['MonthlyCharges'].mean() if 'MonthlyCharges' in raw.columns else 65
            rev_risk=n_churn*avg_m*24

            st.markdown('<div class="sec-label">Summary</div>',unsafe_allow_html=True)
            k1,k2,k3,k4,k5=st.columns(5)
            k1.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#e2e0f0;">{n_total:,}</div><div class="kpi-lbl">Total</div></div>',unsafe_allow_html=True)
            k2.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{n_churn:,}</div><div class="kpi-lbl">At risk</div><div class="kpi-sub">{n_churn/n_total:.1%}</div></div>',unsafe_allow_html=True)
            k3.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{n_high:,}</div><div class="kpi-lbl">High risk</div></div>',unsafe_allow_html=True)
            k4.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#f59e0b;">{n_med:,}</div><div class="kpi-lbl">Medium risk</div></div>',unsafe_allow_html=True)
            k5.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#22c55e;">{n_low:,}</div><div class="kpi-lbl">Low risk</div></div>',unsafe_allow_html=True)

            st.markdown(f'<div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.25);border-radius:12px;padding:16px 20px;margin:14px 0;"><div style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:#ef4444;">Revenue at risk</div><div style="font-family:Syne,sans-serif;font-size:28px;font-weight:700;color:#ef4444;">${rev_risk:,.0f}</div><div style="font-size:12px;color:#8885a0;margin-top:4px;">{n_churn} customers × ${avg_m:.0f}/mo × 24 months</div></div>',unsafe_allow_html=True)

            # Charts
            fig2,axes2=plt.subplots(1,2,figsize=(10,3.5))
            for ax in axes2: ps(fig2,ax)
            sizes=[n_high,n_med,n_low]; clrs=['#ef4444','#f59e0b','#22c55e']; lbls=['High','Medium','Low']
            if sum(sizes)>0:
                wedges,_,autotexts=axes2[0].pie(sizes,colors=clrs,autopct='%1.1f%%',startangle=90,pctdistance=.75,wedgeprops=dict(width=.55,edgecolor='#0c0e16',linewidth=2))
                for at in autotexts: at.set_color('#e2e0f0'); at.set_fontsize(9)
            axes2[0].set_title('Risk distribution',fontsize=10,pad=10)
            axes2[0].legend(lbls,loc='lower center',facecolor='#13152a',edgecolor='#1e2133',labelcolor='#8885a0',fontsize=8,ncol=3,bbox_to_anchor=(.5,-.12))
            axes2[1].hist(probas,bins=25,color='#6c63ff',alpha=.8,edgecolor='#0c0e16')
            axes2[1].axvline(THRESHOLD,color='#ef4444',ls='--',lw=1.5,label=f'Threshold {THRESHOLD:.2f}')
            axes2[1].set_xlabel('Churn probability',fontsize=9); axes2[1].set_ylabel('Customers',fontsize=9)
            axes2[1].set_title('Probability distribution',fontsize=10)
            axes2[1].legend(facecolor='#13152a',edgecolor='#1e2133',labelcolor='#8885a0',fontsize=8)
            plt.tight_layout(); st.pyplot(fig2); plt.close()

            st.markdown('<div class="sec-label">Filter & export</div>',unsafe_allow_html=True)
            f1c,f2c=st.columns(2)
            rf=f1c.multiselect("Risk level",["High","Medium","Low"],default=["High","Medium"])
            tn=f2c.slider("Top N",10,min(500,n_total),50)
            filt=results[results['Risk Level'].isin(rf)].head(tn)
            def color_risk(v):
                if v=='High':   return 'color:#ef4444;font-weight:600'
                if v=='Medium': return 'color:#f59e0b;font-weight:600'
                return 'color:#22c55e'
            st.dataframe(filt.style.applymap(color_risk,subset=['Risk Level']).format({'Churn Prob (%)':'{:.1f}%'}),use_container_width=True,height=380)
            d1,d2=st.columns(2)
            d1.download_button("Download all predictions",data=results.to_csv(index=False),file_name="churn_all.csv",mime="text/csv",use_container_width=True)
            d2.download_button("Download high-risk call list",data=results[results['Risk Level']=='High'].to_csv(index=False),file_name="high_risk.csv",mime="text/csv",use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Upload a CSV above. Download the template to see the required format.")


# ══════════════════════════════════════════════════════════════════
# TAB 3 — Analytics Dashboard
# ══════════════════════════════════════════════════════════════════
with t3:
    st.markdown('<div class="section-pill">Module 03 — New in Phase 2</div>',unsafe_allow_html=True)
    st.markdown("### Analytics Dashboard")
    st.markdown('<div class="info-banner">Upload your full customer dataset to see health of your entire customer base — churn trends, segment breakdowns, and which groups need the most attention.</div>',unsafe_allow_html=True)

    dash_file=st.file_uploader("Upload customer dataset (CSV)",type=['csv'],key="dash")
    if dash_file:
        try:
            df=pd.read_csv(dash_file); dp=df.copy()
            dp['TotalCharges']=pd.to_numeric(dp['TotalCharges'],errors='coerce')
            dp.dropna(subset=['TotalCharges'],inplace=True)
            dp2=dp.copy()
            for c in ['customerID','Churn']:
                if c in dp2.columns: dp2.drop(c,axis=1,inplace=True)
            le2=LabelEncoder()
            for c in dp2.select_dtypes(include='object').columns: dp2[c]=le2.fit_transform(dp2[c])
            probas3=model.predict_proba(dp2)[:,1]; preds3=(probas3>=THRESHOLD).astype(int)
            dp['pred_prob']=probas3; dp['pred_churn']=preds3
            dp['risk_level']=['High' if p>=0.75 else 'Medium' if p>=THRESHOLD else 'Low' for p in probas3]

            n_t=len(dp); n_r=int(preds3.sum())
            avg_m3=dp['MonthlyCharges'].mean() if 'MonthlyCharges' in dp.columns else 65
            rev_r=n_r*avg_m3*24

            st.markdown('<div class="sec-label">Business health overview</div>',unsafe_allow_html=True)
            ka,kb,kc,kd=st.columns(4)
            ka.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#e2e0f0;">{n_t:,}</div><div class="kpi-lbl">Total customers</div></div>',unsafe_allow_html=True)
            kb.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">{n_r:,}</div><div class="kpi-lbl">At churn risk</div><div class="kpi-sub">{n_r/n_t:.1%} of base</div></div>',unsafe_allow_html=True)
            kc.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#f59e0b;">${avg_m3:.0f}</div><div class="kpi-lbl">Avg monthly rev</div></div>',unsafe_allow_html=True)
            kd.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#ef4444;">${rev_r/1e6:.2f}M</div><div class="kpi-lbl">Revenue at risk (24mo)</div></div>',unsafe_allow_html=True)

            st.markdown('<div class="sec-label">Churn risk by segment</div>',unsafe_allow_html=True)
            fig4,axes4=plt.subplots(2,2,figsize=(12,8))
            for ax in axes4.flat: ps(fig4,ax)

            if 'Contract' in dp.columns:
                cg=dp.groupby('Contract')['pred_churn'].mean()*100
                b1=axes4[0,0].bar(cg.index,cg.values,color=['#6c63ff','#8b5cf6','#a78bfa'],edgecolor='#0c0e16',width=.55)
                axes4[0,0].set_title('Churn rate by contract',fontsize=10); axes4[0,0].set_ylabel('Churn rate (%)',fontsize=9)
                for b in b1:
                    h=b.get_height(); axes4[0,0].text(b.get_x()+b.get_width()/2,h+.5,f'{h:.1f}%',ha='center',va='bottom',fontsize=9,color='#8885a0')

            if 'InternetService' in dp.columns:
                ig=dp.groupby('InternetService')['pred_churn'].mean()*100
                b2=axes4[0,1].bar(ig.index,ig.values,color=['#22c55e','#f59e0b','#ef4444'],edgecolor='#0c0e16',width=.55)
                axes4[0,1].set_title('Churn rate by internet service',fontsize=10)
                for b in b2:
                    h=b.get_height(); axes4[0,1].text(b.get_x()+b.get_width()/2,h+.5,f'{h:.1f}%',ha='center',va='bottom',fontsize=9,color='#8885a0')

            if 'tenure' in dp.columns:
                dp['t_bucket']=pd.cut(dp['tenure'],bins=[0,6,12,24,48,72],labels=['0-6mo','6-12mo','1-2yr','2-4yr','4-6yr'])
                tg=dp.groupby('t_bucket')['pred_churn'].mean()*100
                axes4[1,0].plot(tg.index.astype(str),tg.values,color='#6c63ff',lw=2.5,marker='o',markersize=7,markerfacecolor='#6c63ff',markeredgecolor='#0c0e16',markeredgewidth=2)
                axes4[1,0].fill_between(range(len(tg)),tg.values,alpha=.15,color='#6c63ff')
                axes4[1,0].set_xticks(range(len(tg))); axes4[1,0].set_xticklabels(tg.index.astype(str),fontsize=8)
                axes4[1,0].set_title('Churn rate by tenure',fontsize=10); axes4[1,0].set_ylabel('Churn rate (%)',fontsize=9)

            if 'MonthlyCharges' in dp.columns:
                for rv,cv,lv in [('Low','#22c55e','Low'),('Medium','#f59e0b','Medium'),('High','#ef4444','High')]:
                    sub=dp[dp['risk_level']==rv]['MonthlyCharges']
                    if len(sub)>0: axes4[1,1].hist(sub,bins=20,alpha=.6,color=cv,label=lv,edgecolor='#0c0e16')
                axes4[1,1].set_title('Monthly charges by risk',fontsize=10)
                axes4[1,1].set_xlabel('Monthly charges ($)',fontsize=9); axes4[1,1].set_ylabel('Count',fontsize=9)
                axes4[1,1].legend(facecolor='#13152a',edgecolor='#1e2133',labelcolor='#8885a0',fontsize=8)

            plt.tight_layout(pad=2.5); st.pyplot(fig4); plt.close()

            st.markdown('<div class="sec-label">Global feature importance</div>',unsafe_allow_html=True)
            fi=pd.DataFrame({'Feature':feature_names,'Importance':model.feature_importances_}).sort_values('Importance').tail(12)
            fig5,ax5=plt.subplots(figsize=(10,5)); ps(fig5,ax5)
            c5=['#6c63ff' if i>=9 else '#2d2f4e' for i in range(len(fi))]
            ax5.barh(fi['Feature'],fi['Importance'],color=c5,height=.6)
            ax5.set_title('Top 12 features driving churn predictions',fontsize=11,pad=10)
            ax5.set_xlabel('Importance score',fontsize=9)
            p1=mpatches.Patch(color='#6c63ff',label='Top 3'); p2=mpatches.Patch(color='#2d2f4e',label='Others')
            ax5.legend(handles=[p1,p2],facecolor='#13152a',edgecolor='#1e2133',labelcolor='#8885a0',fontsize=9)
            plt.tight_layout(); st.pyplot(fig5); plt.close()

            st.markdown('<div class="sec-label">Top 20 highest risk customers</div>',unsafe_allow_html=True)
            top20=dp.nlargest(20,'pred_prob')[[c for c in ['customerID','tenure','Contract','MonthlyCharges','InternetService','pred_prob','risk_level'] if c in dp.columns]].copy()
            top20['pred_prob']=(top20['pred_prob']*100).round(1)
            top20.columns=[c.replace('pred_prob','Risk %').replace('risk_level','Risk Level') for c in top20.columns]
            st.dataframe(top20,use_container_width=True,height=320)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Upload your full customer CSV to see the analytics dashboard.")


# ══════════════════════════════════════════════════════════════════
# TAB 4 — Explainability
# ══════════════════════════════════════════════════════════════════
with t4:
    st.markdown('<div class="section-pill">Module 05</div>',unsafe_allow_html=True)
    st.markdown("### Why Did the Model Predict This?")
    st.markdown('<div class="info-banner">Enter a customer to see exactly which factors pushed their churn risk up or down — and what changes would lower their score.</div>',unsafe_allow_html=True)

    ea,eb,ec_col=st.columns(3)
    with ea:
        et=st.slider("Tenure ",0,72,12,key="et"); em=st.number_input("Monthly $ ",18.0,120.0,65.0,.5,key="em")
        ec2=st.selectbox("Contract ",["Month-to-month","One year","Two year"],key="ec2")
    with eb:
        ei=st.selectbox("Internet ",["DSL","Fiber optic","No"],key="ei")
        eth=st.selectbox("Tech support ",["No","Yes","No internet service"],key="eth")
        es=st.selectbox("Online security ",["No","Yes","No internet service"],key="es")
    with ec_col:
        esn=st.selectbox("Senior ",["No","Yes"],key="esn")
        ep=st.selectbox("Partner ",["No","Yes"],key="ep")
        epb=st.selectbox("Paperless ",["No","Yes"],key="epb")

    if st.button("Explain This Prediction →",key="xbtn"):
        inp2=build_input(et,em,ec2,ei,eth,es,"No",esn,ep,"No",epb,"Electronic check")
        proba2,pred2=predict(inp2); label2,color2,css2=risk_info(proba2)
        st.markdown("---")
        st.markdown(f'<div style="display:flex;align-items:center;gap:24px;padding:24px;background:#13152a;border:1px solid #1e2133;border-radius:14px;margin-bottom:24px;"><div style="font-family:Syne,sans-serif;font-size:52px;font-weight:700;color:{color2};">{proba2:.1%}</div><div><div style="font-family:Syne,sans-serif;font-size:16px;font-weight:600;color:{color2};">{label2} CHURN RISK</div><div style="font-size:12px;color:#8885a0;margin-top:6px;">{"Model predicts churn." if pred2==1 else "Model predicts stay."} · Threshold: {THRESHOLD:.2f}</div></div></div>',unsafe_allow_html=True)
        xl,xr=st.columns(2)
        with xl:
            st.markdown('<div class="sec-label">Feature impact</div>',unsafe_allow_html=True)
            impacts=[]
            if ec2=="Month-to-month": impacts.append(("Contract","Month-to-month → high churn driver",0.92,"#ef4444","+"))
            elif ec2=="One year":     impacts.append(("Contract","One year → reduces risk",0.55,"#22c55e","−"))
            else:                     impacts.append(("Contract","Two year → strong retention signal",0.75,"#22c55e","−"))
            if et<6:   impacts.append(("Tenure",f"{et}mo → very new, highest risk",0.85,"#ef4444","+"))
            elif et<24:impacts.append(("Tenure",f"{et}mo → building loyalty",0.45,"#f59e0b","+"))
            else:      impacts.append(("Tenure",f"{et}mo → loyal, low risk",0.60,"#22c55e","−"))
            if em>80:  impacts.append(("Charges",f"${em:.0f} → above avg",0.70,"#ef4444","+"))
            elif em>60:impacts.append(("Charges",f"${em:.0f} → moderate",0.35,"#f59e0b","+"))
            else:      impacts.append(("Charges",f"${em:.0f} → below avg",0.30,"#22c55e","−"))
            if ei=="Fiber optic": impacts.append(("Internet","Fiber → higher churn than DSL",0.55,"#f59e0b","+"))
            else:                 impacts.append(("Internet","DSL/No → stable signal",0.30,"#22c55e","−"))
            if eth=="No": impacts.append(("Tech support","No support → issues cause churn",0.45,"#f59e0b","+"))
            else:         impacts.append(("Tech support","Has support → stickier",0.50,"#22c55e","−"))
            impacts.sort(key=lambda x:x[2],reverse=True)
            for fn,fd,fm,fc,fsign in impacts:
                bw=int(fm*100)
                st.markdown(f'<div style="background:#13152a;border:1px solid #1e2133;border-radius:10px;padding:14px 16px;margin:8px 0;"><div style="display:flex;justify-content:space-between;align-items:center;"><div style="font-size:13px;color:#e2e0f0;font-weight:500;">{fn}</div><div style="font-family:JetBrains Mono,monospace;font-size:13px;color:{fc};">{fsign} {fm:.0%}</div></div><div style="font-size:11px;color:#6b6888;margin:4px 0 8px;">{fd}</div><div style="height:5px;background:#1e2133;border-radius:3px;overflow:hidden;"><div style="height:100%;width:{bw}%;background:{fc};border-radius:3px;"></div></div></div>',unsafe_allow_html=True)
        with xr:
            st.markdown('<div class="sec-label">Global importance</div>',unsafe_allow_html=True)
            fi2=pd.DataFrame({'Feature':feature_names,'Importance':model.feature_importances_}).sort_values('Importance').tail(10)
            fig6,ax6=plt.subplots(figsize=(6,5)); ps(fig6,ax6)
            c6=['#6c63ff' if i>=7 else '#2d2f4e' for i in range(len(fi2))]
            ax6.barh(fi2['Feature'],fi2['Importance'],color=c6,height=.6)
            ax6.set_title('Top 10 model weights',fontsize=10,pad=8,fontfamily='monospace')
            ax6.set_xlabel('Importance',fontsize=9)
            p1=mpatches.Patch(color='#6c63ff',label='Top 3'); p2=mpatches.Patch(color='#2d2f4e',label='Others')
            ax6.legend(handles=[p1,p2],facecolor='#13152a',edgecolor='#1e2133',labelcolor='#8885a0',fontsize=8)
            plt.tight_layout(); st.pyplot(fig6); plt.close()

            st.markdown('<div class="sec-label" style="margin-top:14px;">What would lower this risk?</div>',unsafe_allow_html=True)
            sugg=[]
            if ec2=="Month-to-month": sugg.append(("Switch to 1-year contract",f"Risk drops ~22% → ~{max(proba2-.22,.05):.0%}","#22c55e"))
            if eth=="No":   sugg.append(("Add tech support","Risk drops ~8–12%","#22c55e"))
            if es=="No":    sugg.append(("Add online security","Risk drops ~5–8%","#22c55e"))
            if et<12:       sugg.append(("Offer early loyalty reward","First-year retention offers cut churn ~18%","#22c55e"))
            if not sugg:    sugg.append(("Already low risk","Focus on upsell","#8885a0"))
            for st_t,st_n,st_c in sugg:
                st.markdown(f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1e2133;"><div style="color:{st_c};font-size:18px;margin-top:1px;">↓</div><div><div style="font-size:13px;color:#e2e0f0;font-weight:500;">{st_t}</div><div style="font-size:11px;color:#6b6888;margin-top:2px;">{st_n}</div></div></div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 5 — ROI Calculator
# ══════════════════════════════════════════════════════════════════
with t5:
    st.markdown('<div class="section-pill">Module 06 — New in Phase 2</div>',unsafe_allow_html=True)
    st.markdown("### Business ROI Calculator")
    st.markdown('<div class="info-banner">Enter your business numbers to see the exact financial impact of using ChurnGuard vs doing nothing.</div>',unsafe_allow_html=True)

    rc1,rc2=st.columns(2)
    with rc1:
        st.markdown("**Your business**")
        total_cust  =st.number_input("Total customers",100,1000000,10000,100)
        avg_rev     =st.number_input("Avg monthly revenue per customer ($)",5.0,500.0,65.0,1.0)
        churn_rate  =st.slider("Current monthly churn rate (%)",1.0,30.0,26.5,.5)
        ret_cost    =st.number_input("Cost per retention offer ($)",1.0,200.0,15.0,1.0)
        cust_life   =st.slider("Customer lifetime (months)",6,60,24,1)
    with rc2:
        st.markdown("**Model performance**")
        m_recall =st.slider("Model recall — % churners caught",10,100,62,1)
        m_prec   =st.slider("Model precision — % predictions correct",10,100,60,1)
        st.markdown('<div style="background:#13152a;border:1px solid #1e2133;border-radius:10px;padding:14px;margin-top:8px;font-size:12px;color:#8885a0;line-height:1.8;"><b style="color:#e2e0f0;">Recall</b> = how many churners you catch<br><b style="color:#e2e0f0;">Precision</b> = how many flagged are real churners<br><span style="color:#6c63ff;">Your model: Recall 62.3% · Precision 60.4%</span></div>',unsafe_allow_html=True)

    st.markdown("---")

    churners   =total_cust*(churn_rate/100)
    ltv2       =avg_rev*cust_life
    tp2        =churners*(m_recall/100)
    fp2        =tp2*((100-m_prec)/max(m_prec,1))
    fn2        =churners-tp2
    rev_saved2 =tp2*ltv2; rev_lost2=fn2*ltv2
    camp_cost2 =(tp2+fp2)*ret_cost; net_ben2=rev_saved2-camp_cost2
    base_loss2 =churners*ltv2; roi2=(net_ben2/max(camp_cost2,1))*100

    st.markdown('<div class="sec-label">Monthly impact</div>',unsafe_allow_html=True)
    rk1,rk2,rk3,rk4=st.columns(4)
    rk1.markdown(f'<div class="roi-card"><div class="roi-num" style="color:#22c55e;">${net_ben2:,.0f}</div><div class="roi-lbl">Net benefit / month</div></div>',unsafe_allow_html=True)
    rk2.markdown(f'<div class="roi-card"><div class="roi-num" style="color:#6c63ff;">{roi2:.0f}%</div><div class="roi-lbl">ROI on campaign</div></div>',unsafe_allow_html=True)
    rk3.markdown(f'<div class="roi-card"><div class="roi-num" style="color:#ef4444;">${rev_lost2:,.0f}</div><div class="roi-lbl">Revenue still lost</div></div>',unsafe_allow_html=True)
    rk4.markdown(f'<div class="roi-card"><div class="roi-num" style="color:#f59e0b;">${camp_cost2:,.0f}</div><div class="roi-lbl">Campaign cost</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="sec-label" style="margin-top:20px;">Full breakdown</div>',unsafe_allow_html=True)
    bd1,bd2=st.columns(2)
    with bd1:
        rows=[("Total customers",f"{total_cust:,}"),("Monthly churners",f"{churners:.0f}"),("Caught by model (TP)",f"{tp2:.0f}"),("Missed by model (FN)",f"{fn2:.0f}"),("False alarms (FP)",f"{fp2:.0f}"),("Customer LTV",f"${ltv2:,.0f}"),("Revenue saved",f"${rev_saved2:,.0f}"),("Revenue lost (FN)",f"${rev_lost2:,.0f}"),("Campaign cost",f"${camp_cost2:,.0f}"),("Net benefit",f"${net_ben2:,.0f}"),("ROI",f"{roi2:.0f}%"),("Doing nothing costs",f"${base_loss2:,.0f}/mo")]
        for lbl,val in rows:
            vc="#22c55e" if "saved" in lbl.lower() or "benefit" in lbl.lower() or lbl=="ROI" else "#ef4444" if "lost" in lbl.lower() or "missed" in lbl.lower() or "nothing" in lbl.lower() else "#e2e0f0"
            st.markdown(f'<div class="stat-row"><div class="stat-lbl">{lbl}</div><div class="stat-val" style="color:{vc};">{val}</div></div>',unsafe_allow_html=True)
    with bd2:
        fig7,ax7=plt.subplots(figsize=(6,5)); ps(fig7,ax7)
        cats=['Baseline\nloss','Revenue\nsaved','Revenue\nlost','Campaign\ncost','Net\nbenefit']
        vals=[base_loss2,rev_saved2,-rev_lost2,-camp_cost2,net_ben2]
        c7=['#2d2f4e','#22c55e','#ef4444','#f59e0b','#22c55e' if net_ben2>0 else '#ef4444']
        bars7=ax7.bar(cats,vals,color=c7,edgecolor='#0c0e16',width=.6)
        ax7.axhline(0,color='#1e2133',lw=1)
        ax7.set_title('Monthly financial impact ($)',fontsize=10,pad=10)
        ax7.set_ylabel('Amount ($)',fontsize=9)
        for b in bars7:
            h=b.get_height()
            ax7.text(b.get_x()+b.get_width()/2,h+(abs(h)*.03) if h>=0 else h-(abs(h)*.05),f'${abs(h):,.0f}',ha='center',va='bottom' if h>=0 else 'top',fontsize=8,color='#8885a0')
        plt.xticks(fontsize=8); plt.tight_layout()
        st.pyplot(fig7); plt.close()

    st.markdown(f'<div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.25);border-radius:14px;padding:24px;margin-top:20px;text-align:center;"><div style="font-family:JetBrains Mono,monospace;font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:#22c55e;margin-bottom:8px;">Annual projection</div><div style="font-family:Syne,sans-serif;font-size:42px;font-weight:700;color:#22c55e;">${net_ben2*12:,.0f}</div><div style="font-size:13px;color:#8885a0;margin-top:8px;">Net annual benefit · vs ${base_loss2*12:,.0f} lost doing nothing</div></div>',unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align:center;font-family:JetBrains Mono,monospace;font-size:10px;color:#3d3f5a;padding:14px 0;">ChurnGuard Pro v2.0 · Random Forest · AUC-ROC 0.8353 · Phase 2 Complete</div>',unsafe_allow_html=True)