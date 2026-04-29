import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Multi-Alert Intelligence System", layout="wide")

# --- ENHANCED GAUGE FUNCTION ---
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
    # 1. LOAD DATA
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # --- 2. SIDEBAR NAVIGATION ---
    st.sidebar.header("🕹️ Control Room")
    selected_site = st.sidebar.selectbox("Select Plant Location", df['site'].unique())
    site_data = df[df['site'] == selected_site].reset_index(drop=True)
    
    # --- 3. INDEX SELECTION ---
    st.header(f"📊 Live Diagnostic: {selected_site}")
    max_idx = len(site_data) - 1
    selected_idx = st.number_input(f"Inspect Data Point (Range: 0 - {max_idx})", 
                                   min_value=0, max_value=max_idx, value=max_idx)
    
    record = site_data.iloc[selected_idx]

    # --- 4. MULTI-ALERT STACKING LOGIC ---
    st.subheader("🚨 Active Alerts Center")
    
    active_issues = 0

    # TEMP ALERT (RED)
    if record['temp_c'] > 70:
        st.error(f"🔴 **CRITICAL TEMP:** Overheat detected ({record['temp_c']}°C).")
        st.toast("Temperature Critical!", icon="🔥")
        active_issues += 1

    # VIBRATION ALERT (BLACK) - FIXED KEYWORD ARGUMENT HERE
    if record['vibration_mm_s'] > 4.5:
        st.markdown(
            f'<div style="background-color:black;color:white;padding:12px;margin-bottom:10px;border-radius:8px;border-left: 10px solid #ff4b4b;">'
            f'⚫ <b>VIBRATION WARNING:</b> Abnormal movement ({record["vibration_mm_s"]} mm/s).</div>', 
            unsafe_allow_html=True
        )
        st.toast("Vibration Detected!", icon="📳")
        active_issues += 1

    # EFFICIENCY ALERT (YELLOW)
    if record['efficiency_pct'] < 70:
        st.warning(f"🟡 **EFFICIENCY LOSS:** Pump performing at {record['efficiency_pct']}%.")
        st.toast("Efficiency Drop!", icon="📉")
        active_issues += 1

    # PRESSURE ALERT (BLUE)
    if record['pressure_bar'] < 3.0:
        st.info(f"🔵 **LOW PRESSURE:** System pressure dropped to {record['pressure_bar']} bar.")
        st.toast("Pressure Low!", icon="💧")
        active_issues += 1

    # CURRENT ALERT (PURPLE) - FIXED KEYWORD ARGUMENT HERE
    if record['current_a'] > 26:
        st.markdown(
            f'<div style="background-color:purple;color:white;padding:12px;margin-bottom:10px;border-radius:8px;border-left: 10px solid #ffffff;">'
            f'🟣 <b>ABNORMAL LOADING:</b> Motor drawing {record["current_a"]} A.</div>', 
            unsafe_allow_html=True
        )
        st.toast("Electrical Load High!", icon="⚡")
        active_issues += 1

    if active_issues == 0:
        st.success(f"✅ All systems at {selected_site} (Index {selected_idx}) are normal.")

    # --- 5. ROUND GAUGE DASHBOARD (6 GAUGES) ---
    st.divider()
    
    utilization_val = min((record['current_a'] / 35) * 100, 100)
    
    r1c1, r1c2, r1c3 = st.columns(3)
    r2c1, r2c2, r2c3 = st.columns(3)

    with r1c1:
        st.plotly_chart(create_gauge(record['health_score'], "HEALTH STATUS %", is_health=True), use_container_width=True)
    with r1c2:
        st.plotly_chart(create_gauge(record['efficiency_pct'], "EFFICIENCY %", bar_color="#ffa500"), use_container_width=True)
    with r1c3:
        st.plotly_chart(create_gauge(utilization_val, "UTILIZATION %", bar_color="#800080"), use_container_width=True)
    with r2c1:
        st.plotly_chart(create_gauge(record['temp_c'], "TEMPERATURE °C", 100, bar_color="#ff4b4b"), use_container_width=True)
    with r2c2:
        st.plotly_chart(create_gauge(record['pressure_bar'], "PRESSURE BAR", 10, bar_color="#1E90FF"), use_container_width=True)
    with r2c3:
        st.plotly_chart(create_gauge(record['vibration_mm_s'], "VIBRATION mm/s", 10, bar_color="black"), use_container_width=True)

    # --- 6. DATA TABLE ---
    st.divider()
    st.subheader(f"📋 Site History: {selected_site}")
    st.dataframe(site_data, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
