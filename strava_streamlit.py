import random
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import polyline
import matplotlib.pyplot as plt
import urllib3
from datetime import datetime, timedelta
import numpy as np
import matplotlib.dates as mdates

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Strava API endpoints
AUTH_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

# Payload for refreshing token (replace with your values)
payload = {
    'client_id': "156299",
    'client_secret': 'd1808c4f07920ef6b6b0bc9c31eff47c3a3b2ad8',
    'refresh_token': '905747e047b7a67196cf3d806219e64c00c7702a',
    'grant_type': "refresh_token",
    'f': 'json'
}

# Get access token
res = requests.post(AUTH_URL, data=payload, verify=False)
access_token = res.json().get('access_token')

# Function to fetch Strava activities
def get_data(token, page=1, per_page=30):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'page': page, 'per_page': per_page}
    response = requests.get(ACTIVITIES_URL, headers=headers, params=params)
    return response.json() if response.status_code == 200 else []

# App configuration
st.set_page_config(page_title="Strava", layout="wide")

# -----------------
# Sidebar
# -----------------
st.sidebar.header("📅 Select Date Range to fetch your strava activity")
start_date = st.sidebar.date_input("Start Date", datetime.now().date() - timedelta(days=7), key="start_date")
end_date = st.sidebar.date_input("End Date", datetime.now().date(), key="end_date")
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

view_map = st.sidebar.button("🗺️ View My Activity Map", key="view_map_btn")
custom_summary = st.sidebar.button("Generate Activity Summary", key="custom_summary_btn")

# -----------------
# Home Page
# -----------------
def show_home():
    st.title("🚴 Strava Activity Dashboard")
    st.subheader("Your personal activity insights at a glance")
    st.image(
        "https://www.letsroam.com/explorer/wp-content/uploads/sites/10/2023/04/hiking-tips.jpg",
        use_container_width=True
    )

# Initialize page state
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Handle navigation
if view_map:
    st.session_state.page = 'map'
if custom_summary:
    st.session_state.page = 'form'

# Show home if selected
if st.session_state.page == 'home':
    show_home()

# -----------------
# Load Data
# -----------------
@st.cache_data
def load_activities(max_pages=10):
    if not access_token:
        return pd.DataFrame()
    data = []
    for page in range(1, max_pages+1):
        batch = get_data(access_token, page=page)
        if not batch:
            break
        data.extend(batch)
    df = pd.json_normalize(data)
    df['distance_km'] = df['distance'] / 1000
    df['moving_time_h'] = df['moving_time'] / 3600
    df['average_speed_kmh'] = df['average_speed'] * 3.6
    df['start_date'] = pd.to_datetime(df['start_date']).dt.date
    return df

# Load and filter
df_all = load_activities()
df = df_all[(df_all['start_date'] >= start_date) & (df_all['start_date'] <= end_date)]

# -----------------
# Map Page
# -----------------
if st.session_state.page == 'map':
    st.subheader(f"🗺️ Activity Map: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")
    if df.empty:
        st.warning(f"You have no data entered for the date range ({start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}) entered in Strava.")
    else:
        # Get unique dates and activity types from df
        dates = sorted(df['start_date'].unique())
        date_options = ['All'] + [d.strftime('%d %b %Y') for d in dates]

        types = ['Run', 'Walk', 'Ride', 'Swim', 'Hike']

        activity_selected = st.multiselect(
            "Select activity types to show", types, default=[]
        )

        selected = st.selectbox(
            "Select a specific date to view your activity or choose All to show all activities",
            date_options,
            key="map_date_select"
        )

        if selected != 'All':
            sel_date = datetime.strptime(selected, '%d %b %Y').date()
            df_map = df[df['start_date'] == sel_date]
        else:
            df_map = df

        if activity_selected:
            df_map = df_map[df_map['type'].isin(activity_selected)]
        else:
            df_map = df_map.iloc[0:0]  # no data if none selected

        if not df_map.empty:
            import colorsys

            def hsl_to_rgb(h, s, l):
                r, g, b = colorsys.hls_to_rgb(h, l, s)
                return [int(255*r), int(255*g), int(255*b)]

            total_polylines = len(df_map)
            lines, markers = [], []

            for idx, (_, r) in enumerate(df_map.iterrows()):
                poly = r.get('map.summary_polyline')
                if pd.notna(poly):
                    coords = polyline.decode(poly)

                    # Generate a distinct blue shade for each polyline based on idx
                    # Hue from 0.5 (blue) to 0.7 (cyan-ish) spread evenly
                    h = 0.5 + 0.2 * idx / max(total_polylines - 1, 1)
                    color = hsl_to_rgb(h, 0.7, 0.5)

                    for i in range(len(coords)-1):
                        lines.append({
                            'start_lat': coords[i][0], 'start_lon': coords[i][1],
                            'end_lat': coords[i+1][0], 'end_lon': coords[i+1][1],
                            'date': r['start_date'].strftime('%d %b %Y'),
                            'distance_km': round(r['distance_km'], 2),
                            'type': r['type'],
                            'color': color
                        })

                    markers.append({'lat': coords[0][0], 'lon': coords[0][1], 'color': [0,255,0]})
                    markers.append({'lat': coords[-1][0], 'lon': coords[-1][1], 'color': [255,0,0]})

            layer_lines = pdk.Layer(
                'LineLayer', data=pd.DataFrame(lines), pickable=True,
                get_source_position='[start_lon, start_lat]', get_target_position='[end_lon, end_lat]',
                get_color='color',
                get_width=4
            )
            layer_points = pdk.Layer(
                'ScatterplotLayer', data=pd.DataFrame(markers),
                pickable=False, get_position='[lon, lat]', get_color='color', get_radius=10
            )
            deck = pdk.Deck(
                map_style="mapbox://styles/mapbox/outdoors-v12",
                initial_view_state=pdk.ViewState(
                    latitude=np.mean([l['start_lat'] for l in lines]),
                    longitude=np.mean([l['start_lon'] for l in lines]),
                    zoom=12, pitch=45
                ),
                layers=[layer_lines, layer_points],
                tooltip={
                    'html': '<b>Date:</b> {date}<br><b>Distance:</b> {distance_km} km<br><b>Type:</b> {type}'
                }
            )
            st.pydeck_chart(deck)

        else:
            st.warning("No activities found for the selected activity types and date range.")

    if st.button("⬅️ Go Back Home", key="back_home_map_btn"):
        st.session_state.page = 'home'


