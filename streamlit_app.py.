import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pump Health Monitor", layout="wide")

# Title and Logo
st.title("🌊 Pump Health & Performance Dashboard")

# 1. Load Data
df = pd.read_csv("pump_multi_300_anomaly.csv")

# 2. Simple Cleaning Logic
df = df.fillna(method='ffill')

# 3. Sidebar KPI & Status
latest = df.iloc[-1]
score = latest['health_score']

if score >= 80:
    st.sidebar.success(f"Status: HEALTHY (Score: {score})")
elif score >= 50:
    st.sidebar.warning(f"Status: DEGRADED (Score: {score})")
else:
    st.sidebar.error(f"Status: CRITICAL (Score: {score})")

# 4. Display Charts (Power, Energy, Flow, etc.)
col1, col2 = st.columns(2)

with col1:
    st.subheader("Health Score Trend")
    fig1 = px.line(df, x=df.index, y='health_score', title="Health Score over Time")
    # Color coding the graph background
    fig1.add_hrect(y0=0, y1=50, fillcolor="red", opacity=0.2)
    fig1.add_hrect(y0=50, y1=80, fillcolor="orange", opacity=0.2)
    fig1.add_hrect(y0=80, y1=100, fillcolor="green", opacity=0.2)
    st.plotly_chart(fig1)

with col2:
    st.subheader("Power & Utilization")
    # Assuming Power is 'current_a' * 'voltage' or just a metric provided
    fig2 = px.line(df, x=df.index, y=['current_a', 'temp_c', 'flow_m3h'], title="Operational Trends")
    st.plotly_chart(fig2)

st.dataframe(df.tail(10)) # Show latest 10 rows
