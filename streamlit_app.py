import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Plant Intelligence System", layout="wide")

# --- GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False, bar_color="#31333F"):
    steps = [
        {'range': [0, 50], 'color': "#ff4b4b"}, 
        {'range': [50, 80], 'color': "#ffa500"}, 
        {'range': [80, 100], 'color': "#00cc96"}
    ] if is_health else []
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(value, 2),
        title={'text': title, 'font': {'size': 15}},
        gauge={
            'axis': {'range': [0, max_val]}, 
            'bar': {'color': bar_color}, 
            'steps': steps
        }
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=40, b=10))
    return fig

try:
    # 1. LOAD DATA
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # --- 2. SIDEBAR NAVIGATION ---
    st.sidebar.header("📍 Control Panel")
    selected_site = st.sidebar.selectbox("Select Plant", df['site'].unique())
    site_data = df[df['site'] == selected_site].reset_index(drop=True)
    
    # --- 3. INDEX SELECTION ---
    st.header(f"🔍 System Diagnostics: {selected_site}")
    max_idx = len(site_data) - 1
    selected_idx = st.number_input(f"Enter Index Number (0 to {max_idx})", 
                                   min_value=0, max_value=max_idx, value=max_idx)
    
    record = site_data.iloc[selected_idx]

    # --- 4. MULTIPLE ALERT SECTION (Appears 1 by 1) ---
    st.subheader("⚠️ Active Alerts")
    
    # Track if any issue was found
    has_issue = False

    # Temperature Alert (Red)
    if record['temp_c'] > 70:
        st.error(f"🔴 **TEMP ALERT:** Temperature reached {record['temp_c']}°C at {selected_site}")
        st.toast("Temperature Critical!", icon="🔴")
        has_issue = True

    # Vibration Alert (Black)
    if record['vibration_mm_s'] > 4.5:
        st.markdown(f'<div style="background-color:black;color:white;padding:10px;margin-bottom:10px;border-radius:5px;">⚫ <b>VIBRATION ALERT:</b> {record["vibration_mm_s"]} mm/s detected.</div>', unsafe_content_type=True)
        st.toast("Vibration Warning!", icon="⚫")
        has_issue = True

    # Efficiency Alert (Yellow)
    if record['efficiency_pct'] < 70:
        st.warning(f"🟡 **EFFICIENCY ALERT:** Performance dropped to {record['efficiency_pct']}%")
        st.toast("Efficiency Low!", icon="🟡")
        has_issue = True

    # Pressure Alert (Blue)
    if record['pressure_bar'] < 3.0:
        st.info(f"🔵 **PRESSURE ALERT:** Low pressure detected ({record['pressure_bar']} bar)")
        st.toast("Pressure Low!", icon="🔵")
        has_issue = True

    # Current Alert (Purple)
    if record['current_a'] > 26:
        st.markdown(f'<div style="background-color:purple;color:white;padding:10px;margin-bottom:10px;border-radius:5px;">🟣 <b>LOADING ALERT:</b> High current draw ({record["current_a"]} A)</div>', unsafe_content_type=True)
        st.toast("Current Spike!", icon="🟣")
        has_issue = True

    if not has_issue:
        st.success(f"✅ All systems normal for {selected_site} at index {selected_idx}.")

    # --- 5. GAUGES (6 TOTAL) ---
    st.divider()
    
    # Calculate Utilization (Example: Current relative to a max of 35A)
    utilization = (record['current_a'] / 35) * 100
    
    g_col1, g_col2, g_col3 = st.columns(3)
    g_col4, g_col5, g_col6 = st.columns(3)

    with g_col1:
        st.plotly_chart(create_gauge(record['health_score'], "Health State %", is_health=True), use_container_width=True)
    with g_col2:
        st.plotly_chart(create_gauge(record['efficiency_pct'], "Efficiency %", bar_color="yellow"), use_container_width=True)
    with g_col3:
        st.plotly_chart(create_gauge(utilization, "Utilization %", bar_color="orange"), use_container_width=True)
    with g_col4:
        st.plotly_chart(create_gauge(record['temp_c'], "Temperature °C", 100, bar_color="red"), use_container_width=True)
    with g_col5:
        st.plotly_chart(create_gauge(record['pressure_bar'], "Pressure Bar", 10, bar_color="blue"), use_container_width=True)
    with g_col6:
        st.plotly_chart(create_gauge(record['vibration_mm_s'], "Vibration mm/s", 10, bar_color="black"), use_container_width=True)

    # --- 6. DATA LOG ---
    st.divider()
    st.subheader(f"📊 Raw Data Log: {selected_site}")
    st.dataframe(site_data)

except Exception as e:
    st.error(f"Error: {e}")
