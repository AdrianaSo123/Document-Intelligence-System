import streamlit as st

def render_metrics(data):
    """
    Stripe-style Metric Summary: Consistent with dashboard ledger.
    """
    total_docs = len(data)
    from bdis.core.financials import convert_to_usd
    
    total_value_usd = sum(convert_to_usd(d.amount_usd, d.currency) for d in data)
    high_risk_count = sum(1 for d in data if d.is_high_risk)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Processed documents</div>
                <div class="metric-value">{total_docs}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total valuation (USD)</div>
                <div class="metric-value">${total_value_usd:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Anomaly exposure</div>
                <div class="metric-value">{high_risk_count}</div>
            </div>
        """, unsafe_allow_html=True)
