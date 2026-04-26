import streamlit as st

def render_data_table(data):
    if not data:
        st.info("No records found in the ledger.")
        return

    # Build rows first
    rows_html = ""
    for d in data:
        status_class = "status-pending"
        status_text = d.status.replace("_", " ").title()
        if "validated" in d.status.lower() or "complete" in d.status.lower():
            status_class = "status-valid"
        elif "error" in d.status.lower() or "failed" in d.status.lower():
            status_class = "status-error"
            
        due_date = d.due_date if d.due_date else "—"
        
        # Use a single line per row to avoid markdown line-break confusion
        rows_html += f'<tr><td style="font-weight: 500; color: #1A1F36;">{d.company_name}</td><td>${d.amount_usd:,.2f}</td><td style="color: #697386;">{due_date}</td><td><span class="status-pill {status_class}">{status_text}</span></td></tr>'
    
    # Combine everything into one compact string
    html_string = (
        '<div style="width: 100%; overflow-x: auto;">'
        '<table class="stripe-table">'
        '<thead><tr><th>Customer / Vendor</th><th>Amount (USD)</th><th>Due Date</th><th>Status</th></tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        '</div>'
    )
    
    # Use st.markdown with strict unsafe_allow_html
    st.markdown(html_string, unsafe_allow_html=True)
