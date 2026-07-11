import os
import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import requests
from gtts import gTTS

# OpenRouteService API key (see .env / .env.example)
ORS_API_KEY = os.getenv("ORS_API_KEY", "")

# Personal details are read from the environment so they are never committed.
EMERGENCY_PHONE = os.getenv("EMERGENCY_PHONE", "")  # e.g. 919999999999
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "0.0"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "0.0"))

# Get route info
def get_route_info(start_lat, start_lon, end_lat, end_lon):
    # foot-walking is the appropriate profile for a pedestrian navigation aid
    url = "https://api.openrouteservice.org/v2/directions/foot-walking"
    headers = {"Authorization": ORS_API_KEY}
    params = {
        "start": f"{start_lon},{start_lat}",
        "end": f"{end_lon},{end_lat}"
    }
    response = requests.get(url, headers=headers, params=params, timeout=15)
    data = response.json()

    distance_km = data["features"][0]["properties"]["segments"][0]["distance"] / 1000
    duration_min = data["features"][0]["properties"]["segments"][0]["duration"] / 60
    return round(distance_km, 2), round(duration_min, 1)

# Speak using gTTS
def speak_gtts(text, filename="voice.mp3"):
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    audio_file = open(filename, "rb")
    st.audio(audio_file.read(), format="audio/mp3")

# Main Navigation Page
def navigation_page():
    from utils import ui

    ui.hero(
        title="Navigation Assistance",
        subtitle="Find your location, set a destination and get spoken walking directions "
        "to reach it with confidence.",
        eyebrow="Location · Routing · Voice",
    )

    CURRENT_LAT, CURRENT_LON = DEFAULT_LAT, DEFAULT_LON

    if 'current_location' not in st.session_state:
        st.session_state.current_location = (CURRENT_LAT, CURRENT_LON)

    if st.button("📍  Use current location"):
        st.session_state.current_location = (CURRENT_LAT, CURRENT_LON)

    lat, lon = st.session_state.current_location
    ui.notice("info", "Your location:", f"{lat:.6f}, {lon:.6f}")

    if 'destination' not in st.session_state:
        st.session_state.destination = ""

    destination = st.text_input(
        "Enter your destination (address, place, or landmark):",
        value=st.session_state.destination,
        key="destination"
    )

    col1, col2 = st.columns(2)
    with col1:
        send_wa = st.button("📲  Send via WhatsApp", use_container_width=True)
    with col2:
        speak_button = st.button("🔊  Speak info", type="primary", use_container_width=True)

    m = folium.Map(location=[lat, lon], zoom_start=14)
    folium.Marker([lat, lon], tooltip="You are here", icon=folium.Icon(color='blue')).add_to(m)

    if send_wa:
        if not EMERGENCY_PHONE:
            st.warning("Set EMERGENCY_PHONE in your .env file to enable WhatsApp sharing.")
        else:
            message = f"This is Vision. My current location is: https://www.google.com/maps?q={lat},{lon}"
            whatsapp_url = f"https://wa.me/{EMERGENCY_PHONE}?text={message.replace(' ', '%20')}"
            st.markdown(
            f"""
            <a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
                <button style="
                    background-color:#25D366;
                    color:white;
                    padding:10px 20px;
                    border:none;
                    border-radius:5px;
                    font-size:16px;
                    display:flex;
                    align-items:center;
                    gap:10px;
                    cursor:pointer;
                ">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="20" height="20" alt="WhatsApp"/>
                    Send via WhatsApp
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    voice_output = ""

    if destination.strip() != "":
        geolocator = Nominatim(user_agent="visionai_navigation")
        dest_location = geolocator.geocode(destination)
        if dest_location:
            dest_lat, dest_lon = dest_location.latitude, dest_location.longitude
            folium.Marker([dest_lat, dest_lon], tooltip="Destination", icon=folium.Icon(color='red')).add_to(m)
            folium.PolyLine(locations=[(lat, lon), (dest_lat, dest_lon)], color="green", weight=5).add_to(m)

            try:
                distance, duration = get_route_info(lat, lon, dest_lat, dest_lon)
                st.success(f"📍 Route shown to: {destination}")
                st.info(f"🛣️ Distance: **{distance} km** | ⏱️ Estimated Time: **{duration} minutes**")
                voice_output = f"Your destination is {destination}. The distance is {distance} kilometers. Estimated walking time is {duration} minutes."
            except Exception:
                st.warning("Couldn't fetch route info. Check ORS API key or destination validity.")
        else:
            st.warning("Could not find the destination. Please check the spelling or try a different place.")
            voice_output = "Sorry, the destination could not be found."

    else:
        voice_output = f"Your current location is latitude {lat:.2f} and longitude {lon:.2f}."

    if speak_button:
        speak_gtts(voice_output)

    st_folium(m, use_container_width=True, height=520)

# Run app
if __name__ == "__main__":
    navigation_page()