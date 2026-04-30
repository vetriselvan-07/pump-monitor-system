import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Multi-Plant Intelligence System", layout="wide")

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
    # --- DATA ENGINE ---
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()
    df['pump_id'] = df['pump_id'].astype(str).str.strip()
    df['site'] = df['site'].astype(str).str.strip()

    # Calculations (Z-Score calculated per Site)
    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)

    # --- TABS NAVIGATION ---
    tab1, tab2 = st.tabs(["🔍 Live Diagnostic Center", "📊 Quad-Pump Fleet Comparison"])

    # --- PAGE 1: LIVE DIAGNOSTIC CENTER (Now with Plant Selection) ---
    with tab1:
        st.header("🔍 Global Asset Diagnosis")
        
        # PLANT SELECTION (A or B)
        col_plant, col_pump = st.columns(2)
        with col_plant:
            selected_site = st.selectbox("📍 Select Plant Location", sorted(df['site'].unique()), key="live_site_select")
        
        site_data_all = df[df['site'] == selected_site].reset_index(drop=True)
        
        with col_pump:
            # Further filter by specific pump within that plant
            available_pumps_live = sorted(site_data_all['pump_id'].unique())
            selected_pump_live = st.selectbox("⛽ Select Specific Pump ID", available_pumps_live)
            
        # Final dataset for the gauges
        site_data = site_data_all[site_data_all['pump_id'] == selected_pump_live].reset_index(drop=True)
        
        st.divider()
        st.subheader(f"📊 Live Status: {selected_site} — Pump {selected_pump_live}")
        
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
            st.success(f"✅ All systems at {selected_site} - Pump {selected_pump_live} are normal.")

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
        st.subheader("📋 Site-Specific Maintenance Report")
        
        rec = "No immediate action required."
        fault = "No significant fault progression detected."
        if "High Vibration" in str(active_issues):
            rec = "URGENT: Inspect bearings and check alignment."
            fault = "Mechanical failure imminent."
        elif "High Temperature" in active_issues:
            rec = "Check lubrication and cooling."
            fault = "Winding damage risk."

        report_text = f"PREDICTIVE MAINTENANCE REPORT\n----------------------------\nSITE: {selected_site}\nPUMP ID: {selected_pump_live}\nRecord Index: {selected_idx}\n\n1. CONDITION:\n   Health: {record['health_score']}%\n   Efficiency: {record['efficiency_pct']}%\n\n2. ANOMALIES: {', '.join(active_issues) if active_issues else 'None'}\n\n3. ACTION: {rec}\n----------------------------"
        st.text_area("Analysis Summary", report_text, height=200)
        st.download_button(label=f"📥 Download {selected_site} Report", data=report_text, file_name=f"Report_{selected_site}_{selected_pump_live}.txt")

    # --- PAGE 2: QUAD-PUMP COMPARISON ---
    with tab2:
        st.header("📊 Quad-Pump Fleet Analytics")
        
        # Site Selection for Comparison
        comp_site = st.selectbox("Select Plant for 4-Pump Review", sorted(df['site'].unique()), key="quad_site_select")
        
        site_pumps = sorted(df[df['site'] == comp_site]['pump_id'].unique())
        
        st.sidebar.divider()
        st.sidebar.subheader("⚖️ Comparison Controls")
        
        target_default = [p for p in site_pumps if any(num in p for num in ['101', '102', '103', '104'])]
        
        selected_4 = st.sidebar.multiselect(
            "Select Exactly 4 Pumps", 
            site_pumps, 
            default=target_default if len(target_default) == 4 else site_pumps[:4]
        )

        if len(selected_4) < 1:
            st.warning("Please select pumps from the sidebar to begin comparison.")
        else:
            quad_df = df[(df['site'] == comp_site) & (df['pump_id'].isin(selected_4))].reset_index()
            
            st.subheader(f"⏱️ Trend Analysis: {comp_site}")
            metrics = ['vibration_mm_s', 'temp_c', 'efficiency_pct', 'pressure_bar', 'current_a', 'flow_m3h']
            
            m_cols = st.columns(2)
            for i, metric in enumerate(metrics):
                with m_cols[i % 2]:
                    fig = px.line(quad_df, x='index', y=metric, color='pump_id',
                                 title=f"{metric.replace('_', ' ').upper()}",
                                 template="plotly_dark", height=300)
                    st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader(f"🩺 Condition Overview: {comp_site}")
            h_cols = st.columns(len(selected_4))
            for i, pid in enumerate(selected_4):
                latest_subset = quad_df[quad_df['pump_id'] == pid]
                if not latest_subset.empty:
                    latest_rec = latest_subset.iloc[-1]
                    with h_cols[i]:
                        st.metric(label=f"Pump {pid}", value=f"{latest_rec['health_score']}% Health")
                        st.plotly_chart(create_gauge(latest_rec['health_score'], f"ID: {pid}", is_health=True), use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
