import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Pump ID Intelligence System", layout="wide")

def create_gauge(value, title, max_val=100, is_health=False, bar_color="#31333F"):
    steps = [
        {'range': [0, 50], 'color': "#ff4b4b"}, 
        {'range': [50, 80], 'color': "#ffa500"}, 
        {'range': [80, 100], 'color': "#00cc96"}
    ] if is_health else []
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(value, 2),
        title={'text': title, 'font': {'size': 14, 'color': 'white'}},
        gauge={
            'axis': {'range': [0, max_val], 'tickcolor': "gray"}, 
            'bar': {'color': bar_color}, 
            'steps': steps,
            'bgcolor': "#262730"
        }
    ))
    fig.update_layout(height=180, margin=dict(l=15, r=15, t=40, b=15), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- DATA ENGINE ---
@st.cache_data
def load_and_process_data():
    # Load your CSV
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    
    # Standardize column name and clean whitespace
    if 'site' in df.columns and 'pump_id' not in df.columns:
        df = df.rename(columns={'site': 'pump_id'})
    
    df['pump_id'] = df['pump_id'].astype(str).str.strip()
    df = df.ffill()
    
    # Statistical Calculations (Rolling Z-Score for Vibration)
    window = 10
    df['rolling_mean'] = df.groupby('pump_id')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('pump_id')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)
    
    # Global Degradation Flagging
    df['is_degraded'] = (df['health_score'] < 75) | (df['z_score'].abs() > 2.5)
    return df

try:
    df = load_and_process_data()
    all_pump_ids = sorted(df['pump_id'].unique())

    st.title("📊 PUMP ID INTELLIGENCE SYSTEM")
    
    tab1, tab2 = st.tabs(["🌐 Fleet Comparison (ID 101-104)", "🔍 Live Asset Diagnosis"])

    # --- TAB 1: FLEET COMPARISON ---
    with tab1:
        st.sidebar.header("🕹️ Global Control")
        
        group_option = st.sidebar.radio("Selection Mode", ["Manual Select", "Compare 101-104 Range"])
        
        if group_option == "Compare 101-104 Range":
            # Search for the numbers 101, 102, 103, or 104 inside the ID strings
            target_nums = ['101', '102', '103', '104']
            selected_ids = [pid for pid in all_pump_ids if any(num in pid for num in target_nums)]
        else:
            selected_ids = st.sidebar.multiselect("Select Pump IDs", all_pump_ids, default=[all_pump_ids[0]])
        
        if not selected_ids:
            st.warning("⚠️ Please select at least one Pump ID in the sidebar.")
        else:
            comp_df = df[df['pump_id'].isin(selected_ids)].reset_index()

            st.subheader(f"📈 Performance Comparison: {', '.join(selected_ids)}")
            metrics = ['vibration_mm_s', 'temp_c', 'current_a', 'pressure_bar', 'flow_m3h', 'efficiency_pct']
            
            melted_df = comp_df.melt(id_vars=['index', 'pump_id'], value_vars=metrics)
            fig_trends = px.line(
                melted_df, x='index', y='value', color='pump_id', 
                facet_row='variable', height=950,
                template="plotly_dark",
                labels={'index': 'Time Step', 'value': 'Reading', 'pump_id': 'Pump ID'}
            )
            fig_trends.update_yaxes(matches=None)
            st.plotly_chart(fig_trends, use_container_width=True)

            st.divider()
            st.subheader("⚠️ Comparative Degradation Zone")
            fig_health = px.scatter(
                comp_df, x='index', y='health_score', color='pump_id',
                size=comp_df['is_degraded'].map({True: 12, False: 4}),
                symbol='is_degraded',
                template="plotly_dark"
            )
            st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 2: LIVE DIAGNOSIS ---
    with tab2:
        st.sidebar.divider()
        st.sidebar.header("🔍 Asset Deep-Dive")
        selected_id = st.sidebar.selectbox("Inspect Specific Pump ID", all_pump_ids)
        site_data = df[df['pump_id'] == selected_id].reset_index(drop=True)
        
        max_idx = len(site_data) - 1
        selected_idx = st.number_input(f"Timeline Step (0 - {max_idx})", 
                                       min_value=0, max_value=max_idx, value=max_idx)
        
        record = site_data.iloc[selected_idx]

        st.subheader(f"🚨 Status: Pump ID {selected_id}")
        active_issues = []
        priority = "NORMAL"

        if record['temp_c'] > 70:
            st.error(f"🔴 CRITICAL TEMP: {record['temp_c']}°C")
            active_issues.append("Thermal Overload")
            priority = "CRITICAL"

        if record['vibration_mm_s'] > 4.5:
            st.markdown(f'<div style="background-color:#ff4b4b;color:white;padding:10px;border-radius:5px;margin-bottom:10px;">⚫ VIBRATION WARNING: {record["vibration_mm_s"]} mm/s</div>', unsafe_allow_html=True)
            active_issues.append("Mechanical Instability")
            priority = "CRITICAL"

        if abs(record['z_score']) > 3:
            st.warning(f"🟠 STATISTICAL ANOMALY: Z-Score {round(record['z_score'], 2)}")
            active_issues.append("Transient Anomaly")
            if priority != "CRITICAL": priority = "ADVISORY"

        if record['efficiency_pct'] < 70:
            st.info(f"🟡 EFFICIENCY DROP: {record['efficiency_pct']}%")
            active_issues.append("Performance Degradation")
            if priority == "NORMAL": priority = "MAINTENANCE"

        if not active_issues:
            st.success(f"✅ Pump {selected_id} is operating normally.")

        st.divider()
        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        with c1: st.plotly_chart(create_gauge(record['health_score'], "HEALTH %", is_health=True), use_container_width=True)
        with c2: st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", bar_color="#ffa500"), use_container_width=True)
        with c3: st.plotly_chart(create_gauge(min((record['current_a']/35)*100, 100), "UTILIZATION %", bar_color="#800080"), use_container_width=True)
        with c4: st.plotly_chart(create_gauge(record['temp_c'], "TEMP °C", 100, bar_color="#ff4b4b"), use_container_width=True)
        with c5: st.plotly_chart(create_gauge(record['pressure_bar'], "PRESS BAR", 10, bar_color="#1E90FF"), use_container_width=True)
        with c6: st.plotly_chart(create_gauge(record['vibration_mm_s'], "VIB mm/s", 10, bar_color="white"), use_container_width=True)

        st.divider()
        report_text = f"--- PUMP DIAGNOSTIC REPORT ---\nTIMESTAMP: {datetime.now()}\nID: {selected_id}\nSTATUS: {priority}\n\nISSUES:\n" + "\n".join([f"- {i}" for i in active_issues])
        st.text_area("Maintenance Summary", report_text, height=150)
        st.download_button("📥 Export Report", report_text, file_name=f"PdM_{selected_id}.txt")

except Exception as e:
    st.error(f"System Error: {e}")
