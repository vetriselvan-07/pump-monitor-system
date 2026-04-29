import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pump Health Monitor", layout="wide")

st.title("🌊 Industrial Pump Intelligence Dashboard")

try:
    # 1. Load Data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # 2. Get Latest Data
    latest = df.iloc[-1]
    site_name = latest.get('site', 'Unknown Plant')
    pump_id = latest.get('pump_id', 'Unknown Pump')
    
    st.sidebar.header("📍 Current Location")
    st.sidebar.info(f"Monitoring: **{site_name}**")

    # 3. Dynamic Alerts with Plant Info and "Info" Buttons
    st.subheader(f"⚠️ Active Alerts for {site_name}")

    # Vibration Alert
    if latest['vibration_mm_s'] > 4.5:
        st.error(f"🚨 High Vibration at **{site_name}** ({latest['vibration_mm_s']} mm/s)")
        with st.expander(f"ℹ️ View Plant Info for {site_name}"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Vibration Threshold:** 4.5 mm/s")
            st.write(f"**Action:** Check bearing lubrication at {site_name}.")

    # Temperature Alert
    if latest['temp_c'] > 70:
        st.error(f"🔥 Overheat detected at **{site_name}** ({latest['temp_c']}°C)")
        with st.expander(f"ℹ️ View Plant Info for {site_name}"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Current Temp:** {latest['temp_c']}°C (Limit: 70°C)")
            st.write(f"**Location:** {site_name} Main Bay")

    # Pressure Alert
    if latest['pressure_bar'] < 3.0:
        st.warning(f"📉 Low Pressure at **{site_name}** ({latest['pressure_bar']} bar)")
        with st.expander(f"ℹ️ View Plant Info for {site_name}"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Status:** Cavitation Risk likely at {site_name}.")

    # Current/Loading Alert
    if latest['current_a'] > 26:
        st.error(f"⚡ Abnormal Loading at **{site_name}** ({latest['current_a']} A)")
        with st.expander(f"ℹ️ View Plant Info for {site_name}"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Diagnostic:** Motor drawing excess current at {site_name}. Inspect electrical load.")

    # 4. Visual Dashboard (KPIs)
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Plant", site_name)
    m2.metric("Vibration", f"{latest['vibration_mm_s']} mm/s")
    m3.metric("Temp", f"{latest['temp_c']}°C")
    m4.metric("Current", f"{latest['current_a']} A")

    # 5. Health Trend Chart
    st.subheader("Health Score Trend Analysis")
    fig = px.line(df, x=df.index, y='health_score', title=f"Reliability Trend: {site_name}")
    # Zones
    fig.add_hrect(y0=0, y1=50, fillcolor="red", opacity=0.2, annotation_text="Critical")
    fig.add_hrect(y0=50, y1=80, fillcolor="orange", opacity=0.2, annotation_text="Warning")
    fig.add_hrect(y0=80, y1=100, fillcolor="green", opacity=0.2, annotation_text="Optimal")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Data Load Error: {e}")
