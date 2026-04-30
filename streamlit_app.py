import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Multi-Alert Intelligence System", layout="wide")
st.title("📊 ENHANCED DIAGNOSIS & COMPARISON SYSTEM")

try:
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # --- STATISTICAL CALCULATIONS (Rolling Z-Score) ---
    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)

    # --- SIDEBAR: MULTI-PUMP COMPARISON ---
    st.sidebar.header("🕹️ Global Control")
    all_pumps = df['site'].unique()
    selected_pumps = st.sidebar.multiselect("Select Pumps to Compare", all_pumps, default=[all_pumps[0]])
    
    # Filter data based on selection
    comp_df = df[df['site'].isin(selected_pumps)].reset_index()

    # --- 1. TIME TRENDS (Vibration, Temp, Current, Pressure, Flow, Efficiency) ---
    st.subheader("📈 Multi-Parameter Time Trends")
    metrics = ['vibration_mm_s', 'temp_c', 'current_a', 'pressure_bar', 'flow_m3h', 'efficiency_pct']
    
    # We use a facet plot to show all metrics at once
    # Melting the dataframe makes it easier for Plotly to facet
    melted_df = comp_df.melt(id_vars=['index', 'site'], value_vars=metrics)
    
    fig_trends = px.line(
        melted_df, x='index', y='value', color='site', 
        facet_row='variable', height=1000,
        labels={'index': 'Time Step', 'value': 'Reading'},
        title="Comparative Trend Analysis"
    )
    fig_trends.update_yaxes(matches=None) # Allow independent scales
    st.plotly_chart(fig_trends, use_container_width=True)

    # --- 2. DEGRADATION HIGHLIGHTING ---
    st.divider()
    st.subheader("⚠️ Degradation Detection Zone")
    
    # Highlight points where health < 75 or Z-Score is high
    comp_df['is_degraded'] = (comp_df['health_score'] < 75) | (comp_df['z_score'].abs() > 2.5)
    
    fig_health = px.scatter(
        comp_df, x='index', y='health_score', color='site',
        size=comp_df['is_degraded'].map({True: 10, False: 3}),
        symbol='is_degraded',
        title="Asset Health: Larger 'X' indicates visible degradation periods"
    )
    st.plotly_chart(fig_health, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
