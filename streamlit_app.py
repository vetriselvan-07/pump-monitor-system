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

    # --- CALCULATE MISSING COLUMNS ---
    # If power_kw is missing, calculate it (Formula: P = V * I * PF * sqrt(3))
    if 'power_kw' not in df.columns:
        # Assuming 415V and 0.85 Power Factor
        df['power_kw'] = (df['current_a'] * 415 * 0.85 * 1.732) / 1000
    
    # Calculate Energy (kWh) as cumulative sum of power over time (assuming hourly rows)
    df['energy_kwh'] = df['power_kw'].cumsum()

    # 2. Get Latest Data
    latest = df.iloc[-1]
    site_name = latest.get('site', 'Unknown Plant')
    pump_id = latest.get('pump_id', 'Unknown Pump')
    
    st.sidebar.header("📍 Plant Location")
    st.sidebar.info(f"Site: **{site_name}**\n\nPump: **{pump_id}**")

    # 3. Dynamic Alerts (Plant Specific)
    st.subheader(f"⚠️ Active Alerts: {site_name}")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if latest['vibration_mm_s'] > 4.5:
            st.error(f"🚨 High Vibration at {site_name}")
            with st.expander("View Info"):
                st.write(f"Value: {latest['vibration_mm_s']} mm/s. Check mechanical seal.")
        
        if latest['temp_c'] > 70:
            st.error(f"🔥 Overheat at {site_name}")
            with st.expander("View Info"):
                st.write(f"Value: {latest['temp_c']}°C. Inspect cooling system.")

    with col_b:
        if latest['current_a'] > 26:
            st.error(f"⚡ Abnormal Loading at {site_name}")
            with st.expander("View Info"):
                st.write(f"Value: {latest['current_a']} A. Electrical overload detected.")
        
        if latest['efficiency_pct'] < 70:
            st.warning(f"📉 Degradation at {site_name}")
            with st.expander("View Info"):
                st.write(f"Efficiency: {latest['efficiency_pct']}%. Maintenance required.")

    # 4. Round Gauge Views (Voltage/State)
    st.divider()
    g1, g2, g3 = st.columns(3)
    
    with g1:
        # State Gauge
        fig_state = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = latest['health_score'],
            title = {'text': "Health Classification"},
            gauge = {'axis': {'range': [0, 100]},
                     'steps' : [
                         {'range': [0, 50], 'color': "red"},
                         {'range': [50, 80], 'color': "orange"},
                         {'range': [80, 100], 'color': "green"}]}))
        st.plotly_chart(fig_state, use_container_width=True)

    with g2:
        # Voltage Gauge (assuming 415V standard)
        fig_volt = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 415, # Placeholder if voltage isn't in your CSV
            title = {'text': "Voltage (V)"},
            gauge = {'axis': {'range': [0, 500]},
                     'bar': {'color': "blue"}}))
        st.plotly_chart(fig_volt, use_container_width=True)

    with g3:
        # Efficiency Gauge
        fig_eff = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = latest['efficiency_pct'],
            title = {'text': "Efficiency %"},
            gauge = {'axis': {'range': [0, 100]},
                     'bar': {'color': "green"}}))
        st.plotly_chart(fig_eff, use_container_width=True)

    # 5. Trends (Efficiency, Energy, Power)
    st.divider()
    t1, t2 = st.columns(2)
    
    with t1:
        st.subheader("Efficiency Trend")
        st.line_chart(df['efficiency_pct'])
        
    with t2:
        st.subheader("Energy Consumption (kWh)")
        st.area_chart(df['energy_kwh'])

    st.subheader("Power Demand (kW)")
    st.line_chart(df['power_kw'])

except Exception as e:
    st.error(f"Logic Error: {e}")
    st.info("Ensure your CSV has these columns: vibration_mm_s, temp_c, current_a, efficiency_pct, health_score")
