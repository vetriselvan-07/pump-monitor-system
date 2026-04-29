import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Pump Health Intelligence", layout="wide")

# --- GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False):
    if is_health:
        steps = [
            {'range': [0, 50], 'color': "#ff4b4b"}, # Red
            {'range': [50, 80], 'color': "#ffa500"}, # Orange
            {'range': [80, 100], 'color': "#00cc96"} # Green
        ]
    else:
        steps = [{'range': [0, max_val], 'color': "#f0f2f6"}]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 2),
        title={'text': title, 'font': {'size': 18}},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': "#31333F"},
            'steps': steps,
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

st.title("🛡️ Plant Condition Monitoring System")

try:
    # 1. Load Data
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # 2. Sidebar: Site Selection
    st.sidebar.header("Filter by Location")
    unique_sites = df['site'].unique()
    selected_site = st.sidebar.selectbox("Select Plant", unique_sites)

    # Filter data for the selected plant
    site_data = df[df['site'] == selected_site]
    latest = site_data.iloc[-1]

    # 3. Top Row: Gauges for Latest Status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(create_gauge(latest['health_score'], "Current Health %", is_health=True), use_container_width=True)
    with col2:
        st.plotly_chart(create_gauge(latest['efficiency_pct'], "Efficiency %"), use_container_width=True)
    with col3:
        st.plotly_chart(create_gauge(latest.get('voltage', 415), "Voltage (V)", max_val=500), use_container_width=True)

    st.divider()

    # 4. INCIDENT LOG - LISTING ALL ANOMALIES FOR THE SELECTED PLANT
    st.subheader(f"📋 Incident Report: {selected_site}")
    st.write(f"The following log captures every recorded instance at **{selected_site}** that exceeded safety thresholds.")

    # Define the Anomaly Logic
    vibration_fail = site_data['vibration_mm_s'] > 4.5
    temp_fail = site_data['temp_c'] > 70
    pressure_fail = site_data['pressure_bar'] < 3.0
    efficiency_fail = site_data['efficiency_pct'] < 70
    current_fail = site_data['current_a'] > 26

    # Combine filters (OR logic: if any one is true, list the row)
    incidents = site_data[vibration_fail | temp_fail | pressure_fail | efficiency_fail | current_fail].copy()

    if not incidents.empty:
        # Add a 'Issue Type' column to explain why the row is listed
        def identify_issue(row):
            issues = []
            if row['vibration_mm_s'] > 4.5: issues.append("High Vibration")
            if row['temp_c'] > 70: issues.append("Overheat")
            if row['pressure_bar'] < 3.0: issues.append("Low Pressure")
            if row['efficiency_pct'] < 70: issues.append("Low Efficiency")
            if row['current_a'] > 26: issues.append("High Current")
            return ", ".join(issues)

        incidents['Detected_Issues'] = incidents.apply(identify_issue, axis=1)

        # Reorder columns to show the ID and Timestamp first
        cols = ['timestamp', 'pump_id', 'Detected_Issues', 'vibration_mm_s', 'temp_c', 'pressure_bar', 'efficiency_pct', 'current_a']
        st.dataframe(incidents[cols], use_container_width=True)
        
        # Download Button for the filtered Incident Report
        csv = incidents.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Incident Report as CSV",
            data=csv,
            file_name=f"{selected_site}_incident_report.csv",
            mime='text/csv',
        )
    else:
        st.success(f"✅ No incidents detected for {selected_site} based on current thresholds.")

    # 5. Trend Visualization
    st.divider()
    st.subheader("📊 Vibration & Temperature Trends")
    fig = px.line(site_data, x='timestamp', y=['vibration_mm_s', 'temp_c'], 
                 title=f"Sensor History for {selected_site}",
                 labels={"value": "Sensor Reading", "variable": "Sensor Type"})
    # Add warning lines to the chart
    fig.add_hline(y=4.5, line_dash="dot", line_color="red", annotation_text="Vibration Limit")
    fig.add_hline(y=70, line_dash="dot", line_color="orange", annotation_text="Temp Limit")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error initializing dashboard: {e}")
