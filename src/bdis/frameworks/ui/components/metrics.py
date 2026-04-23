import streamlit as st

def render_metrics(data):
    total_docs = len(data)
    total_value = sum(d.amount_usd for d in data)
    high_risk_count = sum(1 for d in data if d.is_high_risk)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents Processed", total_docs)
    with col2:
        st.metric("Total Revenue Parsed", f"${total_value:,.2f}")
    with col3:
        st.metric("High Risk Anomalies", high_risk_count, delta_color="inverse")
