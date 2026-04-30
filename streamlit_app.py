import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURATION ---
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
    # --- DATA ENGINE ---
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # Calculations
    window = 10
    df['rolling_mean'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).mean())
    df['rolling_std'] = df.groupby('site')['vibration_mm_s'].transform(lambda x: x.rolling(window=window).std())
    df['z_score'] = (df['vibration_mm_s'] - df['rolling_mean']) / df['rolling_std'].replace(0, np.nan)
    df['z_score'] = df['z_score'].fillna(0)

    # --- TABS NAVIGATION ---
    tab1, tab2 = st.tabs(["🔍 Live Diagnostic Center", "📊 Pump ID Comparison"])

    # --- PAGE 1: LIVE DIAGNOSTIC CENTER ---
    with tab1:
        st.sidebar.header("🕹️ Control Room")
        selected_site = st.sidebar.selectbox("Select Plant Location", df['site'].unique())
        site_data = df[df['site'] == selected_site].reset_index(drop=True)
        
        st.header(f"📊 Live Diagnostic: {selected_site}")
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

        report_text = f"PREDICTIVE MAINTENANCE REPORT\n----------------------------\nPlant Location: {selected_site}\nRecord Index: {selected_idx}\nPump ID: {record.get('pump_id', 'Unknown')}\n\n1. CURRENT CONDITION:\n   Health Score: {record['health_score']}%\n   Efficiency: {record['efficiency_pct']}%\n\n2. DETECTED ANOMALIES:\n   {', '.join(active_issues) if active_issues else 'None'}\n\n3. LIKELY FAULT PROGRESSION:\n   {fault}\n\n4. MAINTENANCE RECOMMENDATION:\n   {rec}\n----------------------------"
        st.text_area("Analysis Summary", report_text, height=250)
        st.download_button(label="📥 Download Report", data=report_text, file_name=f"Report_{selected_site}_{selected_idx}.txt")

        st.divider()
        st.subheader(f"📋 Site History: {selected_site}")
        st.dataframe(site_data, use_container_width=True)

    # --- PAGE 2: PUMP COMPARISON ---
    with tab2:
        st.header("📊 Multi-Pump Performance Comparison")
        
        # Selection filters
        st.sidebar.divider()
        st.sidebar.header("⚖️ Comparison Filters")
        comp_site = st.sidebar.selectbox("Select Site for Comparison", df['site'].unique(), key="comp_site")
        
        # Get unique pump IDs for that site
        available_pumps = df[df['site'] == comp_site]['pump_id'].unique()
        selected_pumps = st.sidebar.multiselect("Select Pump IDs to Compare", available_pumps, default=available_pumps[:2])

        if not selected_pumps:
            st.warning("Please select at least one Pump ID from the sidebar.")
        else:
            # Filter data for selected site and pumps
            comp_df = df[(df['site'] == comp_site) & (df['pump_id'].isin(selected_pumps))].reset_index()
            
            # Create a facet plot for all major parameters
            metrics_to_plot = ['vibration_mm_s', 'temp_c', 'current_a', 'pressure_bar', 'flow_m3h', 'efficiency_pct']
            
            # Melt data for long-format plotting
            melted_df = comp_df.melt(id_vars=['index', 'pump_id'], value_vars=metrics_to_plot, 
                                     var_name='Parameter', value_name='Value')

            fig_comp = px.line(
                melted_df, 
                x='index', 
                y='Value', 
                color='pump_id', 
                facet_row='Parameter',
                height=1000,
                template="plotly_dark",
                labels={'index': 'Time Step', 'Value': 'Measurement', 'pump_id': 'Pump ID'},
                title=f"Comparative Trends at {comp_site}"
            )

            # Improve layout: allow independent Y axes for different parameters
            fig_comp.update_yaxes(matches=None)
            fig_comp.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            
            st.plotly_chart(fig_comp, use_container_width=True)

            # Statistics Table
            st.subheader("📈 Aggregated Comparison (Averages)")
            stats_df = comp_df.groupby('pump_id')[metrics_to_plot].mean().round(2)
            st.table(stats_df)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
