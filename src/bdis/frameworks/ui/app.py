import logging
from pathlib import Path
import streamlit as st

from bdis.frameworks.ui.api_client import BdisApiClient
from bdis.frameworks.ui.view_models import ErrorViewModel
from bdis.frameworks.ui.components.uploader import render_uploader
from bdis.frameworks.ui.components.metrics import render_metrics
from bdis.frameworks.ui.components.data_table import render_data_table

logging.basicConfig(level=logging.INFO)

# CSS Injector Component
def inject_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="BDIS Intelligence", layout="wide", page_icon="⚡")
inject_css()

client = BdisApiClient()

# Sprint 7: Network Memoization Bound
@st.cache_data(ttl=15, show_spinner=False)
def get_dashboard_data():
    return client.fetch_all_documents()

def render_error_state(msg: str):
    st.error(f"SERVICE CRITICAL: {msg}")
    st.info("System is offline. The engineering team has been notified.")

def render_dashboard():
    # Sprint 6: Establish Command Rail
    with st.sidebar:
        st.title("⚡ BDIS Engine")
        st.caption("Operations Control Center")
        st.divider()
        render_uploader(client)
    
    # Executive Main Stage
    st.title("Enterprise Risk Index")
    
    data = get_dashboard_data()
    
    # Sprint 7: Intercept Service Drops gracefully
    if isinstance(data, ErrorViewModel):
        render_error_state(data.error_message)
        return
        
    if not data:
        st.info("Data lake is completely empty. Awaiting document ingestion via Command Rail.")
        return
        
    render_metrics(data)
    
    st.markdown("### Ledger Analytics")
    render_data_table(data)

if __name__ == "__main__":
    render_dashboard()
