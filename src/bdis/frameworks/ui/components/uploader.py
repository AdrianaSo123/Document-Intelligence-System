import time
import streamlit as st

def render_uploader(client):
    st.markdown("### Secure Document Upload")
    uploaded_file = st.file_uploader("Drag and drop PDF invoices", type=["pdf"])
    
    if uploaded_file and st.button("Process Document"):
        with st.spinner("Uploading to BDIS Engine..."):
            job_id = client.upload_file(uploaded_file.getvalue(), uploaded_file.name)
        
        if job_id:
            status = "processing"
            status_box = st.empty()
            
            while status == "processing":
                with status_box:
                    st.info("🔄 Celery Worker Extracting Insights...")
                time.sleep(1.5)
                status = client.get_status(job_id)
            
            status_box.success("✅ Extraction Complete!")
            st.cache_data.clear() # Force data refresh
        else:
            st.error("Upload failed. File might not be a valid PDF.")