# -----------------
# Summary Form Page
# -----------------
if st.session_state.page == 'form':
    if df.empty:
        st.warning(f"You have no data entered for {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')} in your Strava app.")
        if st.button("⬅️ Go Back Home", key="back_no_data_btn"):
            st.session_state.page = 'home'
    else:
        date_range = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
        st.subheader(f"✏️ Activity Arena Achievement Report ({date_range})")
        types = ['Run','Walk','Ride','Swim','Hike']
        sel_type = st.selectbox("Choose an activity type", types, key="type")
        goals = ['Activities','Distance','Time','Speed']
        goal_kind = st.selectbox("Check your Progress - Select a parameter", goals, key="kind")
        fmt = "%d" if goal_kind == 'Activities' else None
        goal_val = st.number_input(
            "Check your Progress - Enter expected value for parameter",
            min_value=1 if goal_kind=='Activities' else 0.0,
            step=1 if goal_kind=='Activities' else 0.1,
            format=fmt,
            key="value"
        )
        if st.button("Generate Summary", key="gen_btn"):
            st.session_state.form = {'type': sel_type, 'kind': goal_kind, 'value': goal_val}
            st.session_state.page = 'summary'
        if st.button("⬅️ Go Back Home", key="back_form_btn"):
            st.session_state.page = 'home'

# -----------------
# Summary Page
# -----------------
if st.session_state.page == 'summary':
    cfg = st.session_state.form
    sdf = df[df['type'] == cfg['type']]
    days = sdf['start_date'].nunique()
    dist = sdf['distance_km'].sum()
    avg_sp = sdf['average_speed_kmh'].mean() if not sdf.empty else 0
    top_sp = sdf['average_speed_kmh'].max() if not sdf.empty else 0
    range_str = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"

    # Charts
    sdf_grp = sdf.groupby('start_date').agg({'distance_km':'sum','average_speed_kmh':'mean'})
    sdf_grp.index = sdf_grp.index.map(lambda d: d.strftime('%d.%m.%y'))

    st.subheader("📏 Distance vs Days")
    fig1, ax1 = plt.subplots()
    if days > 7:
        ax1.plot(sdf_grp.index, sdf_grp['distance_km'], marker='o')
    else:
        ax1.bar(sdf_grp.index, sdf_grp['distance_km'])
    ax1.set_xlabel('Date'); ax1.set_ylabel('Distance (km)')
    st.pyplot(fig1)

    st.subheader("⚡ Speed vs Days")
    fig2, ax2 = plt.subplots()
    if days > 7:
        ax2.plot(sdf_grp.index, sdf_grp['average_speed_kmh'], marker='o')
    else:
        ax2.bar(sdf_grp.index, sdf_grp['average_speed_kmh'])
    ax2.set_xlabel('Date'); ax2.set_ylabel('Avg Speed (km/h)')
    st.pyplot(fig2)


    st.subheader("Previous Goal Progress")
    
    if cfg['kind'] == 'Activities': 
        ach = len(sdf)
    elif cfg['kind'] == 'Distance': 
        ach = dist
    elif cfg['kind'] == 'Time': 
        ach = sdf['moving_time_h'].sum()
    else: 
        ach = avg_sp
    
    pct = min(100 * ach / cfg['value'], 100)
    
    # Show progress as value and add percent in caption, no arrow in delta
    st.metric("Progress", f"{int(ach)} / {int(cfg['value'])}", delta=" ")
    st.caption(f"{pct:.0f}% progress")



    # Fun Summary
    st.subheader(f"🎉 Summary based on Strava activities")
    if sdf.empty:
        st.warning(f"You have no data entered for {range_str} in your Strava app.")
    else:
        st.write(f"Between **{range_str}**, you were active on **{days} days**, covering **{dist:.2f} km**.")
        st.write(f"Your average speed was **{avg_sp:.2f} km/h**, and your top speed reached **{top_sp:.2f} km/h**.")
        if pct >= 100:
            st.success("🎉 Fantastic! You crushed your goal!")
        elif pct >= 75:
            st.info("💪 Great effort! You're nearing your goal.")
        else:
            st.warning("🚀 Keep going! You're on your way.")

    if st.button("⬅️ Go Back Home", key="back_home_summary_btn"):
        st.session_state.page = 'home'
