import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Bază de date cu ținte strategice
STRATEGIC_TARGETS = {
    "Manual Input / Map Click": [0.0, 0.0],
    "TSMC Fabs (Taiwan Semiconductors)": [24.7738, 120.9976],
    "Suez Canal (Maritime Chokepoint)": [30.5852, 32.2654],
    "Area 51 (Groom Lake, USA)": [37.2370, -115.8080],
    "Kremlin (Moscow, Russia)": [55.7520, 37.6175],
    "Natanz Nuclear Facility (Iran)": [33.7250, 51.7289],
    "Yulin Naval Base (Submarines, China)": [18.2254, 109.5503],
    "Escondida Copper Mine (Chile)": [-24.2683, -69.0664]
}

# Inițializăm "creierul" aplicației ca să nu uite unde suntem când dăm refresh
def init_satellite_state():
    if "sat_lat" not in st.session_state:
        st.session_state.sat_lat = 48.8584 # Default Paris
    if "sat_lon" not in st.session_state:
        st.session_state.sat_lon = 2.2945
    if "sat_zoom" not in st.session_state:
        st.session_state.sat_zoom = 15

# Funcție pentru a căuta orașe/locații pe glob
def geocode_location(location_name):
    try:
        # Folosim Nominatim (OpenStreetMap) complet gratuit
        geolocator = Nominatim(user_agent="omnis_terminal_v1")
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception:
        return None, None

def render_satellite_intel():
    init_satellite_state()
    
    st.markdown("<h3 class='header-blue'>🛰️ Orbital Intelligence (High-Res Optical)</h3>", unsafe_allow_html=True)
    st.markdown("Accessing sub-metric optical imagery via Esri World Imagery. **Click anywhere on the map** to instantly reposition the satellite, or search below.")
    
    st.markdown("---")
    col1, col2 = st.columns([1, 2.5]) # Harta va fi mai lată acum
    
    with col1:
        st.markdown("**1. GLOBAL SEARCH**")
        search_query = st.text_input("Enter City, Base, or Address:", placeholder="e.g. Pentagon, Tokyo, Paris")
        if st.button("🔍 LOCATE TARGET", use_container_width=True):
            if search_query:
                with st.spinner(f"Geolocating '{search_query}'..."):
                    lat, lon = geocode_location(search_query)
                    if lat and lon:
                        st.session_state.sat_lat = lat
                        st.session_state.sat_lon = lon
                        st.session_state.sat_zoom = 14
                        st.rerun() # Refresh instant ca să mutăm harta
                    else:
                        st.error("Target not found on global grid.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**2. TACTICAL PRESETS**")
        target_choice = st.selectbox("Select known strategic asset:", list(STRATEGIC_TARGETS.keys()))
        if target_choice != "Manual Input / Map Click":
            if st.button("🔒 LOCK PRESET", use_container_width=True):
                st.session_state.sat_lat = STRATEGIC_TARGETS[target_choice][0]
                st.session_state.sat_lon = STRATEGIC_TARGETS[target_choice][1]
                st.session_state.sat_zoom = 16
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**3. OPTICS CONTROL**")
        new_zoom = st.slider("Optical Zoom Level:", min_value=2, max_value=20, value=st.session_state.sat_zoom)
        if new_zoom != st.session_state.sat_zoom:
            st.session_state.sat_zoom = new_zoom
            st.rerun()

        st.info(f"📍 **Active Coordinates:**\n\nLat: `{st.session_state.sat_lat:.6f}`\n\nLon: `{st.session_state.sat_lon:.6f}`")

    with col2:
        # HARTA DE SATELIT
        m = folium.Map(
            location=[st.session_state.sat_lat, st.session_state.sat_lon],
            zoom_start=st.session_state.sat_zoom,
            tiles=None,
            control_scale=True
        )

        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(m)

        # Ținta Roșie Militară (Crosshair)
        folium.CircleMarker(
            location=[st.session_state.sat_lat, st.session_state.sat_lon],
            radius=20, color="red", weight=2, fill=False,
            popup=f"LOCKED: {st.session_state.sat_lat:.4f}, {st.session_state.sat_lon:.4f}"
        ).add_to(m)
        folium.CircleMarker(
            location=[st.session_state.sat_lat, st.session_state.sat_lon],
            radius=2, color="red", fill=True, fill_color="red"
        ).add_to(m)

        # AICI E MAGIA PENTRU CLICK: Preluăm coordonatele unde a dat userul click
        st_data = st_folium(m, width=900, height=600, returned_objects=["last_clicked"])

        # Dacă userul a dat click pe hartă, actualizăm și dăm rerun!
        if st_data and st_data.get("last_clicked"):
            clicked_lat = st_data["last_clicked"]["lat"]
            clicked_lon = st_data["last_clicked"]["lng"]
            
            # Verificăm să fie un click nou, să nu intrăm în loop
            if round(clicked_lat, 4) != round(st.session_state.sat_lat, 4) or round(clicked_lon, 4) != round(st.session_state.sat_lon, 4):
                st.session_state.sat_lat = clicked_lat
                st.session_state.sat_lon = clicked_lon
                st.rerun()