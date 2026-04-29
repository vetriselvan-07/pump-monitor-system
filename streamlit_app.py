import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Pump AI Monitor", layout="wide")

# --- GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False):
    if is_health:
        steps = [{'range': [0, 50], 'color': "#ff4b4b"}, {'range': [50, 80], 'color': "#ffa500"}, {'range': [80, 100], 'color': "#00cc96"}]
    else:
        steps = [{'range': [0, max_val], 'color': "#f0f2f6"}]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(value, 2),
        title={'text': title, 'font': {'size': 18}},
        gauge={'axis': {'range': [0, max_val]}, 'bar': {'color': "#31333F"}, 'steps': steps}
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# --- TABLE STYLING ---
def style_incidents(row):
    styles = [''] * len(row)
    if row['vibration_mm_s'] > 4.5: styles[row.index.get_loc('vibration_mm_s')] = 'background-color: black; color: white'
    if row['temp_c'] > 70: styles[row.index.get_loc('temp_c')] = 'background-color: red; color: white'
    if row['efficiency_pct'] < 70: styles[row.index.get_loc('efficiency_pct')] = 'background-color: yellow; color: black'
    # Use .get() to avoid crash if column is missing
    if row.get('is_anomaly', False): 
        styles[row.index.get_loc('Anomaly_Score')] = 'background-color: #FF69B4; color: white' 
    return styles

st.title("🛡️ Advanced AI Pump Monitoring")

try:
    # 1. Load Data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # --- GLOBAL ANOMALY CALCULATION (Run this before filtering) ---
    window = 10 
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window, min_periods=1).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window, min_periods=1).std())
    
    # Calculate Z-Score safely (avoid division by zero)
    df['Anomaly_Score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['Anomaly_Score'] = df['Anomaly_Score'].fillna(0) # Replace NaNs with 0
    df['is_anomaly'] = df['Anomaly_Score'].abs() > 3 

    # 2. Sidebar Filter
    unique_sites = df['site'].unique()
    selected_site = st.sidebar.selectbox("Select Plant", unique_sites)
    site_data = df[df['site'] == selected_site]
    latest = site_data.iloc[-1]

    # 3. Gauges
    c1, c2, c3 = st.columns(3)
    with c1: st.plotly_chart(create_gauge(latest['health_score'], "Health %", is_health=True), use_container_width=True)
    with c2: st.plotly_chart(create_gauge(latest['efficiency_pct'], "Efficiency %"), use_container_width=True)
    with c3: st.plotly_chart(create_gauge(latest['vibration_mm_s'], "Vibration (mm/s)", max_val=10), use_container_width=True)

    st.divider()

    # 4. INCIDENT & ANOMALY REPORT
    st.subheader(f"📋 Intelligent Incident Report: {selected_site}")
    
    # Filter for Threshold fails OR AI Anomaly detection
    # We use .copy() to ensure we aren't working on a slice
    incidents = site_data[
        (site_data['vibration_mm_s'] > 4.5) | (site_data['temp_c'] > 70) | 
        (site_data['efficiency_pct'] < 70) | (site_data['is_anomaly'] == True)
    ].copy()

    if not incidents.empty:
        display_cols = ['timestamp', 'pump_id', 'vibration_mm_s', 'temp_c', 'efficiency_pct', 'Anomaly_Score']
        # Apply style only to existing columns
        styled_df = incidents[display_cols].style.apply(style_incidents, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        st.info("Legend: ⚫ Vibration Fail | 🔴 Overheat | 🟡 Efficiency | 💗 Pink: Statistical Anomaly")
    else:
        st.success("✅ System stable. No threshold breaches or statistical anomalies detected.")

    # 5. Charts
    st.divider()
    st.subheader("Statistical Trends")
    fig = px.line(site_data, x='timestamp', y=['vibration_mm_s', 'rolling_mean'], title="Vibration Anomaly Analysis")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Application Error: {e}")-
