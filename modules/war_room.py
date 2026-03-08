import streamlit as st
import pydeck as pdk
import pandas as pd
import requests
import yfinance as yf
import numpy as np

# Cache pentru radarele de aviație
@st.cache_data(ttl=60)
def get_live_flights():
    url = "https://opensky-network.org/api/states/all"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            states = data.get('states', [])
            if states:
                df = pd.DataFrame(states, columns=[
                    "icao24", "callsign", "origin_country", "time_position",
                    "last_contact", "longitude", "latitude", "baro_altitude",
                    "on_ground", "velocity", "true_track", "vertical_rate",
                    "sensors", "geo_altitude", "squawk", "spi", "position_source"
                ])
                df = df.dropna(subset=['longitude', 'latitude', 'velocity', 'true_track'])
                df['callsign'] = df['callsign'].astype(str).str.strip()
                df['callsign'] = df['callsign'].replace('', 'UNKNOWN')
                df['name'] = df['callsign']
                df['type'] = "Aircraft"
                df['info'] = df['origin_country']
                
                df = df.sample(min(4000, len(df)))
                
                # Calculăm proiecția pt toate, dar o vom randa doar pe cea selectată
                timp_proiectie = 1800 # Proiectăm 30 minute în viitor
                df['target_lon'] = df['longitude'] + (df['velocity'] * timp_proiectie * np.sin(np.radians(df['true_track']))) / (111320 * np.cos(np.radians(df['latitude'])))
                df['target_lat'] = df['latitude'] + (df['velocity'] * timp_proiectie * np.cos(np.radians(df['true_track']))) / 110540
                
                return df
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def generate_maritime_fleet():
    ships = []
    
    # 1. CHOKEPOINTS (Aglomerații la strâmtori)
    hubs = [
        {"lat": 30.58, "lon": 32.26, "spread": 0.4, "count": 60, "info": "Suez Transit"},
        {"lat": 9.14, "lon": -79.69, "spread": 0.3, "count": 50, "info": "Panama Transit"},
        {"lat": 4.0, "lon": 100.0, "spread": 1.5, "count": 90, "info": "Malacca Transit"},
        {"lat": 26.56, "lon": 56.25, "spread": 0.6, "count": 60, "info": "Hormuz Transit"}
    ]
    for hub in hubs:
        lats = np.random.normal(hub["lat"], hub["spread"], hub["count"])
        lons = np.random.normal(hub["lon"], hub["spread"], hub["count"])
        for lat, lon in zip(lats, lons):
            ships.append({"latitude": lat, "longitude": lon, "name": f"Vessel-{np.random.randint(100, 999)}", "type": "Chokepoint Traffic", "info": hub["info"]})

    # 2. OPEN OCEAN LANES (Trafic global pe mări)
    lanes = [
        {"start": (40.0, -70.0), "end": (50.0, -10.0), "count": 120, "noise": 1.5, "name": "North Atlantic Route"},
        {"start": (34.0, -120.0), "end": (30.0, 130.0), "count": 180, "noise": 2.5, "name": "Trans-Pacific Route"},
        {"start": (5.0, 95.0), "end": (15.0, 60.0), "count": 100, "noise": 1.0, "name": "Indian Ocean Route"},
        {"start": (-25.0, -40.0), "end": (-35.0, 15.0), "count": 70, "noise": 1.5, "name": "South Atlantic Route"},
        {"start": (-35.0, 20.0), "end": (-5.0, 105.0), "count": 90, "noise": 2.0, "name": "Cape to Asia Route"}
    ]
    for lane in lanes:
        s_lat, s_lon = lane["start"]
        e_lat, e_lon = lane["end"]
        # Interpolare liniară cu zgomot (să nu fie pe o linie perfect dreaptă)
        lats = np.linspace(s_lat, e_lat, lane["count"]) + np.random.normal(0, lane["noise"], lane["count"])
        lons = np.linspace(s_lon, e_lon, lane["count"]) + np.random.normal(0, lane["noise"], lane["count"])
        for lat, lon in zip(lats, lons):
            ships.append({"latitude": lat, "longitude": lon, "name": f"Cargo-{np.random.randint(1000, 9999)}", "type": "Open Ocean Transit", "info": lane["name"]})

    return pd.DataFrame(ships)

def get_global_infrastructure():
    return pd.DataFrame([
        {"name": "Suez Canal", "lat": 30.5852, "lon": 32.2654, "type": "Chokepoint", "info": "Egypt", "color": [255, 69, 0]},
        {"name": "Strait of Hormuz", "lat": 26.5667, "lon": 56.2500, "type": "Chokepoint", "info": "Iran/Oman", "color": [255, 69, 0]},
        {"name": "Panama Canal", "lat": 9.1416, "lon": -79.6902, "type": "Chokepoint", "info": "Panama", "color": [255, 69, 0]},
        {"name": "Bab el-Mandeb", "lat": 12.5833, "lon": 43.3333, "type": "Chokepoint", "info": "Yemen", "color": [255, 69, 0]},
        {"name": "Malacca Strait", "lat": 4.0, "lon": 100.0, "type": "Chokepoint", "info": "Malaysia", "color": [255, 69, 0]},
        {"name": "Ras Tanura", "lat": 26.6425, "lon": 50.1542, "type": "Energy", "info": "Saudi Arabia", "color": [0, 255, 255]},
        {"name": "Escondida", "lat": -24.2683, "lon": -69.0664, "type": "Minerals", "info": "Chile", "color": [255, 0, 255]},
        {"name": "TSMC Fabs", "lat": 24.7738, "lon": 120.9976, "type": "Tech", "info": "Taiwan", "color": [255, 255, 0]},
    ])

