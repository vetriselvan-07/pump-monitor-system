import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Plant Intelligence System", layout="wide")

# --- GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False):
    color = "#00cc96" if not is_health else "green"
    steps = [
        {'range': [0, 50], 'color': "#ff4b4b"}, 
        {'range': [50, 80], 'color': "#ffa500"}, 
        {'range': [80, 100], 'color': "#00cc96"}
    ] if is_health else []
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(value, 2),
        title={'text': title, 'font': {'size': 16}},
        gauge={'axis': {'range': [0, max_val]}, 'bar': {'color': "#31333F"}, 'steps': steps}
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
    return fig

try:
    # 1. LOAD DATA
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # --- 2. WHOLE PLANT OVERVIEW ---
    st.title("🏭 Whole Plant Performance Overview")
    avg_col1, avg_col2, avg_col3 = st.columns(3)
    avg_col1.metric("Global Avg Health", f"{round(df['health_score'].mean(), 1)}%")
    avg_col2.metric("Global Avg Efficiency", f"{round(df['efficiency_pct'].mean(), 1)}%")
    avg_col3.metric("Global Avg Vibration", f"{round(df['vibration_mm_s'].mean(), 2)} mm/s")
    st.divider()

    # --- 3. SIDEBAR: PLANT SELECTION & POP-UPS ---
    selected_site = st.sidebar.selectbox("Select Plant", df['site'].unique())
    site_data = df[df['site'] == selected_site]
    latest = site_data.iloc[-1]

    # Pop-up Alerts for Selected Plant
    if latest['vibration_mm_s'] > 4.5: st.toast(f"🚨 VIBRATION ALERT: {selected_site}", icon="⚠️")
    if latest['temp_c'] > 70: st.toast(f"🔥 OVERHEAT: {selected_site}", icon="🔴")
    if latest['efficiency_pct'] < 70: st.toast(f"📉 EFFICIENCY DROP: {selected_site}", icon="🟡")

    # --- 4. INDEX LOOKUP (ROUND VIEW) ---
    st.header(f"🔍 Record Lookup: {selected_site}")
    max_idx = len(site_data) - 1
    selected_idx = st.number_input(f"Enter Index Number (0 to {max_idx})", min_value=0, max_value=max_idx, value=max_idx)
    
    # Get data for that specific index
    record = site_data.iloc[selected_idx]
    
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1: st.plotly_chart(create_gauge(record['health_score'], "Health %", is_health=True), use_container_width=True)
    with r2: st.plotly_chart(create_gauge(record['efficiency_pct'], "Efficiency %"), use_container_width=True)
    with r3: st.plotly_chart(create_gauge(record['temp_c'], "Temp °C", 100), use_container_width=True)
    with r4: st.plotly_chart(create_gauge(record['pressure_bar'], "Pressure Bar", 10), use_container_width=True)
    with r5: st.plotly_chart(create_gauge(record['vibration_mm_s'], "Vibration mm/s", 10), use_container_width=True)

    # --- 5. DATA LOG & EXPORT ---
    st.divider()
    st.subheader(f"📊 Full Data Log & Export: {selected_site}")
    
    # Display table
    st.dataframe(site_data, use_container_width=True)
    
    # CSV Download Button
    csv = site_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Plant Data as CSV",
        data=csv,
        file_name=f"{selected_site}_data.csv",
        mime='text/csv',
    )

except Exception as e:
    st.error(f"Application Error: {e}")
