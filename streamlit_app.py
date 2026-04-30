import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Multi-Plant Intelligence System", layout="wide")

def create_gauge(value, title, max_val=100, is_health=False, bar_color="#31333F"):
    steps = [{'range': [0, 50], 'color': "#ff4b4b"}, {'range': [50, 80], 'color': "#ffa500"}, {'range': [80, 100], 'color': "#00cc96"}] if is_health else []
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(value, 2),
        title={'text': title, 'font': {'size': 14, 'color': 'white'}},
        gauge={'axis': {'range': [0, max_val]}, 'bar': {'color': bar_color}, 'steps': steps, 'bgcolor': "#262730"}
    ))
    fig.update_layout(height=180, margin=dict(l=15, r=15, t=40, b=15), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- DATA ENGINE ---
@st.cache_data
def load_and_process_data():
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    # Ensure both 'site' (Plant) and 'pump_id' exist
    df['site'] = df['site'].astype(str).str.strip()
    df['pump_id'] = df['pump_id'].astype(str).str.strip()
    df = df.ffill()
    
    # Statistical Calculations
    window = 10
    df['rolling_mean'] = df.groupby('pump_id')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('pump_id')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)
    df['is_degraded'] = (df['health_score'] < 75) | (df['z_score'].abs() > 2.5)
    return df

try:
    df = load_and_process_data()
    all_plants = sorted(df['site'].unique())

    st.title("🏭 MULTI-PLANT PUMP INTELLIGENCE")
    
    tab1, tab2 = st.tabs(["🌐 Fleet Comparison", "🔍 Live Plant Diagnosis"])

    # --- TAB 1: FLEET COMPARISON ---
    with tab1:
        st.sidebar.header("🕹️ Fleet Controls")
        selected_plant = st.sidebar.selectbox("Select Plant", all_plants)
        
        # Filter available pumps based on the selected plant
        plant_pumps = sorted(df[df['site'] == selected_plant]['pump_id'].unique())
        
        group_option = st.sidebar.radio(f"Selection for {selected_plant}", ["Manual Select", "Compare All in Plant"])
        
        if group_option == "Compare All in Plant":
            selected_ids = plant_pumps
        else:
            selected_ids = st.sidebar.multiselect("Select Pump IDs", plant_pumps, default=[plant_pumps[0]] if plant_pumps else [])
        
        if not selected_ids:
            st.warning("⚠️ Please select pumps to compare.")
        else:
            comp_df = df[df['pump_id'].isin(selected_ids)].reset_index()
            st.subheader(f"📊 Trends: {selected_plant} | Pumps: {', '.join(selected_ids)}")
            
            metrics = ['vibration_mm_s', 'temp_c', 'current_a', 'pressure_bar', 'flow_m3h', 'efficiency_pct']
            melted_df = comp_df.melt(id_vars=['index', 'pump_id'], value_vars=metrics)
            
            fig_trends = px.line(melted_df, x='index', y='value', color='pump_id', facet_row='variable', 
                                 height=900, template="plotly_dark")
            fig_trends.update_yaxes(matches=None)
            st.plotly_chart(fig_trends, use_container_width=True)

    # --- TAB 2: LIVE DIAGNOSIS & PLANT REPORTS ---
    with tab2:
        st.sidebar.divider()
        st.sidebar.header("🔍 Unit Inspection")
        diag_plant = st.sidebar.selectbox("Select Plant for Report", all_plants, key="diag_plant")
        
        # Filter pumps for the specific plant selected in Tab 2
        diag_pumps = sorted(df[df['site'] == diag_plant]['pump_id'].unique())
        selected_id = st.sidebar.selectbox("Select Pump ID", diag_pumps)
        
        unit_data = df[df['pump_id'] == selected_id].reset_index(drop=True)
        record = unit_data.iloc[-1] # Always look at the latest data point

        st.subheader(f"🚨 Live Status: {diag_plant} — {selected_id}")
        
        # UI Columns for Gauges
        c1, c2, c3 = st.columns(3)
        with c1: st.plotly_chart(create_gauge(record['health_score'], "HEALTH %", is_health=True), use_container_width=True)
        with c2: st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", bar_color="#ffa500"), use_container_width=True)
        with c3: st.plotly_chart(create_gauge(record['temp_c'], "TEMP °C", 100, bar_color="#ff4b4b"), use_container_width=True)

        # Automated Plant-Specific Report
        st.divider()
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report_text = f"""--- INDUSTRIAL ASSET REPORT ---
PLANT SITE: {diag_plant}
PUMP IDENTIFIER: {selected_id}
GENERATED AT: {report_time}

[CONDITION SUMMARY]
Health Score: {record['health_score']}%
Vibration: {record['vibration_mm_s']} mm/s
Temperature: {record['temp_c']}°C

[DIAGNOSIS]
- Status: {"CRITICAL" if record['is_degraded'] else "NORMAL"}
- Recommendation: {"Immediate Inspection Required" if record['is_degraded'] else "Continue Routine Monitoring"}

Authorized by: AI Intelligence System
"""
        st.subheader("📝 Site-Wise Maintenance Report")
        st.text_area(f"Generated Report for {diag_plant}", report_text, height=220)
        st.download_button(f"📥 Download {diag_plant} Report", report_text, file_name=f"Report_{diag_plant}_{selected_id}.txt")

except Exception as e:
    st.error(f"Configuration Error: {e}")
