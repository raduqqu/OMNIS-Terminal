import streamlit as st
import time
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & AESTHETICS
# ==========================================
st.set_page_config(
    page_title="OMNIS | Global Intelligence Terminal",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bloomberg Dark Theme CSS Injection
def inject_custom_css():
    st.markdown("""
        <style>
        .stApp { background-color: #000000; color: #FFFFFF; }
        [data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #333333; }
        .metric-gain { color: #00FF00 !important; font-weight: bold; }
        .alert-orange { color: #FF8C00 !important; font-weight: bold; }
        .header-blue { color: #00FFFF !important; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

def manage_refresh():
    if st.sidebar.button("⚠️ FORCE REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.sidebar.success("Cache cleared.")
        time.sleep(1)
        st.rerun()
    st.sidebar.markdown(f"<small style='color:#888;'>Last Sync: {datetime.now().strftime('%H:%M:%S')} UTC</small>", unsafe_allow_html=True)

# ==========================================
# MAIN APPLICATION ROUTING
# ==========================================
def main():
    inject_custom_css()
    
    st.sidebar.markdown("<h2 class='header-blue'>OMNIS TERMINAL</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    manage_refresh()
    st.sidebar.markdown("---")

    menu_options = [
        "📈 Markets (Financial Engine)", 
        "🌍 World Map (Geopolitics)", 
        "🛰️ Satellite Intel", 
        "🧠 AI Sentiment", 
        "📡 Hardware Hub"
    ]
    selection = st.sidebar.radio("NAVIGATION", menu_options)

    # ==========================================
    # ⚖️ LEGAL & DATA SOURCES (CREDITS)
    # ==========================================
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚖️ Data Sources & Legal"):
        st.markdown("""
        <div style='font-size: 0.75rem; color: #AAAAAA; line-height: 1.4;'>
        <b>OMNIS Terminal</b><br>
        Proprietary research tool by <b>Rodiss Capital</b>.<br><br>
        <b>Data Providers:</b><br>
        • Aviation: <a href='https://opensky-network.org' style='color:#00FFFF; text-decoration:none;'>OpenSky Network</a><br>
        • Satellites: <a href='https://www.esri.com' style='color:#00FFFF; text-decoration:none;'>Esri World Imagery</a><br>
        • Markets: <a href='https://finance.yahoo.com' style='color:#00FFFF; text-decoration:none;'>Yahoo Finance API</a><br>
        • Radio Feed: <a href='https://www.radio-browser.info' style='color:#00FFFF; text-decoration:none;'>Radio Browser API</a><br>
        • Mapping: <a href='https://www.openstreetmap.org' style='color:#00FFFF; text-decoration:none;'>OpenStreetMap</a><br><br>
        <i><b>Disclaimer:</b> Aggregated data is for informational and research purposes only. Not intended as direct trading advice. Rodiss Capital assumes no liability for market actions taken based on this tool.</i>
        </div>
        """, unsafe_allow_html=True)

    # --- ROUTING LOGIC ---
    if selection == "📈 Markets (Financial Engine)":
        st.markdown("<h1 class='header-blue'>Financial Engine</h1>", unsafe_allow_html=True)
        try:
            from modules.finance import render_finance_dashboard
            render_finance_dashboard()
        except Exception as e:
            st.error(f"Module error: {e}")
            st.info("Check if 'modules/finance.py' exists.")
        
    elif selection == "🌍 World Map (Geopolitics)":
        try:
            from modules.war_room import render_war_room
            render_war_room()
        except Exception as e:
            st.error(f"Module error: {e}")
            st.info("Check if 'modules/war_room.py' exists.")
        
    elif selection == "🛰️ Satellite Intel":
        try:
            from modules.satellite import render_satellite_intel
            render_satellite_intel()
        except Exception as e:
            st.error(f"Module error: {e}")
            st.info("Check if 'modules/satellite.py' exists and folium is installed.")
        
    elif selection == "🧠 AI Sentiment":
        try:
            from modules.sentiment import render_ai_sentiment
            render_ai_sentiment()
        except Exception as e:
            st.error(f"Module error: {e}")
            st.info("Check if 'modules/sentiment.py' exists.")
        
    elif selection == "📡 Hardware Hub":
        try:
            from modules.hardware import render_hardware_hub
            render_hardware_hub()
        except Exception as e:
            st.error(f"Module error: {e}")
            st.info("Check if 'modules/hardware.py' exists.")

if __name__ == "__main__":
    main()