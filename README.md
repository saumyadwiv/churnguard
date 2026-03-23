# ChurnGuard — Customer Churn Prediction App

A machine learning web app that predicts telecom customer churn in real time.

## Features
- **Module 1** — Single customer prediction with risk level and retention recommendation
- **Module 2** — Bulk CSV upload with ranked risk list and export
- **Module 5** — Explainability — why did the model predict this?

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