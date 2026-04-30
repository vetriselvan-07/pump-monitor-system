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
        title={'text': title, 'font': {'size': 14, 'color': 'gray'}},
        gauge={
            'axis': {'range': [0, max_val], 'tickcolor': "gray"}, 
            'bar': {'color': bar_color}, 
            'steps': steps
        }
    ))
    fig.update_layout(height=180, margin=dict(l=15, r=15, t=40, b=15))
    return fig

# --- DATA ENGINE ---
@st.cache_data
def load_and_process_data():
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()
    
    # Statistical Calculations (Rolling Z-Score)
    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)
    
    # Degradation Flags
    df['is_degraded'] = (df['health_score'] < 75) | (df['z_score'].abs() > 2.5)
    return df

try:
    df = load_and_process_data()
    all_pumps = df['site'].unique()

    st.title("📊 MULTI-ALERT INTELLIGENCE SYSTEM")
    
    # TABS FOR NAVIGATION
    tab1, tab2 = st.tabs(["🌐 Fleet Comparison", "🔍 Live Asset Diagnosis"])

    # --- TAB 1: FLEET COMPARISON ---
    with tab1:
        st.sidebar.header("🕹️ Global Control")
        selected_pumps = st.sidebar.multiselect("Select Pumps to Compare", all_pumps, default=[all_pumps[0]])
        
        comp_df = df[df['site'].isin(selected_pumps)].reset_index()

        st.subheader("📈 Multi-Parameter Time Trends")
        metrics = ['vibration_mm_s', 'temp_c', 'current_a', 'pressure_bar', 'flow_m3h', 'efficiency_pct']
        
        melted_df = comp_df.melt(id_vars=['index', 'site'], value_vars=metrics)
        fig_trends = px.line(
            melted_df, x='index', y='value', color='site', 
            facet_row='variable', height=900,
            labels={'index': 'Time Step', 'value': 'Reading'},
            title="Comparative Trend Analysis"
        )
        fig_trends.update_yaxes(matches=None)
        st.plotly_chart(fig_trends, use_container_width=True)

        st.divider()
        st.subheader("⚠️ Degradation Detection Zone")
        fig_health = px.scatter(
            comp_df, x='index', y='health_score', color='site',
            size=comp_df['is_degraded'].map({True: 12, False: 4}),
            symbol='is_degraded',
            title="Asset Health: Larger 'X' indicates visible degradation periods"
        )
        st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 2: LIVE DIAGNOSIS ---
    with tab2:
        st.sidebar.divider()
        st.sidebar.header("🔍 Asset Deep-Dive")
        selected_site = st.sidebar.selectbox("Inspect Specific Plant", all_pumps)
        site_data = df[df['site'] == selected_site].reset_index(drop=True)
        
        max_idx = len(site_data) - 1
        selected_idx = st.number_input(f"Inspect Data Point (0 - {max_idx})", 
                                       min_value=0, max_value=max_idx, value=max_idx)
        
        record = site_data.iloc[selected_idx]

        # Alert Engine
        st.subheader(f"🚨 Active Alerts: {selected_site}")
        active_issues = []
        priority = "NORMAL"

        if record['temp_c'] > 70:
            st.error(f"🔴 **CRITICAL TEMP:** Overheat detected ({record['temp_c']}°C).")
            active_issues.append("Thermal Overload")
            priority = "CRITICAL"

        if record['vibration_mm_s'] > 4.5:
            st.markdown(f'<div style="background-color:black;color:white;padding:12px;margin-bottom:10px;border-radius:8px;border-left: 10px solid #ff4b4b;">⚫ <b>VIBRATION WARNING:</b> Abnormal movement ({record["vibration_mm_s"]} mm/s).</div>', unsafe_allow_html=True)
            active_issues.append("Mechanical Instability")
            priority = "CRITICAL"

        if abs(record['z_score']) > 3:
            st.markdown(f'<div style="background-color:orange;color:black;padding:12px;margin-bottom:10px;border-radius:8px;">🟠 <b>STATISTICAL ANOMALY:</b> Sudden Vibration Deviation (Z-Score: {round(record["z_score"], 2)}).</div>', unsafe_allow_html=True)
            active_issues.append("Transient Anomaly")
            if priority != "CRITICAL": priority = "ADVISORY"

        if record['efficiency_pct'] < 70:
            st.warning(f"🟡 **EFFICIENCY LOSS:** Pump performing at {record['efficiency_pct']}%.")
            active_issues.append("Performance Degradation")
            if priority == "NORMAL": priority = "MAINTENANCE REQUIRED"

        if not active_issues:
            st.success(f"✅ All systems at {selected_site} are normal.")

        # Gauges
        st.divider()
        util_val = min((record['current_a'] / 35) * 100, 100)
        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        with c1: st.plotly_chart(create_gauge(record['health_score'], "HEALTH STATUS %", is_health=True), use_container_width=True)
        with c2: st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", bar_color="#ffa500"), use_container_width=True)
        with c3: st.plotly_chart(create_gauge(util_val, "UTILIZATION %", bar_color="#800080"), use_container_width=True)
        with c4: st.plotly_chart(create_gauge(record['temp_c'], "TEMPERATURE °C", 100, bar_color="#ff4b4b"), use_container_width=True)
        with c5: st.plotly_chart(create_gauge(record['pressure_bar'], "PRESSURE BAR", 10, bar_color="#1E90FF"), use_container_width=True)
        with c6: st.plotly_chart(create_gauge(record['vibration_mm_s'], "VIBRATION mm/s", 10, bar_color="black"), use_container_width=True)

        # Predictive Report
        st.divider()
        fault_map = {
            "Thermal Overload": "High friction in bearings or cooling jacket blockage.",
            "Mechanical Instability": "Misalignment, looseness, or impeller damage.",
            "Performance Degradation": "Internal wear or possible cavitation.",
            "Electrical Overload": "Pump blockage or motor winding issues.",
            "Transient Anomaly": "Early stage bearing pitting or sudden debris entry."
        }
        rec_map = {
            "CRITICAL": "IMMEDIATE SHUTDOWN ADVISED. Perform vibration spectral analysis.",
            "MAINTENANCE REQUIRED": "Schedule inspection within 48 hours. Check for internal obstructions.",
            "ADVISORY": "Increase monitoring frequency. Inspect at next scheduled downtime.",
            "NORMAL": "Continue routine operations. No action required."
        }

        report_text = f"""
PUMP HEALTH & PREDICTIVE MAINTENANCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
SITE: {selected_site} | PRIORITY: {priority}

1. CONDITION SUMMARY:
   - Health Score: {record['health_score']}% | Efficiency: {record['efficiency_pct']}%

2. DETECTED ANOMALIES:
   {chr(10).join([f"• {issue}: {fault_map.get(issue, 'General Stress')}" for issue in active_issues]) if active_issues else "No anomalies."}

3. RECOMMENDATION:
   {rec_map[priority]}
"""
        st.text_area("Finalized Report", report_text, height=250)
        st.download_button("📥 Download Report", report_text, file_name=f"Report_{selected_site}.txt")
        st.dataframe(site_data.tail(20), use_container_width=True)

except Exception as e:
    st.error(f"System Error: {e}")
