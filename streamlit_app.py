import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Pump Health Intelligence", layout="wide")

# --- GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False):
    if is_health:
        steps = [
            {'range': [0, 50], 'color': "#ff4b4b"}, 
            {'range': [50, 80], 'color': "#ffa500"}, 
            {'range': [80, 100], 'color': "#00cc96"}
        ]
    else:
        steps = [{'range': [0, max_val], 'color': "#f0f2f6"}]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 2),
        title={'text': title, 'font': {'size': 18}},
        gauge={'axis': {'range': [0, max_val]}, 'bar': {'color': "#31333F"}, 'steps': steps}
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# --- STYLING FUNCTION FOR TABLE ---
def style_incidents(row):
    styles = [''] * len(row)
    # Vibration > 4.5 -> Black background, White text
    if row['vibration_mm_s'] > 4.5:
        styles[row.index.get_loc('vibration_mm_s')] = 'background-color: black; color: white'
    # Temp > 70 -> Red background
    if row['temp_c'] > 70:
        styles[row.index.get_loc('temp_c')] = 'background-color: red; color: white'
    # Efficiency < 70 -> Yellow background
    if row['efficiency_pct'] < 70:
        styles[row.index.get_loc('efficiency_pct')] = 'background-color: yellow; color: black'
    # Pressure < 3 -> Blue (Different color)
    if row['pressure_bar'] < 3.0:
        styles[row.index.get_loc('pressure_bar')] = 'background-color: #1E90FF; color: white'
    # Current > 26 -> Purple (Different color)
    if row['current_a'] > 26:
        styles[row.index.get_loc('current_a')] = 'background-color: #800080; color: white'
    return styles

st.title("🛡️ Plant Condition Monitoring System")

try:
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    st.sidebar.header("Filter by Location")
    selected_site = st.sidebar.selectbox("Select Plant", df['site'].unique())
    site_data = df[df['site'] == selected_site]
    latest = site_data.iloc[-1]

    # Gauges
    col1, col2, col3 = st.columns(3)
    with col1: st.plotly_chart(create_gauge(latest['health_score'], "Health %", is_health=True), use_container_width=True)
    with col2: st.plotly_chart(create_gauge(latest['efficiency_pct'], "Efficiency %"), use_container_width=True)
    with col3: st.plotly_chart(create_gauge(latest.get('voltage', 415), "Voltage (V)", max_val=500), use_container_width=True)

    st.divider()

    # --- COLORED INCIDENT REPORT ---
    st.subheader(f"📋 Incident Report: {selected_site}")
    
    # Filter for any anomaly
    incidents = site_data[
        (site_data['vibration_mm_s'] > 4.5) | 
        (site_data['temp_c'] > 70) | 
        (site_data['pressure_bar'] < 3.0) | 
        (site_data['efficiency_pct'] < 70) | 
        (site_data['current_a'] > 26)
    ].copy()

    if not incidents.empty:
        # Define columns to show
        display_cols = ['timestamp', 'pump_id', 'vibration_mm_s', 'temp_c', 'pressure_bar', 'efficiency_pct', 'current_a']
        
        # Apply the style function
        styled_df = incidents[display_cols].style.apply(style_incidents, axis=1)
        
        # Display styled table
        st.dataframe(styled_df, use_container_width=True)
        
        st.info("Legend: ⚫ Vibration Fail | 🔴 Overheat | 🟡 Efficiency Drop | 🔵 Pressure Drop | 🟣 Current Spike")
    else:
        st.success(f"✅ No incidents detected for {selected_site}.")

except Exception as e:
    st.error(f"Error: {e}")
