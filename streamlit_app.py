import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    fig.update_layout(height=160, margin=dict(l=15, r=15, t=40, b=15))
    return fig

try:
    df_raw = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df_raw.dropna().copy()
    
    df['pump_id'] = df['pump_id'].astype(str).str.strip()
    df['site'] = df['site'].astype(str).str.strip()

    # --- ANOMALY DETECTION ENGINE ---
    # Rolling Statistics for Vibration Z-Score
    window = 10
    df['roll_m'] = df.groupby('pump_id')['vibration_mm_s'].transform(lambda x: x.rolling(window, min_periods=1).mean())
    df['roll_s'] = df.groupby('pump_id')['vibration_mm_s'].transform(lambda x: x.rolling(window, min_periods=1).std())
    df['vibration_zscore'] = (df['vibration_mm_s'] - df['roll_m']) / df['roll_s'].replace(0, np.nan)
    df['vibration_zscore'] = df['vibration_zscore'].fillna(0)

    st.sidebar.header("💾 Data Management")
    st.sidebar.info(f"Rows removed (Incomplete): {len(df_raw) - len(df)}")
    
    cleaned_csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(label="📥 Download Cleaned CSV", data=cleaned_csv, file_name="pump_data_cleaned.csv", mime="text/csv")

    tab1, tab2 = st.tabs(["🔍 Live Diagnostic Center", "📊 Quad-Pump Fleet Comparison"])

    with tab1:
        st.header("🔍 Global Asset Diagnosis")
        
        c1, c2 = st.columns(2)
        with c1: selected_site = st.selectbox("📍 Select Plant Location", sorted(df['site'].unique()))
        site_data_all = df[df['site'] == selected_site].reset_index(drop=True)
        with c2: 
            available_pumps = sorted(site_data_all['pump_id'].unique())
            selected_pump = st.selectbox("⛽ Select Specific Pump ID", available_pumps)
            
        site_data = site_data_all[site_data_all['pump_id'] == selected_pump].reset_index(drop=True)
        st.divider()
        
        selected_idx = st.number_input(f"Inspect Row Index (0 - {len(site_data)-1})", 0, len(site_data)-1, len(site_data)-1)
        record = site_data.iloc[selected_idx]

        # --- ALERT LOGIC & POPUPS ---
        alerts = []
        if record['vibration_mm_s'] > 4.5: alerts.append(("High Vibration", "📳", "warning"))
        if record['temp_c'] > 70: alerts.append(("High Temperature", "🔥", "warning"))
        if record['pressure_bar'] < 3.0: alerts.append(("Low Pressure", "💧", "warning"))
        if record['efficiency_pct'] < 70: alerts.append(("System Degradation", "📉", "error"))
        if record['current_a'] > 26: alerts.append(("Abnormal Loading", "⚡", "warning"))
        if abs(record['vibration_zscore']) > 3: alerts.append(("Statistical Anomaly", "⚠️", "info"))

        for msg, icon, _ in alerts:
            st.toast(f"{msg} Detected!", icon=icon)

        st.subheader(f"Current Analysis: Pump {selected_pump}")
        
        # Display Alerts as Cards
        if alerts:
            al_cols = st.columns(len(alerts))
            for i, (msg, icon, type) in enumerate(alerts):
                with al_cols[i]:
                    if type == "error": st.error(f"{icon} {msg}")
                    elif type == "warning": st.warning(f"{icon} {msg}")
                    else: st.info(f"{icon} {msg}")
        else:
            st.success("✅ Pump operating within nominal parameters.")

        st.info(f"**Reported Fault:** {record['fault_type']}")

        r1 = st.columns(4)
        r2 = st.columns(4)
        with r1[0]: st.plotly_chart(create_gauge(record['health_score'], "HEALTH SCORE", is_health=True), use_container_width=True)
        with r1[1]: st.plotly_chart(create_gauge(record['flow_m3h'], "FLOW (m³/h)", 500, bar_color="#00CED1"), use_container_width=True)
        with r1[2]: st.plotly_chart(create_gauge(record['pressure_bar'], "PRESSURE (Bar)", 15, bar_color="#1E90FF"), use_container_width=True)
        with r1[3]: st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", 100, bar_color="#00cc96"), use_container_width=True)
        with r2[0]: st.plotly_chart(create_gauge(record['temp_c'], "TEMP (°C)", 120, bar_color="#ff4b4b"), use_container_width=True)
        with r2[1]: st.plotly_chart(create_gauge(record['vibration_mm_s'], "VIBRATION (mm/s)", 10, bar_color="gray"), use_container_width=True)
        with r2[2]: st.plotly_chart(create_gauge(record['current_a'], "CURRENT (A)", 50, bar_color="#800080"), use_container_width=True)
        with r2[3]: 
            util = min((record['current_a'] / 35) * 100, 100)
            st.plotly_chart(create_gauge(util, "UTILIZATION %", 100, bar_color="#FFA500"), use_container_width=True)

    with tab2:
        st.header("📊 Quad-Pump Fleet Analytics")
        comp_site = st.selectbox("Select Plant for Trends", sorted(df['site'].unique()), key="qsite")
        site_pumps = sorted(df[df['site'] == comp_site]['pump_id'].unique())
        selected_4 = st.multiselect("Select Pumps", site_pumps, default=site_pumps[:4])

        if selected_4:
            quad_df = df[(df['site'] == comp_site) & (df['pump_id'].isin(selected_4))].copy()
            quad_df['idx'] = range(len(quad_df))
            
            metrics = ['flow_m3h', 'pressure_bar', 'vibration_mm_s', 'temp_c', 'current_a', 'efficiency_pct', 'health_score']
            m_cols = st.columns(2)
            for i, metric in enumerate(metrics):
                with m_cols[i % 2]:
                    fig = px.line(quad_df, x='idx', y=metric, color='pump_id', title=f"TREND: {metric.upper()}", template="plotly_dark", height=350)
                    
                    # HIGHLIGHT DEGRADATION (Health < 70)
                    degraded = quad_df[quad_df['health_score'] < 70]
                    if not degraded.empty:
                        for d_idx in degraded['idx'].unique():
                            fig.add_vrect(x0=d_idx-0.5, x1=d_idx+0.5, fillcolor="red", opacity=0.1, line_width=0)
                    
                    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
