import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pump Health Monitor", layout="wide")

st.title("🌊 Industrial Pump Intelligence Dashboard")

try:
    # 1. Load and Clean Data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # 2. Get Latest Data for Alerts
    latest = df.iloc[-1]
    
    # 3. Sidebar: Plant Information
    st.sidebar.header("📍 Plant Information")
    st.sidebar.info(f"**Site:** {latest.get('site', 'N/A')}\n\n**Pump ID:** {latest.get('pump_id', 'N/A')}")

    # 4. Custom Logic Alerts (The "Pop-ups")
    st.subheader("⚠️ Real-Time Alerts")
    
    # Create columns for alerts to look organized
    alert_col = st.columns(1)[0]
    
    if latest['vibration_mm_s'] > 4.5:
        st.error(f"🚨 WARNING: High Vibration detected! ({latest['vibration_mm_s']} mm/s)")
    
    if latest['temp_c'] > 70:
        st.error(f"🔥 WARNING: Temperature Over Limit! ({latest['temp_c']}°C)")
        
    if latest['pressure_bar'] < 3.0:
        st.warning(f"📉 WARNING: Low Pressure Drop! ({latest['pressure_bar']} bar)")
        
    if latest['efficiency_pct'] < 70:
        st.info(f"⚙️ DEGRADATION: Efficiency below threshold ({latest['efficiency_pct']}%)")
        
    if latest['current_a'] > 26:
        st.toast("Abnormal Loading Detected!", icon="⚠️")
        st.error(f"⚡ ABNORMAL LOADING: Current spike detected! ({latest['current_a']} A)")

    # 5. Dashboard Metrics (Cards)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Health Score", f"{latest['health_score']}%")
    m2.metric("Vibration", f"{latest['vibration_mm_s']} mm/s")
    m3.metric("Temperature", f"{latest['temp_c']}°C")
    m4.metric("Efficiency", f"{latest['efficiency_pct']}%")

    # 6. Charts
    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Health Trend (Green/Orange/Red)")
        fig1 = px.line(df, x=df.index, y='health_score', title="Health Score Trend")
        # Color coding thresholds
        fig1.add_hrect(y0=0, y1=50, fillcolor="red", opacity=0.2)
        fig1.add_hrect(y0=50, y1=80, fillcolor="orange", opacity=0.2)
        fig1.add_hrect(y0=80, y1=100, fillcolor="green", opacity=0.2)
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Operational Parameter Trends")
        # Let user choose what to see
        metric_choice = st.multiselect("Select Parameters", 
                                      ['vibration_mm_s', 'temp_c', 'pressure_bar', 'current_a'],
                                      default=['vibration_mm_s', 'temp_c'])
        fig2 = px.line(df, x=df.index, y=metric_choice)
        st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"System Error: {e}")
