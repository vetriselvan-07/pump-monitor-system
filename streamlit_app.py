import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Multi-Plant Pump Monitor", layout="wide")

# --- FIXED GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False):
    # Define steps clearly to avoid the 'Step constructor' error
    if is_health:
        steps = [
            {'range': [0, 50], 'color': "red"},
            {'range': [50, 80], 'color': "orange"},
            {'range': [80, 100], 'color': "green"}
        ]
    else:
        steps = [{'range': [0, max_val], 'color': "lightgray"}]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 2),
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, max_val], 'tickwidth': 1},
            'bar': {'color': "black"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': steps
        }
    ))
    fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20))
    return fig

# --- MAIN APP ---
st.title("🌊 Multi-Plant Intelligence Dashboard")

try:
    # 1. Load Data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # 2. Sidebar Filter
    st.sidebar.header("🏢 Site Selection")
    if 'site' in df.columns:
        unique_plants = df['site'].unique()
        selected_plant = st.sidebar.selectbox("Choose Plant to Monitor", unique_plants)
        plant_df = df[df['site'] == selected_plant]
    else:
        st.error("Column 'site' not found in CSV!")
        st.stop()

    latest = plant_df.iloc[-1]
    pump_id = latest.get('pump_id', 'N/A')

    # 3. Alerts for Selected Plant
    st.subheader(f"⚠️ Live Alerts: {selected_plant}")
    
    # Check for specific thresholds
    if latest['vibration_mm_s'] > 4.5:
        st.error(f"🚨 **High Vibration** at {selected_plant}")
        with st.expander(f"ℹ️ Plant Info: {selected_plant}"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Vibration:** {latest['vibration_mm_s']} mm/s (Limit: 4.5)")

    if latest['temp_c'] > 70:
        st.error(f"🔥 **Overheat Alert** at {selected_plant}")
        with st.expander(f"ℹ️ Plant Info: {selected_plant}"):
            st.write(f"**Pump ID:** {pump_id}")
            st.write(f"**Temperature:** {latest['temp_c']}°C (Limit: 70)")

    # 4. Gauges (Health, Efficiency, Voltage)
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.plotly_chart(create_gauge(latest['health_score'], "Health State %", is_health=True), use_container_width=True)

    with col2:
        # Show efficiency
        st.plotly_chart(create_gauge(latest['efficiency_pct'], "Efficiency %"), use_container_width=True)

    with col3:
        # Show Voltage (assuming 415 if missing)
        volts = latest.get('voltage', 415)
        st.plotly_chart(create_gauge(volts, "Voltage (V)", max_val=500), use_container_width=True)

    # 5. Trends
    st.divider()
    st.subheader(f"📈 Performance Trends: {selected_plant}")
    
    # Combined line chart for parameters
    metrics = ['health_score', 'efficiency_pct', 'temp_c']
    fig_trend = px.line(plant_df, y=metrics, title="Historical View")
    st.plotly_chart(fig_trend, use_container_width=True)

except Exception as e:
    st.error(f"Application Error: {e}")
