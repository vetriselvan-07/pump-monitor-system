import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    
    # Calculate Power if missing (Current * assumed 415V * sqrt(3) * PF)
    if 'power_kw' not in df.columns:
        df['power_kw'] = (df['current_a'] * 415 * 1.732 * 0.85) / 1000

    st.sidebar.header("📍 Current Location")
    st.sidebar.info(f"Monitoring: **{site_name}**")

    # 3. Dynamic Alerts (Keep your existing logic)
    st.subheader(f"⚠️ Active Alerts for {site_name}")
    if latest['vibration_mm_s'] > 4.5:
        st.error(f"🚨 High Vibration at **{site_name}** ({latest['vibration_mm_s']} mm/s)")
        with st.expander(f"ℹ️ View Plant Info"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Action:** Check bearing lubrication.")

    # 4. Round View (Gauge) for Voltage/State Classification
    # We use a gauge to show "State" based on Voltage or Health
    st.divider()
    col_gauge, col_text = st.columns([1, 2])
    
    with col_gauge:
        st.subheader("System State")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = latest['health_score'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Health State %"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "black"},
                'steps' : [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "green"}]
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_text:
        st.subheader("Key Performance Metrics")
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Efficiency", f"{latest['efficiency_pct']}%")
        m2.metric("Power Consumption", f"{latest['power_kw']:.2f} kW")
        m3.metric("Vibration", f"{latest['vibration_mm_s']} mm/s")

    # 5. Efficiency Trend (Separately)
    st.divider()
    st.subheader("📈 Efficiency & Power Trends")
    tab1, tab2, tab3 = st.tabs(["Efficiency Trend", "Energy & Power", "Voltage/Current"])
    
    with tab1:
        fig_eff = px.area(df, x=df.index, y='efficiency_pct', title="Efficiency Trend (%)", color_discrete_sequence=['#00CC96'])
        fig_eff.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Degradation Limit")
        st.plotly_chart(fig_eff, use_container_width=True)
        
    with tab2:
        # Energy/Power Trend
        fig_pwr = px.line(df, x=df.index, y='power_kw', title="Power Usage (kW)")
        st.plotly_chart(fig_pwr, use_container_width=True)
        
    with tab3:
        # Show Current/Voltage behavior
        fig_elec = px.line(df, x=df.index, y=['current_a'], title="Electrical Loading (Amps)")
        st.plotly_chart(fig_elec, use_container_width=True)

    # 6. Overall Health Trend (Original)
    st.divider()
    st.subheader("📋 Reliability Summary")
    fig_health = px.line(df, x=df.index, y='health_score', title=f"Reliability History: {site_name}")
    st.plotly_chart(fig_health, use_container_width=True)

except Exception as e:
    st.error(f"Data Load Error: {e}")
