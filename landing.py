"""
landing.py — Public marketing home page for ChurnGuard Pro.

Shown to anyone who is not signed in and hasn't clicked "Get Started" yet.
Purely presentational: no auth, no DB calls. Clicking "Get Started" flips
`st.session_state.site_entered = True` and reruns, which hands control to
auth.require_login() (the sign in / create account page).
"""

import streamlit as st


def _inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
    .stApp{
        background:
            radial-gradient(1100px 550px at 12% -8%, rgba(108,99,255,.22), transparent 60%),
            radial-gradient(900px 500px at 88% 8%, rgba(139,92,246,.16), transparent 55%),
            radial-gradient(700px 500px at 50% 105%, rgba(34,197,94,.08), transparent 60%),
            #0c0e16;
    }
    #MainMenu{visibility:hidden;} footer{visibility:hidden;} header{background:transparent!important;}

    /* ── Top nav ─────────────────────────────────────────── */
    .lp-nav{display:flex;align-items:center;justify-content:space-between;padding:6px 4px 28px;}
    .lp-logo{font-family:'Syne',sans-serif;font-weight:800;font-size:20px;color:#f2f1fb;display:flex;align-items:center;gap:10px;letter-spacing:-.01em;}
    .lp-logo-badge{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6c63ff,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 8px 20px -6px rgba(108,99,255,.7);}
    .lp-nav-links{display:flex;gap:28px;font-size:13px;color:#9c99b5;font-weight:500;}

    /* ── Hero ────────────────────────────────────────────── */
    .lp-eyebrow{display:inline-flex;align-items:center;gap:8px;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#a89bff;background:rgba(108,99,255,.12);border:1px solid rgba(108,99,255,.3);border-radius:20px;padding:6px 14px;margin-bottom:22px;}
    .lp-eyebrow .dot{width:6px;height:6px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;}
    .lp-h1{font-family:'Syne',sans-serif;font-weight:800;font-size:52px;line-height:1.08;letter-spacing:-.03em;color:#f5f4fc;margin-bottom:20px;}
    .lp-h1 span{background:linear-gradient(135deg,#8b7bff,#c084fc 60%,#8b7bff);-webkit-background-clip:text;background-clip:text;color:transparent;}
    .lp-sub{font-size:16.5px;line-height:1.75;color:#9c99b5;font-weight:300;max-width:520px;margin-bottom:34px;}
    .lp-stats{display:flex;gap:36px;margin-top:38px;padding-top:26px;border-top:1px solid #1e2133;}
    .lp-stat-val{font-family:'Syne',sans-serif;font-size:26px;font-weight:700;color:#f2f1fb;}
    .lp-stat-lbl{font-family:'JetBrains Mono',monospace;font-size:9.5px;text-transform:uppercase;letter-spacing:.1em;color:#6b6888;margin-top:3px;}

    /* ── 3D tilted dashboard mockup ─────────────────────────*/
    .lp-scene{perspective:1600px;padding:20px 0 20px 30px;}
    .lp-card3d{
        transform:rotateY(-14deg) rotateX(7deg) rotateZ(1deg);
        transform-style:preserve-3d;
        background:linear-gradient(160deg,#171a30,#11132200);
        background-color:#12142497;
        border:1px solid #2a2d55;
        border-radius:20px;
        padding:22px 22px 26px;
        box-shadow:-40px 55px 90px -30px rgba(0,0,0,.65), 0 0 0 1px rgba(139,92,246,.08);
        transition:transform .6s cubic-bezier(.16,1,.3,1);
        backdrop-filter:blur(6px);
    }
    .lp-card3d:hover{transform:rotateY(-7deg) rotateX(3deg) rotateZ(0.5deg) scale(1.015);}
    .lp-card3d-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;}
    .lp-dots{display:flex;gap:6px;}
    .lp-dots span{width:9px;height:9px;border-radius:50%;display:inline-block;}
    .lp-card3d-title{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.1em;color:#8885a0;text-transform:uppercase;}
    .lp-gauge-wrap{display:flex;gap:16px;margin-bottom:14px;}
    .lp-mini-kpi{flex:1;background:#0e1020;border:1px solid #23264a;border-radius:12px;padding:12px 14px;transform:translateZ(18px);}
    .lp-mini-val{font-family:'Syne',sans-serif;font-size:20px;font-weight:700;}
    .lp-mini-lbl{font-family:'JetBrains Mono',monospace;font-size:8.5px;text-transform:uppercase;letter-spacing:.1em;color:#6b6888;margin-top:2px;}
    .lp-bars{display:flex;align-items:flex-end;gap:8px;height:90px;background:#0e1020;border:1px solid #23264a;border-radius:12px;padding:14px;transform:translateZ(10px);}
    .lp-bars .b{flex:1;border-radius:5px 5px 0 0;background:linear-gradient(180deg,#8b7bff,#6c63ff);box-shadow:0 6px 18px -4px rgba(108,99,255,.6);}
    .lp-float-chip{position:relative;transform:translateZ(46px) translate(-18px,-130px);background:#171a30;border:1px solid #2a2d55;border-radius:12px;padding:10px 14px;width:180px;box-shadow:0 20px 40px -12px rgba(0,0,0,.7);}

    /* ── Feature grid ────────────────────────────────────── */
    .lp-section-lbl{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:#6c63ff;text-align:center;margin-bottom:10px;}
    .lp-section-title{font-family:'Syne',sans-serif;font-size:32px;font-weight:700;color:#f2f1fb;text-align:center;margin-bottom:10px;letter-spacing:-.02em;}
    .lp-section-sub{font-size:14.5px;color:#8885a0;text-align:center;max-width:560px;margin:0 auto 44px;line-height:1.7;}
    .lp-feat{background:#12142a;border:1px solid #1e2133;border-radius:16px;padding:26px 24px;height:100%;transition:all .25s ease;}
    .lp-feat:hover{border-color:#4b45a8;transform:translateY(-4px);box-shadow:0 20px 40px -20px rgba(108,99,255,.45);}
    .lp-feat-icon{width:44px;height:44px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:21px;margin-bottom:16px;}
    .lp-feat-title{font-family:'Syne',sans-serif;font-size:16px;font-weight:700;color:#f2f1fb;margin-bottom:8px;}
    .lp-feat-body{font-size:13px;color:#8885a0;line-height:1.7;}

    /* ── CTA banner ──────────────────────────────────────── */
    .lp-cta{margin-top:70px;background:linear-gradient(135deg,#181c37,#221947);border:1px solid #362f6e;border-radius:24px;padding:52px 40px;text-align:center;position:relative;overflow:hidden;}
    .lp-cta::before{content:'';position:absolute;inset:0;background:radial-gradient(500px 200px at 50% 0%,rgba(139,92,246,.25),transparent 70%);}
    .lp-cta-title{font-family:'Syne',sans-serif;font-size:28px;font-weight:700;color:#f5f4fc;margin-bottom:10px;position:relative;}
    .lp-cta-sub{font-size:14px;color:#a8a5c0;margin-bottom:26px;position:relative;}

    div[data-testid="stButton"] button{
        background:linear-gradient(135deg,#6c63ff,#8b5cf6)!important;color:#fff!important;border:none!important;
        border-radius:11px!important;font-family:'JetBrains Mono',monospace!important;font-size:12.5px!important;
        letter-spacing:.08em!important;text-transform:uppercase!important;padding:14px 20px!important;
        box-shadow:0 12px 28px -10px rgba(108,99,255,.65)!important;transition:all .25s!important;
    }
    div[data-testid="stButton"] button:hover{transform:translateY(-2px)!important;box-shadow:0 16px 34px -8px rgba(108,99,255,.85)!important;}
    </style>
    """, unsafe_allow_html=True)


def _hero() -> None:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown("""
        <div class="lp-eyebrow"><span class="dot"></span> LIVE MODEL &middot; AUC-ROC 0.835</div>
        <div class="lp-h1">Know who's<br>about to <span>churn</span><br>before they do.</div>
        <div class="lp-sub">ChurnGuard Pro scores every customer in real time, explains exactly
        why they're at risk, and quantifies the revenue you can protect by acting on it —
        all in one dashboard your whole team can use.</div>
        """, unsafe_allow_html=True)

        b1, b2, _ = st.columns([1, 1, 1.4])
        with b1:
            if st.button("Get Started →", key="lp_get_started", use_container_width=True):
                st.session_state.site_entered = True
                st.rerun()
        with b2:
            st.link_button("View on GitHub", "https://github.com/saumyadwiv/churnguard", use_container_width=True)

        st.markdown("""
        <div class="lp-stats">
            <div><div class="lp-stat-val">83.5%</div><div class="lp-stat-lbl">AUC-ROC</div></div>
            <div><div class="lp-stat-val">7,043</div><div class="lp-stat-lbl">Customers trained on</div></div>
            <div><div class="lp-stat-val">$410K+</div><div class="lp-stat-lbl">Net benefit / cohort</div></div>
            <div><div class="lp-stat-val">5,611%</div><div class="lp-stat-lbl">Campaign ROI</div></div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="lp-scene">
          <div class="lp-card3d">
            <div class="lp-float-chip">
                <div style="font-family:'JetBrains Mono',monospace;font-size:8.5px;color:#6b6888;text-transform:uppercase;letter-spacing:.1em;">Risk alert</div>
                <div style="font-size:12.5px;color:#f2f1fb;font-weight:500;margin-top:4px;">CUST-2291 · <span style="color:#ef4444;">87% churn risk</span></div>
            </div>
            <div class="lp-card3d-head">
                <div class="lp-dots"><span style="background:#ef4444;"></span><span style="background:#f59e0b;"></span><span style="background:#22c55e;"></span></div>
                <div class="lp-card3d-title">churnguard · live dashboard</div>
            </div>
            <div class="lp-gauge-wrap">
                <div class="lp-mini-kpi"><div class="lp-mini-val" style="color:#ef4444;">312</div><div class="lp-mini-lbl">High risk</div></div>
                <div class="lp-mini-kpi"><div class="lp-mini-val" style="color:#f59e0b;">540</div><div class="lp-mini-lbl">Medium risk</div></div>
                <div class="lp-mini-kpi"><div class="lp-mini-val" style="color:#22c55e;">6,191</div><div class="lp-mini-lbl">Stable</div></div>
            </div>
            <div class="lp-bars">
                <div class="b" style="height:35%;"></div>
                <div class="b" style="height:55%;"></div>
                <div class="b" style="height:40%;"></div>
                <div class="b" style="height:78%;"></div>
                <div class="b" style="height:60%;"></div>
                <div class="b" style="height:92%;"></div>
                <div class="b" style="height:70%;"></div>
                <div class="b" style="height:48%;"></div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


def _features() -> None:
    st.markdown('<div style="margin-top:90px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lp-section-lbl">What\'s inside</div>', unsafe_allow_html=True)
    st.markdown('<div class="lp-section-title">Six modules, one retention workflow</div>', unsafe_allow_html=True)
    st.markdown('<div class="lp-section-sub">From a single lookup to a boardroom-ready ROI number — everything is built on the same Random Forest model, so the story stays consistent end to end.</div>', unsafe_allow_html=True)

    feats = [
        ("🎯", "#6c63ff", "Single Predict", "Score one customer instantly and get a plain-English retention recommendation."),
        ("📊", "#8b5cf6", "Bulk Predict", "Upload a CSV of thousands of customers and get a ranked, exportable at-risk list in seconds."),
        ("📈", "#22c55e", "Analytics Dashboard", "Portfolio-level churn patterns by contract, tenure and service — spot the segments that matter."),
        ("🕓", "#f59e0b", "My History", "Every prediction is saved per-user in MongoDB, so you can track outcomes over time."),
        ("🔍", "#ef4444", "Explainability", "SHAP-powered breakdowns show exactly which factors are driving each prediction."),
        ("💰", "#22c55e", "ROI Calculator", "Turn a batch of predictions into a dollar figure — cost, revenue protected, and ROI %."),
    ]
    cols = st.columns(3, gap="medium")
    for i, (icon, color, title, body) in enumerate(feats):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="lp-feat">
                <div class="lp-feat-icon" style="background:{color}22;border:1px solid {color}55;">{icon}</div>
                <div class="lp-feat-title">{title}</div>
                <div class="lp-feat-body">{body}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)


def _cta() -> None:
    st.markdown('<div class="lp-cta">', unsafe_allow_html=True)
    st.markdown('<div class="lp-cta-title">Ready to see your own churn risk?</div>', unsafe_allow_html=True)
    st.markdown('<div class="lp-cta-sub">Create a free account — no credit card, model runs instantly.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 0.8, 1.2])
    with c2:
        if st.button("Get Started →", key="lp_get_started_bottom", use_container_width=True):
            st.session_state.site_entered = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def show_landing_page() -> None:
    st.set_page_config(
        page_title="ChurnGuard Pro — Predict customer churn before it happens",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    st.markdown("""
    <div class="lp-nav">
        <div class="lp-logo"><div class="lp-logo-badge">🛡️</div> ChurnGuard Pro</div>
        <div class="lp-nav-links">PREDICT &nbsp;·&nbsp; ANALYTICS &nbsp;·&nbsp; EXPLAIN &nbsp;·&nbsp; ROI</div>
    </div>
    """, unsafe_allow_html=True)

    _hero()
    _features()
    _cta()

    st.markdown(
        '<div style="text-align:center;font-family:JetBrains Mono,monospace;font-size:10px;'
        'color:#3d3f5a;padding:40px 0 10px;">ChurnGuard Pro · Random Forest · AUC-ROC 0.835 · '
        'Built on the IBM Telco Customer Churn dataset</div>',
        unsafe_allow_html=True,
    )
