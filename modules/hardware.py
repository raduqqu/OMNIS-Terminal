import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import requests

# Funcție pentru a calcula distanța dintre click-ul tău și stațiile de radio
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Raza pământului în km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@st.cache_data(ttl=3600)
def fetch_public_radios():
    """Trage Top 1000 radiouri publice globale cu coordonate GPS de pe Radio Browser API"""
    url = "https://de1.api.radio-browser.info/json/stations/search"
    params = {
        "limit": 1500, # Tragem 1500 de posturi pentru o hartă bogată
        "has_geo_info": "true",
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true"
    }
    valid_stations = []
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for s in data:
                try:
                    lat = float(s.get('geo_lat'))
                    lon = float(s.get('geo_long'))
                    # Filtrăm coordonatele invalide
                    if lat == 0.0 and lon == 0.0: continue
                    
                    valid_stations.append({
                        "name": s.get("name", "Unknown Radio").strip(),
                        "lat": lat,
                        "lon": lon,
                        "url": s.get("url_resolved", s.get("url")),
                        "country": s.get("country", "Unknown"),
                        "tags": s.get("tags", "general")
                    })
                except:
                    pass
            return valid_stations
    except Exception:
        pass
    
    # Fallback de urgență dacă pică API-ul
    return [
        {"name": "BBC Radio 1", "lat": 51.5, "lon": -0.1, "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one", "country": "UK", "tags": "pop, top40"},
        {"name": "Kiss FM Romania", "lat": 44.4268, "lon": 26.1025, "url": "https://live.kissfm.ro/kissfm.aacp", "country": "Romania", "tags": "pop, dance"}
    ]

def render_hardware_hub():
    st.markdown("<h3 class='header-blue'>📻 Global Public Radio Scanner</h3>", unsafe_allow_html=True)
    st.markdown("Live audio intercept from public web-radios worldwide. **Pan the globe and click near any green dot to tune in.**")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1.2])

    with st.spinner("Synchronizing with Global Radio Arrays..."):
        radio_stations = fetch_public_radios()

    # ==========================================
    # 1. HARTA INTERACTIVĂ (RADIO GARDEN CLONE)
    # ==========================================
    with col1:
        if "radio_lat" not in st.session_state:
            st.session_state.radio_lat = 44.4268 # Default București
            st.session_state.radio_lon = 26.1025
            
        # Folosim harta din Satelit (Esri) exact ca la Radio Garden
        m = folium.Map(
            location=[st.session_state.radio_lat, st.session_state.radio_lon],
            zoom_start=4,
            tiles=None,
            control_scale=True
        )
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Esri Satellite', overlay=False, control=True
        ).add_to(m)

        # Punem stațiile radio ca puncte mici verzi
        for station in radio_stations:
            folium.CircleMarker(
                location=[station["lat"], station["lon"]],
                radius=3, # Puncte mici ca să încapă mii pe ecran
                color="#00FF00", # Verde neon (Radio Garden style)
                fill=True,
                fill_color="#00FF00",
                fill_opacity=0.8
            ).add_to(m)

        # Cercul de tuning (Raza ta de ascultare)
        folium.CircleMarker(
            location=[st.session_state.radio_lat, st.session_state.radio_lon],
            radius=20,
            color="white",
            weight=2,
            fill=False
        ).add_to(m)
        folium.CircleMarker(
            location=[st.session_state.radio_lat, st.session_state.radio_lon],
            radius=3, color="white", fill=True, fill_color="white"
        ).add_to(m)

        # Randăm harta și prindem click-ul pe ecran
        st_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])

        if st_data and st_data.get("last_clicked"):
            clicked_lat = st_data["last_clicked"]["lat"]
            clicked_lon = st_data["last_clicked"]["lng"]
            
            if round(clicked_lat, 4) != round(st.session_state.radio_lat, 4):
                st.session_state.radio_lat = clicked_lat
                st.session_state.radio_lon = clicked_lon
                st.rerun()

    # ==========================================
    # 2. AUDIO PLAYER & STATION INFO
    # ==========================================
    with col2:
        st.markdown("<h4 class='header-blue'>📡 Live Intercept Stream</h4>", unsafe_allow_html=True)
        
        if radio_stations:
            # Găsim cel mai apropiat radio de locul unde ai dat click
            closest_station = None
            min_dist = float('inf')
            
            for station in radio_stations:
                dist = haversine(st.session_state.radio_lat, st.session_state.radio_lon, station["lat"], station["lon"])
                if dist < min_dist:
                    min_dist = dist
                    closest_station = station

            if min_dist < 500: # Dacă ești la maxim 500km de un radio
                st.success("🟢 CONNECTION ESTABLISHED")
                
                # Afișăm detaliile radioului
                st.markdown(f"**Station:** {closest_station['name']}")
                st.markdown(f"**Country:** {closest_station['country']}")
                st.markdown(f"**Genre/Tags:** `{closest_station['tags'][:50]}...`")
                
                # AUDIO PLAYER HTML (Asta îți permite să asculți direct în browser!)
                audio_html = f"""
                <div style="background-color: #111; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-top: 20px;">
                    <audio controls autoplay style="width: 100%; outline: none;">
                        <source src="{closest_station['url']}" type="audio/mpeg">
                        <source src="{closest_station['url']}" type="audio/aac">
                        <source src="{closest_station['url']}" type="audio/ogg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                
                st.info("💡 *Note: If the audio doesn't play automatically, click the Play button. Some global streams might be temporarily offline.*")
            else:
                st.error("🔴 NO SIGNAL DETECTED")
                st.markdown("You clicked in a dead zone (e.g., middle of the ocean).")
                st.markdown("👉 **Click near the green dots on the map to tune in!**")
        else:
            st.warning("Fetching radio networks...")

        st.markdown("---")
        st.markdown("#### 🌍 Geographic Coordinates")
        st.code(f"Lat: {st.session_state.radio_lat:.4f}\nLon: {st.session_state.radio_lon:.4f}", language="text")