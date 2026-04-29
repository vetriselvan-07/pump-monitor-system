import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    

    st.header(f"📊 LIVE DIAGNOSIS SYSTEM: {selected_site}")
    max_idx = len(site_data) - 1
    selected_idx = st.number_input(f"Inspect Data Point (Range: 0 - {max_idx})", 
                                   min_value=0, max_value=max_idx, value=max_idx)
    
    record = site_data.iloc[selected_idx]

    st.subheader("🚨 Active Alerts Center")
    active_issues = []

    if record['temp_c'] > 70:
        st.error(f"🔴 **CRITICAL TEMP:** Overheat detected ({record['temp_c']}°C).")
        st.toast("Temperature Critical!", icon="🔥")
        active_issues.append("High Temperature")

    if record['vibration_mm_s'] > 4.5:
        st.markdown(f'<div style="background-color:black;color:white;padding:12px;margin-bottom:10px;border-radius:8px;border-left: 10px solid #ff4b4b;">⚫ <b>VIBRATION WARNING:</b> Abnormal movement ({record["vibration_mm_s"]} mm/s).</div>', unsafe_allow_html=True)
        st.toast("Vibration Detected!", icon="📳")
        active_issues.append("High Vibration (Threshold)")


    if abs(record['z_score']) > 3:
        st.markdown(f'<div style="background-color:orange;color:black;padding:12px;margin-bottom:10px;border-radius:8px;">🟠 <b>STATISTICAL ANOMALY:</b> Sudden Vibration Deviation (Z-Score: {round(record["z_score"], 2)}).</div>', unsafe_allow_html=True)
        active_issues.append("Statistical Anomaly (Z-Score)")

 
    if record['efficiency_pct'] < 70:
        st.warning(f"🟡 **EFFICIENCY LOSS:** Pump performing at {record['efficiency_pct']}%.")
        st.toast("Efficiency Drop!", icon="📉")
        active_issues.append("Low Efficiency")

   
    if record['pressure_bar'] < 3.0:
        st.info(f"🔵 **LOW PRESSURE:** System pressure dropped to {record['pressure_bar']} bar.")
        st.toast("Pressure Low!", icon="💧")
        active_issues.append("Low Pressure")

    
    if record['current_a'] > 26:
        st.markdown(f'<div style="background-color:purple;color:white;padding:12px;margin-bottom:10px;border-radius:8px;border-left: 10px solid #ffffff;">🟣 <b>ABNORMAL LOADING:</b> Motor drawing {record["current_a"]} A.</div>', unsafe_allow_html=True)
        st.toast("Electrical Load High!", icon="⚡")
        active_issues.append("Abnormal Loading")

    if not active_issues:
        st.success(f"✅ All systems at {selected_site} (Index {selected_idx}) are normal.")


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
    

    rec = "No immediate action required. Continue routine monitoring."
    fault = "No significant fault progression detected."
    if "High Vibration (Threshold)" in active_issues or "Statistical Anomaly (Z-Score)" in active_issues:
        rec = "URGENT: Inspect bearings and check shaft alignment."
        fault = "Progression to bearing failure or mechanical seal leakage likely."
    elif "High Temperature" in active_issues:
        rec = "Check lubrication levels and cooling system efficiency."
        fault = "Heat could lead to winding insulation failure."

    report_text = f"""PREDICTIVE MAINTENANCE REPORT
----------------------------
Plant Location: {selected_site}
Record Index: {selected_idx}
Pump ID: {record.get('pump_id', 'Unknown')}

1. CURRENT CONDITION:
   Health Score: {record['health_score']}%
   Efficiency: {record['efficiency_pct']}%

2. DETECTED ANOMALIES:
   {", ".join(active_issues) if active_issues else "None"}

3. LIKELY FAULT PROGRESSION:
   {fault}

4. MAINTENANCE RECOMMENDATION:
   {rec}

5. CONFIDENCE & LIMITATIONS:
   Analysis confidence: 85% based on Z-Score and Threshold logic. 
   Note: Analysis is limited to 10-point rolling window context.
----------------------------
"""
    st.text_area("Analysis Summary", report_text, height=250)
    
    st.download_button(
        label="📥 Download Maintenance Report",
        data=report_text,
        file_name=f"Maintenance_Report_{selected_site}_{selected_idx}.txt",
        mime="text/plain"
    )

    st.divider()
    st.subheader(f"📋 Site History: {selected_site}")
    st.dataframe(site_data, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
