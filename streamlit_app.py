import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Plant Intelligence System", layout="wide")

# --- GAUGE FUNCTION ---
def create_gauge(value, title, max_val=100, is_health=False):
    steps = [
        {'range': [0, 50], 'color': "#ff4b4b"}, 
        {'range': [50, 80], 'color': "#ffa500"}, 
        {'range': [80, 100], 'color': "#00cc96"}
    ] if is_health else []
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(value, 2),
        title={'text': title, 'font': {'size': 16}},
        gauge={'axis': {'range': [0, max_val]}, 'bar': {'color': "#31333F"}, 'steps': steps}
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=40, b=10))
    return fig

try:
    # 1. LOAD DATA
    df = pd.read_csv("pump_multi_300_anomaly.csv")
    df = df.ffill()

    # --- 2. SIDEBAR: PLANT SELECTION ---
    st.sidebar.header("📍 Navigation")
    selected_site = st.sidebar.selectbox("Select Plant", df['site'].unique())
    site_data = df[df['site'] == selected_site].reset_index(drop=True)
    
    # --- 3. INDEX SELECTION ---
    st.header(f"🔍 Inspecting: {selected_site}")
    max_idx = len(site_data) - 1
    selected_idx = st.number_input(f"Enter Index Number to Inspect (0 to {max_idx})", 
                                   min_value=0, max_value=max_idx, value=max_idx)
    
    # Extract data for the specific chosen index
    record = site_data.iloc[selected_idx]
    pump_id = record.get('pump_id', 'N/A')

    # --- 4. ALERT SECTION (Logic based ONLY on selected index) ---
    st.subheader("⚠️ Active Alerts for Selected Index")
    
    # Define thresholds and trigger pop-ups + colored boxes
    if record['temp_c'] > 70:
        st.error(f"🔴 **CRITICAL OVERHEAT:** Temp is {record['temp_c']}°C (Limit: 70)")
        st.toast(f"Temp Alert at Index {selected_idx}", icon="🔴")

    if record['vibration_mm_s'] > 4.5:
        # Custom Black Alert Box using Markdown
        st.markdown(f'<div style="background-color:black;color:white;padding:10px;border-radius:5px;">⚫ <b>VIBRATION WARNING:</b> Vibration is {record["vibration_mm_s"]} mm/s (Limit: 4.5)</div>', unsafe_content_type=True)
        st.toast(f"Vibration Alert at Index {selected_idx}", icon="⚫")

    if record['pressure_bar'] < 3.0:
        st.info(f"🔵 **LOW PRESSURE:** Pressure is {record['pressure_bar']} bar (Limit: 3.0)")
        st.toast(f"Pressure Alert at Index {selected_idx}", icon="🔵")

    if record['efficiency_pct'] < 70:
        st.warning(f"🟡 **EFFICIENCY DEGRADATION:** Efficiency is {record['efficiency_pct']}% (Limit: 70)")
        st.toast(f"Efficiency Alert at Index {selected_idx}", icon="🟡")

    if record['current_a'] > 26:
        st.markdown(f'<div style="background-color:purple;color:white;padding:10px;border-radius:5px;">🟣 <b>ABNORMAL LOADING:</b> Current is {record["current_a"]} A (Limit: 26)</div>', unsafe_content_type=True)
        st.toast(f"Loading Alert at Index {selected_idx}", icon="🟣")

    if not (record['temp_c'] > 70 or record['vibration_mm_s'] > 4.5 or record['pressure_bar'] < 3.0 or record['efficiency_pct'] < 70 or record['current_a'] > 26):
        st.success(f"✅ Index {selected_idx} is operating within normal parameters.")

    # --- 5. ROUND GAUGE VIEWS ---
    st.divider()
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1: st.plotly_chart(create_gauge(record['health_score'], "Health %", is_health=True), use_container_width=True)
    with r2: st.plotly_chart(create_gauge(record['efficiency_pct'], "Efficiency %"), use_container_width=True)
    with r3: st.plotly_chart(create_gauge(record['temp_c'], "Temp °C", 100), use_container_width=True)
    with r4: st.plotly_chart(create_gauge(record['pressure_bar'], "Pressure Bar", 10), use_container_width=True)
    with r5: st.plotly_chart(create_gauge(record['vibration_mm_s'], "Vibration mm/s", 10), use_container_width=True)

    # --- 6. EXPORT SECTION ---
    st.divider()
    st.subheader(f"📥 Download Data for {selected_site}")
    csv = site_data.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Plant CSV", data=csv, file_name=f"{selected_site}_report.csv", mime='text/csv')
    st.dataframe(site_data)

except Exception as e:
    st.error(f"Application Error: {e}")
