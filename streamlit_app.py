import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pump Health Monitor", layout="wide")

st.title("🌊 Pump Health & Performance Dashboard")

# 1. Load Data
try:
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    
    # 2. Modern Cleaning Logic (Fixed for new Pandas versions)
    df = df.ffill()

    # 3. Sidebar KPI & Status
    latest = df.iloc[-1]
    score = latest['health_score']

    if score >= 80:
        st.sidebar.success(f"Status: HEALTHY (Score: {score})")
    elif score >= 50:
        st.sidebar.warning(f"Status: DEGRADED (Score: {score})")
    else:
        st.sidebar.error(f"Status: CRITICAL (Score: {score})")

    # 4. Display Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Health Score Trend")
        fig1 = px.line(df, x=df.index, y='health_score', title="Health Score over Time")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Operational Trends")
        # Ensure these column names match your CSV exactly
        metrics = [c for c in ['current_a', 'temp_c', 'flow_m3h'] if c in df.columns]
        fig2 = px.line(df, x=df.index, y=metrics, title="Sensor Values")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Recent Data Logs")
    st.dataframe(df.tail(10))

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Check if your CSV filename is exactly: pump_multi_300_anomaly.csv")
