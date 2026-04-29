import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Multi-Plant Pump Monitor", layout="wide")

# --- CUSTOM FUNCTIONS ---
def create_gauge(value, title, color, max_val=100, steps=False):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 50], 'color': "red"},
                {'range': [50, 80], 'color': "orange"},
                {'range': [80, 100], 'color': "green"}
            ] if steps else {'range': [0, max_val], 'color': "white"}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- MAIN APP ---
st.title("🌊 Multi-Plant Intelligence Dashboard")

try:
    # 1. Load Data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # 2. Sidebar Filter (Plant Selection)
    st.sidebar.header("🏢 Site Selection")
    unique_plants = df['site'].unique()
    selected_plant = st.sidebar.selectbox("Choose Plant to Monitor", unique_plants)

    # Filter Data for Selected Plant
    plant_df = df[df['site'] == selected_plant]
    latest = plant_df.iloc[-1]
    pump_id = latest.get('pump_id', 'N/A')

    # 3. Dynamic Alerts (Pop-ups for Selected Plant)
    st.subheader(f"⚠️ Live Alerts: {selected_plant}")
    
    if latest['vibration_mm_s'] > 4.5:
        st.error(f"🚨 **High Vibration** at {selected_plant} (Pump {pump_id})")
        with st.expander("Show Diagnostic Info"):
            st.write(f"Vibration is at {latest['vibration_mm_s']} mm/s. Recommended: Check alignment.")
            
    if latest['temp_c'] > 70:
        st.error(f"🔥 **Overheat Alert** at {selected_plant} (Pump {pump_id})")
        with st.expander("Show Diagnostic Info"):
            st.write(f"Temperature is {latest['temp_c']}°C. Recommended: Inspect cooling water flow.")

    if latest['current_a'] > 26:
        st.toast(f"Abnormal Load at {selected_plant}!", icon="⚠️")
        st.error(f"⚡ **Abnormal Load** at {selected_plant} (Pump {pump_id})")

    # 4. Gauge Row (Efficiency, Voltage, Health)
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        # Health Gauge (with colored steps)
        st.plotly_chart(create_gauge(latest['health_score'], "Health Score %", "green", steps=True), use_container_width=True)

    with col2:
        # Efficiency Gauge
        st.plotly_chart(create_gauge(latest['efficiency_pct'], "Efficiency %", "blue"), use_container_width=True)

    with col3:
        # Voltage Gauge (assuming constant 415 if column is missing, or use 'voltage' if exists)
        volts = latest.get('voltage', 415)
        st.plotly_chart(create_gauge(volts, "Voltage (V)", "purple", max_val=500), use_container_width=True)

    # 5. Trend Analysis for Selected Plant
    st.divider()
    st.subheader(f"📈 Historical Trends: {selected_plant}")
    
    tab1, tab2 = st.tabs(["Performance Trends", "Raw Data Logs"])
    
    with tab1:
        # Combined Trends
        metrics = st.multiselect("Select Trends to Compare", 
                                ['health_score', 'efficiency_pct', 'temp_c', 'vibration_mm_s'],
                                default=['health_score', 'efficiency_pct'])
        fig_trend = px.line(plant_df, x=plant_df.index, y=metrics, title=f"Operational History - {selected_plant}")
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with tab2:
        st.dataframe(plant_df.tail(20), use_container_width=True)

except Exception as e:
    st.error(f"Selection Error: {e}")
    st.info("Ensure your CSV has a 'site' column to enable plant filtering.")
