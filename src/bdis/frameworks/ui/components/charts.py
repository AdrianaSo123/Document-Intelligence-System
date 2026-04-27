import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

def render_revenue_distribution(data):
    """
    Capital Allocation by Entity (Stripe Style).
    Horizontal bar chart showing grounding in specific companies.
    """
    if not data:
        return
        
    df = pd.DataFrame([d.model_dump() for d in data])
    entity_data = df.groupby("company_name")["amount_usd"].sum().sort_values(ascending=True).reset_index()
    
    fig = px.bar(
        entity_data, 
        x='amount_usd', 
        y='company_name', 
        orientation='h',
        color_discrete_sequence=['#635BFF']
    )
    
    fig.update_layout(
        xaxis_title="Total Valuation (USD)",
        yaxis_title=None,
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=12, color="#4F566B"),
        xaxis=dict(showgrid=True, gridcolor='#E3E8EE'),
        yaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_confidence_distribution(data):
    """
    System Trust Distribution (Stripe Style).
    Histogram showing how confidence varies across the dataset.
    """
    if not data:
        return
        
    df = pd.DataFrame([d.model_dump() for d in data])
    df['Confidence %'] = df['confidence'] * 100
    
    fig = px.histogram(
        df, 
        x='Confidence %',
        nbins=10,
        color_discrete_sequence=['#7A73FF']
    )
    
    fig.update_layout(
        xaxis_title="Confidence Level (%)",
        yaxis_title="Record Count",
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=12, color="#4F566B"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#E3E8EE')
    )
    
    st.plotly_chart(fig, use_container_width=True)
