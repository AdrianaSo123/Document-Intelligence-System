import logging
from pathlib import Path
import streamlit as st

from bdis.frameworks.ui.api_client import BdisApiClient
from bdis.frameworks.ui.view_models import ErrorViewModel
from bdis.frameworks.ui.components.uploader import render_uploader
from bdis.frameworks.ui.components.metrics import render_metrics
from bdis.frameworks.ui.components.data_table import render_data_table

logging.basicConfig(level=logging.INFO)

def inject_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="BDIS Intelligence Console", layout="wide")
inject_css()

if "bdis_workspace_id" not in st.session_state:
    st.session_state["bdis_workspace_id"] = None

client = BdisApiClient(workspace_id=st.session_state["bdis_workspace_id"])

@st.cache_data(ttl=15, show_spinner=False)
def get_dashboard_data():
    return client.fetch_all_documents()

def render_dashboard():
    # 1. Sidebar Command Panel (Stripe Style)
    with st.sidebar:
        st.markdown("""
            <div style="padding: 10px 0; margin-bottom: 24px;">
                <h1 style="font-size: 1.5rem; color: #635BFF; margin: 0; font-weight: 700;">BDIS</h1>
                <p style="font-size: 0.85rem; color: #4F566B; margin: 4px 0 0 0; font-weight: 500;">Intelligence & Logistics</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("Workspace")

        workspaces = client.list_workspaces()
        workspace_ids = [w.get("workspace_id") for w in workspaces if w.get("workspace_id")]
        if workspace_ids:
            current = st.session_state["bdis_workspace_id"] or workspace_ids[0]
            selected = st.selectbox("Workspace", workspace_ids, index=workspace_ids.index(current) if current in workspace_ids else 0)
            st.session_state["bdis_workspace_id"] = selected
            client.set_workspace(selected)
        else:
            st.caption("No workspaces found. Run `scripts/bootstrap_dev_workspace.py` and enable `BDIS_AUTH_MODE=dev_headers`.")

        st.divider()
        st.subheader("Data Ingestion")
        # Role-aware UI: auditors are read-only.
        if client.role == "AUDITOR":
            st.info("Read-only access (AUDITOR). Upload disabled.")
        else:
            render_uploader(client)

        # Owner admin panel (minimal)
        if client.role == "OWNER":
            st.divider()
            st.subheader("Workspace Admin")
            members = client.list_members()
            if members:
                st.caption("Members")
                st.json(members)
            else:
                st.caption("No members (or insufficient permissions).")

            with st.expander("Add member"):
                new_user_id = st.text_input("User ID", key="new_member_user_id")
                new_email = st.text_input("Email (optional)", key="new_member_email")
                new_role = st.selectbox("Role", ["ANALYST", "AUDITOR", "OWNER"], index=0, key="new_member_role")
                if st.button("Add/Update member"):
                    ok = client.add_member(new_user_id, role=new_role, email=new_email or None)
                    if ok:
                        st.success("Member updated.")
                    else:
                        st.error("Failed to update member.")
        
        st.divider()
        st.subheader("Asset Filters")
        
        filter_status = st.multiselect(
            "Status",
            ["VALIDATED", "REVIEW_REQUIRED", "FAILED", "PENDING"],
            default=["VALIDATED", "REVIEW_REQUIRED", "FAILED", "PENDING"]
        )
        
        filter_risk = st.radio("Risk level", ["All assets", "High risk only", "Standard assets"], index=0)
        
        st.divider()
        audit_mode = st.toggle("Enable audit mode", value=False)
        
        st.sidebar.markdown("<br>"*5, unsafe_allow_html=True)
        st.sidebar.caption("v1.8.0 • Focused Edition")

    # 2. Executive Header (Minimalist)
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
            <div>
                <h1 style="margin: 0;">Analytics Dashboard</h1>
                <p style="margin: 4px 0 0 0; color: #4F566B; font-size: 1.1rem;">
                    Unified view of enterprise document intelligence and financial grounding.
                </p>
            </div>
            <div style="background: #E3FBE3; padding: 6px 16px; border-radius: 16px; border: 1px solid #0E6245;">
                <span style="color: #0E6245; font-weight: 600; font-size: 0.75rem;">System operational</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    data = get_dashboard_data()
    
    if isinstance(data, ErrorViewModel):
        st.error(f"Service Error: {data.error_message}")
        return
        
    if not data:
        st.info("The asset registry is empty. Please upload a document to initiate the processing protocol.")
        return

    # Filter Logic
    filtered_data = [d for d in data if d.status in filter_status]
    if filter_risk == "High risk only":
        filtered_data = [d for d in filtered_data if d.is_high_risk]
    elif filter_risk == "Standard assets":
        filtered_data = [d for d in filtered_data if not d.is_high_risk]

    # 3. Main Stage (Ledger-First)
    render_metrics(filtered_data)

    # Jobs ledger (Phase 6C2)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Jobs ledger")
    jobs = client.list_jobs()
    st.dataframe(jobs, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Document registry ledger")
    render_data_table(filtered_data)

    if audit_mode:
        st.divider()
        st.markdown("### Developer Audit (JSON View)")
        st.json([d.model_dump() for d in filtered_data])

if __name__ == "__main__":
    render_dashboard()
