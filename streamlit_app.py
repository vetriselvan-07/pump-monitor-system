import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Multi-Alert Intelligence System", layout="wide")

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
    # Load data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()
    
    # Statistical Calculations (Rolling Z-Score for Vibration)
    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)
    
    # Global Degradation Flagging
    df['is_degraded'] = (df['health_score'] < 75) | (df['z_score'].abs() > 2.5)
    return df

try:
    df = load_and_process_data()
    all_pumps = sorted(df['site'].unique())

    st.title("📊 MULTI-ALERT INTELLIGENCE SYSTEM")
    
    tab1, tab2 = st.tabs(["🌐 Fleet Comparison (101-104)", "🔍 Live Asset Diagnosis"])

    # --- TAB 1: FLEET COMPARISON ---
    with tab1:
        st.sidebar.header("🕹️ Global Control")
        
        # Helper for your 100-series requirement
        group_option = st.sidebar.radio("Selection Mode", ["Manual Select", "Auto-Group 100-Series"])
        
        if group_option == "Auto-Group 100-Series":
            # Selects all pumps containing '10' (matches 101, 102, 103, 104)
            selected_pumps = [p for p in all_pumps if '10' in str(p)]
        else:
            selected_pumps = st.sidebar.multiselect("Select Pumps", all_pumps, default=[all_pumps[0]])
        
        if not selected_pumps:
            st.warning("⚠️ Please select at least one pump in the sidebar.")
        else:
            comp_df = df[df['site'].isin(selected_pumps)].reset_index()

            st.subheader(f"📈 Performance Trends: {', '.join(map(str, selected_pumps))}")
            metrics = ['vibration_mm_s', 'temp_c', 'current_a', 'pressure_bar', 'flow_m3h', 'efficiency_pct']
            
            melted_df = comp_df.melt(id_vars=['index', 'site'], value_vars=metrics)
            fig_trends = px.line(
                melted_df, x='index', y='value', color='site', 
                facet_row='variable', height=900,
                template="plotly_dark",
                labels={'index': 'Time Step', 'value': 'Reading'}
            )
            fig_trends.update_yaxes(matches=None)
            st.plotly_chart(fig_trends, use_container_width=True)

            st.divider()
            st.subheader("⚠️ Comparative Degradation Zone")
            fig_health = px.scatter(
                comp_df, x='index', y='health_score', color='site',
                size=comp_df['is_degraded'].map({True: 12, False: 4}),
                symbol='is_degraded',
                template="plotly_dark",
                title="Larger 'X' markers indicate detected anomalies"
            )
            st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 2: LIVE DIAGNOSIS ---
    with tab2:
        st.sidebar.divider()
        st.sidebar.header("🔍 Asset Deep-Dive")
        selected_site = st.sidebar.selectbox("Inspect Specific Unit", all_pumps)
        site_data = df[df['site'] == selected_site].reset_index(drop=True)
        
        max_idx = len(site_data) - 1
        selected_idx = st.number_input(f"Timeline Slider (0 - {max_idx})", 
                                       min_value=0, max_value=max_idx, value=max_idx)
        
        record = site_data.iloc[selected_idx]

        # ALERT ENGINE
        st.subheader(f"🚨 Active Status: {selected_site}")
        active_issues = []
        priority = "NORMAL"

        # Logic for Alerts
        if record['temp_c'] > 70:
            st.error(f"🔴 CRITICAL TEMP: {record['temp_c']}°C")
            active_issues.append("Thermal Overload")
            priority = "CRITICAL"

        if record['vibration_mm_s'] > 4.5:
            st.markdown(f'<div style="background-color:#ff4b4b;color:white;padding:10px;border-radius:5px;">⚫ VIBRATION WARNING: {record["vibration_mm_s"]} mm/s</div>', unsafe_allow_html=True)
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
            st.success(f"✅ Pump {selected_site} is operating within normal parameters.")

        # GAUGES
        st.divider()
        util_val = min((record['current_a'] / 35) * 100, 100)
        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        with c1: st.plotly_chart(create_gauge(record['health_score'], "HEALTH %", is_health=True), use_container_width=True)
        with c2: st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", bar_color="#ffa500"), use_container_width=True)
        with c3: st.plotly_chart(create_gauge(util_val, "UTILIZATION %", bar_color="#800080"), use_container_width=True)
        with c4: st.plotly_chart(create_gauge(record['temp_c'], "TEMP °C", 100, bar_color="#ff4b4b"), use_container_width=True)
        with c5: st.plotly_chart(create_gauge(record['pressure_bar'], "PRESS BAR", 10, bar_color="#1E90FF"), use_container_width=True)
        with c6: st.plotly_chart(create_gauge(record['vibration_mm_s'], "VIB mm/s", 10, bar_color="white"), use_container_width=True)

        # PREDICTIVE MAINTENANCE REPORT
        st.divider()
        fault_map = {
            "Thermal Overload": "Bearing friction or cooling failure.",
            "Mechanical Instability": "Misalignment or impeller damage.",
            "Performance Degradation": "Wear rings or cavitation issues.",
            "Transient Anomaly": "Sudden debris or early-stage bearing pitting."
        }
        
        report_text = f"""--- PUMP DIAGNOSTIC REPORT ---
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ASSET: {selected_site} | STATUS: {priority}

CURRENT METRICS:
- Health: {record['health_score']}%
- Operating Efficiency: {record['efficiency_pct']}%

DIAGNOSED ISSUES:
{chr(10).join([f"- {iss}: {fault_map.get(iss, 'Check mechanical alignment')}" for iss in active_issues]) if active_issues else "No faults detected."}
"""
        st.text_area("Maintenance Summary", report_text, height=200)
        st.download_button("📥 Export Report", report_text, file_name=f"PdM_{selected_site}.txt")
        st.dataframe(site_data.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Critical System Error: {e}")
