import pandas as pd
import streamlit as st

def render_data_table(data):
    dicts_list = []
    for d in data:
        row = d.model_dump()
        # Clean Architecture: We strictly consume the pre-calculated boolean from the ViewModel. No logic interpolation.
        row["is_high_risk"] = d.is_high_risk 
        row["s3_uri"] = d.s3_uri
        dicts_list.append(row)
        
    df = pd.DataFrame(dicts_list)
    if not df.empty:
        columns_to_show = ["company_name", "amount_usd", "status", "due_date", "is_high_risk", "s3_uri"]
        df = df[columns_to_show]
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "company_name": st.column_config.TextColumn("Vendor"),
                "amount_usd": st.column_config.NumberColumn(
                    "Obligation",
                    format="$ %.2f"
                ),
                "status": st.column_config.TextColumn("State"),
                "due_date": st.column_config.TextColumn("Due Date"),
                "is_high_risk": st.column_config.CheckboxColumn("Fraud Alert"),
                "s3_uri": st.column_config.LinkColumn("S3 Object URI")
            }
        )
