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
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()
    df['pump_id'] = df['pump_id'].astype(str).str.strip()
    df['site'] = df['site'].astype(str).str.strip()

    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)

    tab1, tab2 = st.tabs(["🔍 Live Diagnostic Center", "📊 Quad-Pump Fleet Comparison"])

    with tab1:
        st.header("🔍 Global Asset Diagnosis")
        
        col_plant, col_pump = st.columns(2)
        with col_plant:
            selected_site = st.selectbox("📍 Select Plant Location", sorted(df['site'].unique()), key="live_site_select")
        
        site_data_all = df[df['site'] == selected_site].reset_index(drop=True)
        
        with col_pump:
            available_pumps_live = sorted(site_data_all['pump_id'].unique())
            selected_pump_live = st.selectbox("⛽ Select Specific Pump ID", available_pumps_live)
            
        site_data = site_data_all[site_data_all['pump_id'] == selected_pump_live].reset_index(drop=True)
        
        st.divider()
        
        max_idx = len(site_data) - 1
        selected_idx = st.number_input(f"Inspect CSV Index (Range: 0 - {max_idx})", 
                                       min_value=0, max_value=max_idx, value=max_idx)
        
        record = site_data.iloc[selected_idx]

        st.subheader(f"Status for Pump {selected_pump_live} (Index {selected_idx})")
        st.info(f"**Current Fault Type:** {record['fault_type']}")

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
            util = min((record['current_a'] / 40) * 100, 100)
            st.plotly_chart(create_gauge(util, "UTILIZATION %", 100, bar_color="#FFA500"), use_container_width=True)

        st.divider()
        st.subheader("🚨 Logic Alerts")
        if record['health_score'] < 70: st.error(f"Low Health: {record['health_score']}%")
        if record['temp_c'] > 80: st.warning(f"High Temperature: {record['temp_c']}°C")
        if record['vibration_mm_s'] > 5: st.warning(f"High Vibration: {record['vibration_mm_s']} mm/s")

    with tab2:
        st.header("📊 Quad-Pump Fleet Analytics")
        comp_site = st.selectbox("Select Plant for Trends", sorted(df['site'].unique()), key="quad_site_select")
        site_pumps = sorted(df[df['site'] == comp_site]['pump_id'].unique())
        
        selected_4 = st.multiselect("Select Pumps to Compare", site_pumps, default=site_pumps[:4])

        if selected_4:
            quad_df = df[(df['site'] == comp_site) & (df['pump_id'].isin(selected_4))].copy()
            quad_df['csv_index'] = quad_df.index
            
            metrics = ['flow_m3h', 'pressure_bar', 'vibration_mm_s', 'temp_c', 'current_a', 'efficiency_pct', 'health_score']
            
            m_cols = st.columns(2)
            for i, metric in enumerate(metrics):
                with m_cols[i % 2]:
                    fig = px.line(quad_df, x='csv_index', y=metric, color='pump_id',
                                 title=f"TREND: {metric.upper()}",
                                 labels={'csv_index': 'CSV Row Index'},
                                 template="plotly_dark", height=300)
                    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
