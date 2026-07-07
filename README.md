# ChurnGuard — Customer Churn Prediction App

A machine learning web app that predicts telecom customer churn in real time.

## Features
- **Home page** — public landing page with a "Get Started" button that leads into sign in / create account
- **Module 1** — Single customer prediction with risk level, retention recommendation, and a live gauge
- **Module 2** — Bulk CSV upload with ranked risk list, an interactive 3D risk map, and export
- **Module 3** — Analytics dashboard with a 3D portfolio scatter (tenure × monthly charges × churn %)
- **Module 5** — Explainability — why did the model predict this?
- **Module 6** — ROI calculator with an ROI gauge and a cost/benefit waterfall chart

## Google sign-in
"Continue with Google" needs three secrets set in `.streamlit/secrets.toml`:
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `REDIRECT_URI`. If it's not working,
open the "Google sign-in not working?" expander on the sign-in page — it shows
the exact redirect URI the app is using, which must match an **Authorized
redirect URI** on your OAuth client in the Google Cloud Console exactly
(scheme, host, and no trailing slash). If your OAuth consent screen is in
**Testing** mode, only emails added under **Test users** can sign in.

## Setup

### Files needed in this folder
```
customer-churn-prediction/
├── app.py
├── requirements.txt
├── churn_model_final.pkl
├── feature_names.pkl
└── metrics.json
```

### Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy on Streamlit Cloud (free)
1. Push this folder to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repo
4. Set main file to app.py
5. Done — live URL in 2 minutes

## Model
- Algorithm: Random Forest Classifier
- Dataset: IBM Telco Customer Churn (7,043 customers)
- AUC-ROC: 0.8353
- Threshold: 0.63 (tuned)
- Overfit gap: 0.013