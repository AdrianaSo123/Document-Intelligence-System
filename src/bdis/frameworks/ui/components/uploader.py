import time
import streamlit as st

def render_uploader(client):
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <h3 style="margin: 0; font-size: 1rem; color: #1A1F36; font-weight: 600;">Ingestion Engine</h3>
            <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #697386;">Upload documents for AI extraction</p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file:
        if st.button("Run Extraction"):
            with st.spinner("Processing..."):
                job_id = client.upload_file(uploaded_file.getvalue(), uploaded_file.name)
            
            if job_id:
                status = "processing"
                status_box = st.empty()
                
                while status == "processing":
                    with status_box:
                        st.info("🔄 Processing with BDIS Engine...")
                    time.sleep(1.5)
                    status = client.get_status(job_id)
                
                status_box.success("✅ Document Processed")
                st.cache_data.clear()
            else:
                st.error("Upload failed. Verify document format.")
