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
    # Sprint 6: Establish Command Rail (Sidebar)
    with st.sidebar:
        st.markdown("""
            <div style="padding: 10px 0; margin-bottom: 24px;">
                <h1 style="font-size: 1.4rem; color: #635BFF; margin: 0; font-weight: 700;">BDIS</h1>
                <p style="font-size: 0.8rem; color: #697386; margin: 0; font-weight: 500;">Intelligence Dashboard</p>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        render_uploader(client)
        
        st.sidebar.markdown("<br>"*5, unsafe_allow_html=True)
        st.sidebar.caption("v1.4.0 • Enterprise Edition")
    
    # Executive Main Stage
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px;">
            <div>
                <h1 style="margin: 0; font-size: 1.8rem; color: #1A1F36;">Document Analytics</h1>
                <p style="margin: 4px 0 0 0; color: #697386; font-size: 1rem;">Comprehensive overview of ingested business assets.</p>
            </div>
            <div style="background: #E3E8EE; padding: 6px 12px; border-radius: 6px; display: flex; align-items: center;">
                <span style="color: #0E6245; font-weight: 600; font-size: 0.75rem;">● SYSTEM OPERATIONAL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    data = get_dashboard_data()
    
    # Sprint 7: Intercept Service Drops gracefully
    if isinstance(data, ErrorViewModel):
        render_error_state(data.error_message)
        return
        
    if not data:
        st.info("The data lake is currently empty. Please upload a document to begin.")
        return
        
    render_metrics(data)
    
    st.markdown("<h3 style='margin-top: 48px; margin-bottom: 16px; font-size: 1.1rem; color: #1A1F36;'>Recent Transactions</h3>", unsafe_allow_html=True)
    render_data_table(data)

if __name__ == "__main__":
    render_dashboard()
