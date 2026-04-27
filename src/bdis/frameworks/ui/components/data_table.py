import streamlit as st
import pandas as pd

def render_data_table(data):
    """
    Focused Asset Ledger: Optimized for high-speed verification.
    """
    if not data:
        return

    df_data = []
    for d in data:
        df_data.append({
            "Status": d.status,
            "Legal entity": d.company_name or "Unknown",
            "Valuation (USD)": float(d.amount_usd),
            "Confidence": float(d.confidence * 100),
            "Risk": "High" if d.is_high_risk else "Standard",
            "Asset ID": d.document_id,
            "Created": d.created_at
        })
    
    df = pd.DataFrame(df_data)

    # 1. Search (Stripe Style)
    search_query = st.text_input("Filter assets", placeholder="Search by company, ID, or risk level...", label_visibility="collapsed")
    
    if search_query:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        df = df[mask]

    # 2. Document Grid
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Confidence": st.column_config.ProgressColumn(
                "Trust score",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Valuation (USD)": st.column_config.NumberColumn("Valuation (USD)", format="$%.2f"),
            "Status": st.column_config.TextColumn("Status"),
            "Legal entity": st.column_config.TextColumn("Legal entity"),
            "Asset ID": st.column_config.TextColumn("Internal ID"),
        }
    )

    # 3. Enhanced Inspection Pane (Proving Data Grounding)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Inspection and verification")
    
    selected_id = st.selectbox("Select asset for deep-dive verification", df["Asset ID"].tolist() if not df.empty else ["None"])
    
    if selected_id != "None":
        asset = next(d for d in data if d.document_id == selected_id)
        
        # Performance Insight directly in context
        confidence_pct = asset.confidence * 100
        st.markdown(f"**System trust score for this asset:** `{confidence_pct:.2f}%`")
        
        col_raw, col_mapped = st.columns(2)
        
        with col_raw:
            st.markdown("**Raw extraction source**")
            st.code(asset.raw_text if asset.raw_text else "Raw text content unavailable.", language="text")
            st.caption("The exact OCR/Text payload processed by the AI.")
            
        with col_mapped:
            st.markdown("**Structured registry data**")
            st.json({
                "company_name": asset.company_name,
                "amount_usd": asset.amount_usd,
                "currency": asset.currency,
                "confidence": asset.confidence,
                "risk_flag": asset.is_high_risk
            })
            st.write(f"**Storage path:** `{asset.s3_uri}`")
            st.write(f"**Internal trace ID:** `{asset.trace_id}`")
            st.write(f"**Exposure level:** {'HIGH' if asset.is_high_risk else 'NOMINAL'}")
