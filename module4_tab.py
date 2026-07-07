"""
MODULE 4 — Customer History & Retention Tracking
Paste this into your Phase 2 app.py.

Instructions:
1. Add the import block at the top of app.py
2. Add the "Save to history" checkbox to Tab 1 (Module 01)
3. Add a new tab for Module 4
"""


# ══════════════════════════════════════════════════════════════════
# PASTE THESE IMPORTS AT THE TOP OF app.py (after existing imports)
# ══════════════════════════════════════════════════════════════════

# from mongo import (
#     save_prediction,
#     record_outcome,
#     get_predictions_as_df,
#     get_customer_history,
#     get_retention_effectiveness,
#     get_dashboard_kpis,
#     test_connection,
#     RETENTION_ACTIONS,
#     customer_exists,
# )


# ══════════════════════════════════════════════════════════════════
# PASTE THIS BLOCK IN TAB 1 (Module 01) — after the prediction runs
# Add a checkbox input in col_c alongside other inputs:
#   save_to_history = st.checkbox("Save to customer history", value=True)
# Then after predict() runs, add this save block:
# ══════════════════════════════════════════════════════════════════

# if save_to_history:
#     save_prediction(
#         customer_id  = final_id,
#         churn_prob   = proba,
#         risk_level   = label,
#         will_churn   = bool(pred),
#         threshold    = THRESHOLD,
#         input_data   = {
#             "tenure"          : tenure,
#             "monthly_charges" : monthly,
#             "contract"        : contract,
#             "internet"        : internet,
#             "tech_support"    : tech,
#             "senior_citizen"  : senior,
#             "partner"         : partner,
#         }
#     )
#     st.success(f"Saved prediction for **{final_id}** to history.")


