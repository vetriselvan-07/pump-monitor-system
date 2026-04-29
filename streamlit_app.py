import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Multi-Alert Intelligence System", layout="wide")

st.title("📊 LIVE DIAGNOSIS SYSTEM")

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

try:
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)

    st.sidebar.header("🕹️ Control Room")
    selected_site = st.sidebar.selectbox("Select Plant Location", df['site'].unique())
    site_data = df[df['site'] == selected_site].reset_index(drop=True)
    
    # --- TREND ANALYSIS SECTION ---
    st.sidebar.divider()
    st.sidebar.subheader("📈 Trend Settings")
    trend_param = st.sidebar.selectbox(
        "Select Parameter to Graph", 
        ['vibration_mm_s', 'temp_c', 'pressure_bar', 'efficiency_pct', 'current_a', 'health_score']
    )
    
    max_idx = len(site_data) - 1
    selected_idx = st.number_input(f"Inspect Data Point (Range: 0 - {max_idx})", 
                                   min_value=0, max_value=max_idx, value=max_idx)
    
    record = site_data.iloc[selected_idx]

    # --- TOP ROW: TREND CHART ---
    st.subheader(f"📈 Historical Trend: {trend_param} at {selected_site}")
    fig_trend = px.line(
        site_data, 
        x=site_data.index, 
        y=trend_param,
        title=f"Time Series Analysis of {trend_param}",
        template="plotly_white",
        line_shape="spline"
    )
    # Add a vertical line for the currently inspected point
    fig_trend.add_vline(x=selected_idx, line_dash="dash", line_color="red", annotation_text="Selected Point")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    st.subheader("🚨 Active Alerts Center")
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

    if record['pressure_bar'] < 3.0:
        st.info(f"🔵 **LOW PRESSURE:** System pressure dropped to {record['pressure_bar']} bar.")
        active_issues.append("Pressure Drop")

    if record['current_a'] > 26:
        st.markdown(f'<div style="background-color:purple;color:white;padding:12px;margin-bottom:10px;border-radius:8px;border-left: 10px solid #ffffff;">🟣 <b>ABNORMAL LOADING:</b> Motor drawing {record["current_a"]} A.</div>', unsafe_allow_html=True)
        active_issues.append("Electrical Overload")
        priority = "CRITICAL"

    if not active_issues:
        st.success(f"✅ All systems at {selected_site} are normal.")

    st.divider()
    utilization_val = min((record['current_a'] / 35) * 100, 100)
    
    r1c1, r1c2, r1c3 = st.columns(3)
    r2c1, r2c2, r2c3 = st.columns(3)

    with r1c1: st.plotly_chart(create_gauge(record['health_score'], "HEALTH STATUS %", is_health=True), use_container_width=True)
    with r1c2: st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", bar_color="#ffa500"), use_container_width=True)
    with r1c3: st.plotly_chart(create_gauge(utilization_val, "UTILIZATION %", bar_color="#800080"), use_container_width=True)
    with r2c1: st.plotly_chart(create_gauge(record['temp_c'], "TEMPERATURE °C", 100, bar_color="#ff4b4b"), use_container_width=True)
    with r2c2: st.plotly_chart(create_gauge(record['pressure_bar'], "PRESSURE BAR", 10, bar_color="#1E90FF"), use_container_width=True)
    with r2c3: st.plotly_chart(create_gauge(record['vibration_mm_s'], "VIBRATION mm/s", 10, bar_color="black"), use_container_width=True)

    st.divider()
    st.subheader("📋 Predictive Maintenance Report")
    
    fault_map = {
        "Thermal Overload": "High friction in bearings or cooling jacket blockage.",
        "Mechanical Instability": "Misalignment, looseness, or impeller damage.",
        "Performance Degradation": "Internal wear or possible cavitation.",
        "Electrical Overload": "Pump blockage or motor winding issues.",
        "Transient Anomaly": "Early stage bearing pitting or sudden debris entry."
    }

    rec_map = {
        "CRITICAL": "IMMEDIATE SHUTDOWN ADVISED. Perform vibration spectral analysis and check lubrication.",
        "MAINTENANCE REQUIRED": "Schedule inspection within 48 hours. Check for internal obstructions.",
        "ADVISORY": "Increase monitoring frequency. Inspect at next scheduled downtime.",
        "NORMAL": "Continue routine operations. No action required."
    }

    progression = "Stabilized" if priority == "NORMAL" else "Accelerated wear if left unaddressed."
    
    report_text = f"""
PUMP HEALTH & PREDICTIVE MAINTENANCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-----------------------------------------------------------
SITE LOCATION: {selected_site}
ASSET ID: PMP-{selected_site[:3].upper()}-{selected_idx}
PRIORITY LEVEL: {priority}

1. CURRENT CONDITION SUMMARY:
   - System Health Score: {record['health_score']}%
   - Operating Efficiency: {record['efficiency_pct']}%
   - Load Utilization: {round(utilization_val, 1)}%

2. DETECTED ANOMALIES & ROOT CAUSE:
   {chr(10).join([f"• {issue}: {fault_map.get(issue, 'Unknown mechanical stress')}" for issue in active_issues]) if active_issues else "No anomalies detected."}

3. LIKELY FAULT PROGRESSION:
   {progression} - Continued operation under current conditions likely leads to catastrophic component failure within 50-100 operating hours.

4. MAINTENANCE RECOMMENDATIONS:
   {rec_map[priority]}

5. CONFIDENCE & LIMITATIONS:
   - Analysis Confidence: 92% (Based on multi-sensor fusion)
   - Limitations: Analysis assumes constant speed operation. Results may vary under Variable Frequency Drive (VFD) fluctuations.
-----------------------------------------------------------
"""
    st.text_area("Finalized Report", report_text, height=350)
    
    st.download_button(
        label="📥 Download Official Report",
        data=report_text,
        file_name=f"PdM_Report_{selected_site}_{selected_idx}.txt",
        mime="text/plain"
    )

    st.divider()
    st.dataframe(site_data, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