def render_war_room():
    # 1. DATE & STATE
    with st.spinner("Synchronizing with Global Arrays..."):
        flights_df = get_live_flights()
        ships_df = generate_maritime_fleet()
        chokepoints = get_global_infrastructure()

    # 2. FILTRE TACTICE & TARGET LOCK
    st.markdown("<h3 class='header-blue'>Global Geopolitical War Room</h3>", unsafe_allow_html=True)
    
    st.markdown("**Tactical Command Center:**")
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        show_aviation = st.checkbox("✈️ Aviation Radar", value=True)
        show_maritime = st.checkbox("🛳️ Maritime Fleet", value=True)
    with col_f2:
        show_infra = st.checkbox("🏭 Critical Infra", value=True)
        if st.button("📡 PING RADARS", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_f3:
        # SISTEM DE TARGET LOCK (Afișează rute)
        target_flight = None
        if show_aviation and not flights_df.empty:
            callsigns = ["NONE"] + sorted(flights_df[flights_df['callsign'] != "UNKNOWN"]['callsign'].dropna().unique().tolist())
            target_flight = st.selectbox("🎯 TARGET LOCK (Select flight to map route vector):", callsigns)

    # 3. PYDECK LAYERS
    layers = []

    if show_infra:
        infra_layer = pdk.Layer(
            "ScatterplotLayer", data=chokepoints,
            get_position="[lon, lat]", get_color="color",
            get_radius=85000, pickable=True, opacity=0.7, filled=True,
        )
        layers.append(infra_layer)

    if show_maritime and not ships_df.empty:
        ship_layer = pdk.Layer(
            "ScatterplotLayer", data=ships_df,
            get_position="[longitude, latitude]",
            get_color=[255, 140, 0, 180], # Orange pentru nave
            get_radius=25000, pickable=True
        )
        layers.append(ship_layer)

    if show_aviation and not flights_df.empty:
        # Desenăm TOATE avioanele
        flight_layer = pdk.Layer(
            "ScatterplotLayer", data=flights_df,
            get_position="[longitude, latitude]",
            get_color=[0, 255, 0, 200], # Verde
            get_radius=15000, pickable=True
        )
        layers.append(flight_layer)
        
        # Desenăm RUTA doar pentru zborul Targetat!
        if target_flight and target_flight != "NONE":
            target_data = flights_df[flights_df['callsign'] == target_flight]
            if not target_data.empty:
                route_layer = pdk.Layer(
                    "LineLayer", data=target_data,
                    get_source_position="[longitude, latitude]",
                    get_target_position="[target_lon, target_lat]",
                    get_color=[255, 0, 0, 255], # Roșu agresiv pentru target lock
                    get_width=5000, pickable=False
                )
                layers.append(route_layer)
                
                # Facem Highlight și pe punctul avionului târgetat
                highlight_layer = pdk.Layer(
                    "ScatterplotLayer", data=target_data,
                    get_position="[longitude, latitude]",
                    get_color=[255, 255, 255, 255], # Alb pentru a ieși în evidență
                    get_radius=30000, pickable=False
                )
                layers.append(highlight_layer)

    # 4. RANDAREA HĂRȚII
    # Dacă avem un target, centrăm camera pe el. Dacă nu, o lăsăm globală.
    if target_flight and target_flight != "NONE" and not target_data.empty:
        view_state = pdk.ViewState(latitude=target_data.iloc[0]['latitude'], longitude=target_data.iloc[0]['longitude'], zoom=5, pitch=45, bearing=0)
    else:
        view_state = pdk.ViewState(latitude=20.0, longitude=10.0, zoom=1.5, pitch=35, bearing=0)

    tooltip_html = {
        "html": "<b style='color:#00FFFF'>{name}</b><br/><b>Type:</b> {type}<br/><b>Detail:</b> {info}",
        "style": {"backgroundColor": "#0A0A0A", "color": "white", "border": "1px solid #333333"}
    }

    r = pdk.Deck(layers=layers, initial_view_state=view_state, map_style="mapbox://styles/mapbox/dark-v10", tooltip=tooltip_html)
    st.pydeck_chart(r, use_container_width=True)

    # 5. DATA TABLES
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h5 class='header-blue'>Live Airspace Feed</h5>", unsafe_allow_html=True)
        if not flights_df.empty:
            st.dataframe(flights_df[['callsign', 'origin_country', 'velocity', 'true_track']].head(10), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("<h5 class='header-blue'>Maritime Transport Grid</h5>", unsafe_allow_html=True)
        if not ships_df.empty:
            st.dataframe(ships_df[['name', 'info']].sample(10), use_container_width=True, hide_index=True)