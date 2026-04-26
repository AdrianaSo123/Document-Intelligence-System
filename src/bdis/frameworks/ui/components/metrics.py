import streamlit as st

def render_metrics(data):
    total_docs = len(data)
    total_value = sum(d.amount_usd for d in data)
    high_risk_count = sum(1 for d in data if d.is_high_risk)
    
    col1, col2, col3 = st.columns(3)
    
    metrics = [
        ("Documents Processed", str(total_docs), "📄"),
        ("Total Revenue Parsed", f"${total_value:,.2f}", "💰"),
        ("High Risk Anomalies", str(high_risk_count), "⚠️")
    ]
    
    for col, (label, value, icon) in zip([col1, col2, col3], metrics):
        with col:
            st.markdown(f"""
                <div class="stripe-card">
                    <div style="font-size: 0.8rem; color: #697386; font-weight: 500; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.025em;">
                        {label}
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 600; color: #1A1F36; margin-bottom: 8px;">
                        {value}
                    </div>
                    <div style="font-size: 0.8rem; color: #24B47E; font-weight: 500; display: flex; align-items: center;">
                        <span style="margin-right: 4px;">↑</span> 12.5% <span style="color: #697386; margin-left: 4px; font-weight: 400;">vs last month</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