# ══════════════════════════════════════════════════════════════════
# ADD A NEW TAB IN YOUR tabs = st.tabs([...]) LINE:
#   "04 · History",
# Then add this entire block as the new tab's content:
# ══════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def render_module4():
    """
    Complete Module 4 — paste the contents of this function
    inside your new t4 tab block like:

        with t4:
            render_module4()
    """

    st.markdown('<div class="sec-pill">Module 04 — New</div>',
                unsafe_allow_html=True)
    st.markdown("### Customer History & Retention Tracking")

    # ── Connection check ───────────────────────────────────────────
    from mongo import (
        test_connection, get_dashboard_kpis, get_predictions_as_df,
        record_outcome, get_retention_effectiveness, get_customer_history,
        RETENTION_ACTIONS, customer_exists,
    )

    if not test_connection():
        st.error("""
        Cannot connect to MongoDB.
        Check your MONGO_URI in the .env file and make sure your
        cluster is running on MongoDB Atlas.
        """)
        st.code("MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/churnguard")
        return

    # ── Three sub-tabs ─────────────────────────────────────────────
    sub1, sub2, sub3 = st.tabs([
        "All Customers",
        "Record Outcome",
        "Retention Effectiveness",
    ])


    # ══════════════════════════════════════════════════════════════
    # SUB-TAB 1 — All customers with their latest prediction
    # ══════════════════════════════════════════════════════════════
    with sub1:

        # KPI cards
        kpis = get_dashboard_kpis()

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-val" style="color:#e7ecf2;">{kpis["total_tracked"]}</div>'
            f'<div class="kpi-lbl">Total tracked</div>'
            f'</div>', unsafe_allow_html=True)
        k2.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-val" style="color:#ef4444;">{kpis["at_risk"]}</div>'
            f'<div class="kpi-lbl">At risk</div>'
            f'</div>', unsafe_allow_html=True)
        k3.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-val" style="color:#22c55e;">{kpis["retained"]}</div>'
            f'<div class="kpi-lbl">Retained</div>'
            f'</div>', unsafe_allow_html=True)
        k4.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-val" style="color:#ef4444;">{kpis["churned"]}</div>'
            f'<div class="kpi-lbl">Churned</div>'
            f'</div>', unsafe_allow_html=True)
        k5.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-val" style="color:#22d3ee;">{kpis["retention_rate"]:.0f}%</div>'
            f'<div class="kpi-lbl">Retention rate</div>'
            f'</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-lbl" style="margin-top:20px;">All predictions</div>',
                    unsafe_allow_html=True)

        df = get_predictions_as_df()

        if df.empty:
            st.info(
                "No predictions saved yet. "
                "Go to the Predict tab, tick "
                "**Save to customer history**, and run a prediction."
            )
        else:
            # Filters
            fc1, fc2, fc3 = st.columns(3)
            risk_filter = fc1.multiselect(
                "Risk level",
                ["High", "Medium", "Low"],
                default=["High", "Medium", "Low"],
                key="m4_risk"
            )
            outcome_filter = fc2.multiselect(
                "Outcome",
                ["—", "retained", "churned", "pending", "no_action"],
                default=["—", "retained", "churned", "pending", "no_action"],
                key="m4_outcome"
            )
            search = fc3.text_input(
                "Search customer ID", "", key="m4_search"
            )

            # Apply filters
            filtered = df.copy()
            if risk_filter:
                filtered = filtered[filtered["Risk Level"].isin(risk_filter)]
            if outcome_filter:
                filtered = filtered[filtered["Outcome"].isin(outcome_filter)]
            if search.strip():
                filtered = filtered[
                    filtered["Customer ID"].str.contains(
                        search.strip(), case=False, na=False
                    )
                ]

            st.caption(f"Showing {len(filtered)} of {len(df)} records")

            # Colour rows by risk and outcome
            def style_risk(v):
                if v == "High":   return "color:#ef4444;font-weight:600"
                if v == "Medium": return "color:#f59e0b;font-weight:600"
                if v == "Low":    return "color:#22c55e"
                return ""

            def style_outcome(v):
                if v == "retained":  return "color:#22c55e;font-weight:600"
                if v == "churned":   return "color:#ef4444;font-weight:600"
                if v == "pending":   return "color:#f59e0b"
                if v == "no_action": return "color:#8b98a9"
                return "color:#67768a"

            st.dataframe(
                filtered.style
                    .applymap(style_risk,    subset=["Risk Level"])
                    .applymap(style_outcome, subset=["Outcome"])
                    .format({"Churn Prob (%)": "{:.1f}%"}),
                use_container_width=True,
                height=420,
            )

            # Export
            st.download_button(
                "Export to CSV",
                data=filtered.to_csv(index=False),
                file_name="customer_history.csv",
                mime="text/csv",
            )

            # Customer deep-dive
            st.markdown(
                '<div class="sec-lbl" style="margin-top:20px;">Customer deep-dive</div>',
                unsafe_allow_html=True
            )
            cid_input = st.text_input(
                "Enter a Customer ID to see their full history",
                placeholder="e.g. CUST-001",
                key="m4_deepdive"
            )
            if cid_input.strip():
                history = get_customer_history(cid_input.strip())
                if history:
                    st.success(f"Found {len(history)} prediction(s) for **{cid_input}**")
                    for i, record in enumerate(history):
                        prob   = record.get("churn_prob", 0)
                        risk   = record.get("risk_level", "")
                        outcome = record.get("outcome") or "No outcome recorded"
                        action  = record.get("action_taken") or "—"
                        at      = record.get("predicted_at", "")
                        rc      = "#ef4444" if risk=="High" else "#f59e0b" if risk=="Medium" else "#22c55e"
                        oc      = "#22c55e" if outcome=="retained" else "#ef4444" if outcome=="churned" else "#f59e0b"
                        st.markdown(f"""
                        <div style="background:#10141d;border:1px solid #1d2530;
                                    border-left:4px solid {rc};border-radius:10px;
                                    padding:16px;margin:8px 0;">
                          <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                              <div style="font-family:JetBrains Mono,monospace;
                                          font-size:11px;color:#67768a;">
                                Prediction #{i+1} · {str(at)[:16]}
                              </div>
                              <div style="font-size:20px;font-weight:700;
                                          color:{rc};margin:4px 0;">
                                {prob*100:.1f}% churn probability
                              </div>
                            </div>
                            <div style="text-align:right;">
                              <div style="font-family:JetBrains Mono,monospace;
                                          font-size:11px;color:{oc};">
                                {outcome.upper()}
                              </div>
                              <div style="font-size:11px;color:#67768a;margin-top:4px;">
                                {action}
                              </div>
                            </div>
                          </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.warning(f"No records found for **{cid_input}**")


    # ══════════════════════════════════════════════════════════════
    # SUB-TAB 2 — Record outcome after team contacts customer
    # ══════════════════════════════════════════════════════════════
    with sub2:
        st.markdown("### Record what happened after you contacted a customer")
        st.markdown(
            '<div class="info-banner">'
            'After your retention team contacts a flagged customer, '
            'record the outcome here. '
            'This data powers the effectiveness analysis in the next tab.'
            '</div>',
            unsafe_allow_html=True
        )

        oc1, oc2 = st.columns(2)

        with oc1:
            o_cid = st.text_input(
                "Customer ID",
                placeholder="e.g. CUST-001",
                key="o_cid"
            )

            # Show warning if customer not found in DB
            if o_cid.strip() and not customer_exists(o_cid.strip()):
                st.warning(
                    f"No prediction found for **{o_cid.strip()}**. "
                    "Make sure you saved the prediction first."
                )

            o_outcome = st.selectbox(
                "Outcome",
                ["retained", "churned", "pending", "no_action"],
                format_func=lambda x: {
                    "retained" : "Retained — customer agreed to stay",
                    "churned"  : "Churned — customer left anyway",
                    "pending"  : "Pending — still in contact",
                    "no_action": "No action taken",
                }[x],
                key="o_outcome"
            )

            o_action = st.selectbox(
                "Retention action taken",
                RETENTION_ACTIONS,
                key="o_action"
            )

        with oc2:
            o_agent = st.text_input(
                "Agent / team member name",
                placeholder="e.g. Priya Sharma",
                key="o_agent"
            )
            o_notes = st.text_area(
                "Notes",
                placeholder="Any extra context about this interaction...\ne.g. Customer was unhappy with fiber speed. Offered DSL downgrade.",
                height=140,
                key="o_notes"
            )

        if st.button("Save Outcome →", key="save_outcome_btn"):
            if not o_cid.strip():
                st.error("Please enter a Customer ID.")
            else:
                success = record_outcome(
                    customer_id  = o_cid.strip(),
                    outcome      = o_outcome,
                    action_taken = o_action,
                    agent_name   = o_agent,
                    notes        = o_notes,
                )
                if success:
                    outcome_labels = {
                        "retained" : "RETAINED",
                        "churned"  : "CHURNED",
                        "pending"  : "PENDING",
                        "no_action": "NO ACTION",
                    }
                    oc = "#22c55e" if o_outcome=="retained" else "#ef4444" if o_outcome=="churned" else "#f59e0b"
                    st.markdown(f"""
                    <div style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.3);
                                border-radius:10px;padding:16px;margin-top:12px;">
                      <div style="font-family:JetBrains Mono,monospace;font-size:10px;
                                  text-transform:uppercase;letter-spacing:.12em;color:#22c55e;
                                  margin-bottom:4px;">Outcome saved</div>
                      <div style="font-size:14px;color:#e7ecf2;">
                        Customer <b>{o_cid.strip()}</b> marked as
                        <span style="color:{oc};font-weight:600;">
                          {outcome_labels[o_outcome]}
                        </span>
                      </div>
                      <div style="font-size:12px;color:#8b98a9;margin-top:6px;">
                        Action: {o_action} · Agent: {o_agent or "not specified"}
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.warning(
                        f"Could not update prediction for **{o_cid.strip()}**. "
                        "Make sure a prediction was saved for this customer first."
                    )


    # ══════════════════════════════════════════════════════════════
    # SUB-TAB 3 — Retention effectiveness analysis
    # ══════════════════════════════════════════════════════════════
    with sub3:
        st.markdown("### Which retention actions work best?")
        st.markdown(
            '<div class="info-banner">'
            'Based on all recorded outcomes. '
            'Actions with the highest success rate should be your team\'s '
            'default strategy. This table grows smarter as more outcomes '
            'are recorded.'
            '</div>',
            unsafe_allow_html=True
        )

        stats = get_retention_effectiveness()

        if not stats:
            st.info(
                "No effectiveness data yet. "
                "Record outcomes in the **Record Outcome** tab — "
                "once you have at least 2-3 outcomes with different actions, "
                "the analysis will appear here."
            )
        else:
            # Best action highlight
            best = stats[0]
            st.markdown(f"""
            <div style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);
                        border-radius:12px;padding:20px;margin-bottom:20px;
                        display:flex;align-items:center;gap:20px;">
              <div>
                <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                            text-transform:uppercase;letter-spacing:.12em;
                            color:#22c55e;margin-bottom:4px;">Best performing action</div>
                <div style="font-size:18px;color:#e7ecf2;font-weight:500;">
                  {best.get("action","—")}
                </div>
              </div>
              <div style="margin-left:auto;text-align:right;">
                <div style="font-family:Syne,sans-serif;font-size:36px;
                            font-weight:700;color:#22c55e;line-height:1;">
                  {best.get("success_rate",0):.0f}%
                </div>
                <div style="font-size:11px;color:#67768a;">success rate</div>
              </div>
            </div>""", unsafe_allow_html=True)

            # All actions breakdown
            st.markdown(
                '<div class="sec-lbl">All actions breakdown</div>',
                unsafe_allow_html=True
            )

            for s in stats:
                rate    = s.get("success_rate", 0)
                total   = s.get("total", 0)
                ret     = s.get("retained", 0)
                churn   = s.get("churned", 0)
                action  = s.get("action", "—")
                bar_w   = int(rate)
                color   = "#22c55e" if rate >= 65 else "#f59e0b" if rate >= 35 else "#ef4444"

                st.markdown(f"""
                <div style="background:#10141d;border:1px solid #1d2530;
                            border-radius:10px;padding:16px 18px;margin:8px 0;">
                  <div style="display:flex;justify-content:space-between;
                              align-items:center;margin-bottom:8px;">
                    <div style="font-size:13px;color:#e7ecf2;font-weight:500;
                                flex:1;margin-right:16px;">{action}</div>
                    <div style="font-family:JetBrains Mono,monospace;
                                font-size:18px;font-weight:500;
                                color:{color};">{rate:.0f}%</div>
                  </div>
                  <div style="height:6px;background:#1d2530;
                              border-radius:3px;overflow:hidden;margin-bottom:10px;">
                    <div style="height:100%;width:{bar_w}%;
                                background:{color};border-radius:3px;"></div>
                  </div>
                  <div style="display:flex;gap:20px;font-size:11px;color:#67768a;">
                    <span style="color:#22c55e;">{ret} retained</span>
                    <span style="color:#ef4444;">{churn} churned</span>
                    <span>{total} total contacted</span>
                  </div>
                </div>""", unsafe_allow_html=True)

            # Bar chart
            if len(stats) >= 2:
                st.markdown(
                    '<div class="sec-lbl" style="margin-top:20px;">Visual comparison</div>',
                    unsafe_allow_html=True
                )
                actions = [s.get("action","")[:30]+"..." if len(s.get("action",""))>30
                           else s.get("action","") for s in stats]
                rates   = [s.get("success_rate", 0) for s in stats]
                colors  = ["#22c55e" if r>=65 else "#f59e0b" if r>=35 else "#ef4444"
                           for r in rates]

                fig, ax = plt.subplots(figsize=(10, max(3, len(stats)*0.8)))
                fig.patch.set_facecolor('#10141d')
                ax.set_facecolor('#10141d')
                bars = ax.barh(actions, rates, color=colors, height=0.55,
                               edgecolor='#080a0f')
                ax.axvline(x=50, color='#67768a', linestyle='--',
                           lw=1, alpha=0.5, label='50% baseline')
                ax.set_xlabel('Success rate (%)', color='#8b98a9', fontsize=9)
                ax.set_title('Retention action success rates',
                             color='#e7ecf2', fontsize=11, pad=10)
                ax.tick_params(colors='#8b98a9', labelsize=8)
                ax.set_xlim(0, 100)
                for sp in ax.spines.values(): sp.set_color('#1d2530')
                for bar, rate in zip(bars, rates):
                    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                            f'{rate:.0f}%', va='center', fontsize=9, color='#8b98a9')
                p1 = mpatches.Patch(color='#22c55e', label='High (≥65%)')
                p2 = mpatches.Patch(color='#f59e0b', label='Medium (35-65%)')
                p3 = mpatches.Patch(color='#ef4444', label='Low (<35%)')
                ax.legend(handles=[p1,p2,p3], facecolor='#10141d',
                          edgecolor='#1d2530', labelcolor='#8b98a9', fontsize=8,
                          loc='lower right')
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # Export stats table
            if stats:
                stats_df = pd.DataFrame([{
                    "Action"        : s.get("action",""),
                    "Total"         : s.get("total",0),
                    "Retained"      : s.get("retained",0),
                    "Churned"       : s.get("churned",0),
                    "Success Rate %": s.get("success_rate",0),
                } for s in stats])
                st.download_button(
                    "Export effectiveness report",
                    data=stats_df.to_csv(index=False),
                    file_name="retention_effectiveness.csv",
                    mime="text/csv",                )