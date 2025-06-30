import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
import google_auth_oauthlib.flow
import googleapiclient.discovery
import json
import os
import random


# App configuration
st.set_page_config(page_title="GFit", layout="wide")

# --- CONFIGURATION ---
CLIENT_SECRETS_FILE = "client_secret.json"
DATA_FILE = None
SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.location.read",
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/userinfo.email",    # <-- Add this!
    "openid"                                              
]
API_SERVICE_NAME = 'fitness'
API_VERSION = 'v1'
calories_per_step = 0.05
base_hr_calorie_multiplier = 0.01

# --- UI HEADER ---
st.title("Google Fit Step Counter and Heart Rate Tracker")
st.markdown(
    """
    <img src="https://live.staticflickr.com/7864/39640863583_1af30cb1e0_b.jpg" 
         style="height:700px; width:auto;">
    """,
    unsafe_allow_html=True
)

st.subheader("🏃‍♂️ Track. Improve. Repeat.")

# --- SIDEBAR CONFIG ---

    # Optional: Add some fun emojis or GIFs (use markdown with image links)
st.sidebar.markdown(
"""
<div style="text-align: center;">
    <img src="https://cdn.dribbble.com/userupload/4777282/file/original-cdd4ea4c2c8549262ec7d19a8d55f9dd.gif" width="200">
</div>
""",
unsafe_allow_html=True
)


st.sidebar.title("🛠️ Customize Your Fitness Display Settings")

days_option = st.sidebar.radio("📆 Choose data range:", ("7 days", "2 weeks", "1 month"))
with st.sidebar.expander("💡 StepSmart Guide: Age-wise Facts!"):
    st.markdown("""
    🧠 **Did you know?** Your ideal daily steps can vary with age! Here's a quick cheat sheet:

    - 🧒 **Kids (6–12 yrs):** 12,000–16,000 steps/day (they're like energizer bunnies!)
    - 🧑 **Teens (13–19 yrs):** 10,000–12,000 steps/day (school, sports, and fun!)
    - 👨‍💼 **Adults (20–40 yrs):** 8,000–10,000 steps/day (hello desk jobs 👋)
    - 👵 **Older Adults (40+):** 6,000–8,000 steps/day (steady and strong 🦶)

    📲 *Fitness trackers and smartwatches often aim for 10,000 steps — but you can adjust based on your lifestyle and goals!*

    🎯 **Set your step goal below and track your progress like a pro!**
    """)

    st.toast("✨ Tip: Setting realistic goals = long-term success!", icon="🎉")

goal_steps = st.sidebar.number_input("👟 Daily Step Goal", min_value=1000, max_value=50000, value=5000, step=500)
cals_goal = st.sidebar.number_input("🔥  Daily Calories Burn Goal", min_value=500, max_value=8000, value=2000, step=200)
analytics_options = st.sidebar.multiselect(
    "📊 Choose analytics to display:",
    ["Steps & Heart Rate", "Calories Burned", "Step Goal Achievements", "Streak Tracker"]
)
clear_data = st.sidebar.button("🧹 Clear Your Saved Data")
if clear_data and DATA_FILE and os.path.exists(DATA_FILE):
    os.remove(DATA_FILE)
    st.sidebar.success("✅ Your data has been cleared!")

if not analytics_options:
    st.info("👈 Select one or more analytics from the sidebar to begin!")
    st.stop()

# Sidebar button to generate summary
generate_summary = st.sidebar.button("📊 Generate Summary")



# --- GOOGLE FIT AUTHENTICATION ---
def authenticate_google_fit():
    if "credentials" not in st.session_state:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES
        )
        credentials = flow.run_local_server(port=0)
        st.session_state.credentials = credentials
        st.session_state.service = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials
        )

        # Fetch user email
        oauth2_service = googleapiclient.discovery.build('oauth2', 'v2', credentials=credentials)
        user_info = oauth2_service.userinfo().get().execute()
        st.session_state.user_email = user_info.get('email')

if "service" not in st.session_state:
    authenticate_google_fit()

service = st.session_state.service
user_email = st.session_state.user_email
DATA_FILE = f"fitness_data_{user_email.replace('@', '_at_').replace('.', '_dot_')}.json"

# --- FETCH DATA ---
fetch_days = {"7 days": 7, "2 weeks": 14, "1 month": 30}
selected_days = fetch_days[days_option]
# Scale calorie goal based on selected duration
multiplier_map = {"7 days": 7, "2 weeks": 14, "1 month": 30}
total_goal_cals = cals_goal * multiplier_map[days_option]

now = datetime.now(timezone.utc)
start_time = int((now - timedelta(days=selected_days)).timestamp() * 1000)
end_time = int(now.timestamp() * 1000)

steps_response = service.users().dataset().aggregate(userId="me", body={
    "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
    "bucketByTime": {"durationMillis": 86400000},
    "startTimeMillis": start_time,
    "endTimeMillis": end_time
}).execute()

hr_response = service.users().dataset().aggregate(userId="me", body={
    "aggregateBy": [{"dataTypeName": "com.google.heart_rate.bpm"}],
    "bucketByTime": {"durationMillis": 86400000},
    "startTimeMillis": start_time,
    "endTimeMillis": end_time
}).execute()

# --- PROCESS DATA ---
dates, steps_counts, heart_rates, calories_burned = [], [], [], []
goal_achieved = []
hr_map = {}

# Heart rate
for bucket in hr_response.get('bucket', []):
    date = datetime.utcfromtimestamp(int(bucket['startTimeMillis']) / 1000).strftime('%Y-%m-%d')
    total_bpm, count = 0, 0
    for dataset in bucket['dataset']:
        for point in dataset.get('point', []):
            for value in point['value']:
                total_bpm += value.get('fpVal', 0)
                count += 1
    avg_bpm = total_bpm / count if count else 0
    hr_map[date] = avg_bpm


# Steps + calories
for bucket in steps_response.get('bucket', []):
    date = datetime.utcfromtimestamp(int(bucket['startTimeMillis']) / 1000).strftime('%Y-%m-%d')
    steps = sum(value.get('intVal', 0) for dataset in bucket['dataset']
                for point in dataset.get('point', [])
                for value in point.get('value', []))
    
    avg_hr = hr_map.get(date, 0)
    hr_factor = max(avg_hr - 80, 0) * base_hr_calorie_multiplier
    est_cals = steps * (calories_per_step + hr_factor)

    dates.append(date)
    steps_counts.append(steps)
    heart_rates.append(avg_hr)
    calories_burned.append(est_cals)
    goal_achieved.append(steps >= goal_steps)

# Save
data_to_save = {
    "dates": dates,
    "steps": steps_counts,
    "heart_rates": heart_rates,
    "calories": calories_burned,
    "goal_achieved": goal_achieved,
    "goal_steps": goal_steps
}
with open(DATA_FILE, 'w') as f:
    json.dump(data_to_save, f)

# --- MOTIVATION ---
total_cals_burnt = sum(calories_burned)
met_goal = total_cals_burnt >= total_goal_cals

motivations = {
    True: [
        "🔥 You're crushing it! Keep that fire alive!",
        "🏆 Calorie goal met — you're unstoppable!",
        "💪 Legend! Time to raise the bar!"
    ],
    False: [
        "🙌 Small steps = big gains. Stay consistent!",
        "📈 You're on your way — don’t stop now!",
        "😎 You didn’t come this far to only come this far."
    ]
}
st.markdown("### 💬 Motivation for the Week")
st.info(random.choice(motivations[met_goal]))


# --- DISPLAY ANALYTICS ---

chart_type = 'bar' if selected_days <= 7 else 'line'
import matplotlib.dates as mdates
if "Steps & Heart Rate" in analytics_options:
    st.header("📈 Steps and Heart Rate Over Time")

    
    fig, ax1 = plt.subplots(figsize=(20, 9))  

    ax1.set_xlabel("Date", fontsize=14)
    ax1.set_ylabel("Steps", color='blue', fontsize=14)
    ax1.plot(dates, steps_counts, marker='o', color='blue', label='Steps', linewidth=2)
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.tick_params(axis='x', labelsize=12)
    ax1.tick_params(axis='y', labelsize=12)

    ax1.set_xticks(range(len(dates)))
    ax1.set_xticklabels(dates, rotation=45, ha='right')

    ax2 = ax1.twinx()
    ax2.set_ylabel("Heart Rate (bpm)", color='red', fontsize=14)
    ax2.plot(dates, heart_rates, marker='s', linestyle='--', color='red', label='Heart Rate', linewidth=2)
    ax2.tick_params(axis='y', labelcolor='red', labelsize=12)

    fig.tight_layout()

    # Centered chart on Streamlit
    col1, col2, col3 = st.columns([0.5, 6, 0.5])
    with col2:
        st.pyplot(fig)

if "Calories Burned" in analytics_options:
    st.header("🔥 Estimated Calories Burned")

    # --- Donut Chart: % of Goal Reached ---
    percent_burned = min(total_cals_burnt / total_goal_cals, 1.0)

    # Create a small donut chart
    fig, ax = plt.subplots(figsize=(2.8, 2.8))  # small chart size
    wedges, _ = ax.pie(
        [percent_burned, 1 - percent_burned],
        startangle=90,
        colors=["#00cc99", "#eeeeee"],
        wedgeprops={'width': 0.5, 'edgecolor': 'white'}
    )

    # Add center text
    ax.text(0, 0, f"{int(percent_burned * 100)}%", ha='center', va='center',
            fontsize=12, fontweight='bold', color="#333333")
    ax.set(aspect="equal")
    fig.tight_layout()

    # Display metrics
    st.markdown(f"**📊 Total Calories Burned:** `{int(total_cals_burnt)} kcal`")
    st.markdown(f"**🎯 Calories Goal:** `{total_goal_cals} kcal`")

    # Center the chart using Streamlit layout columns
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.pyplot(fig)

    
    chart_type = 'bar' if selected_days <= 7 else 'line'
    # --- Colorful Bar Chart for Daily Burn ---
    from matplotlib.colors import LinearSegmentedColormap
    
    cmap = LinearSegmentedColormap.from_list("fun_green", ["#b2f7ef", "#00cc99"])
    bar_colors = [cmap(min(c/total_goal_cals, 1.0)) for c in calories_burned]
    
    fig, ax = plt.subplots(figsize=(20, 9))
    ax.bar(dates, calories_burned, color=bar_colors)
    ax.axhline(y=total_goal_cals/multiplier_map[days_option], color='red', linestyle='--', label='Daily Calorie Goal')
    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Estimated Calories", fontsize=14)
    ax.set_title("Daily Calories Burned", fontsize=16)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha='right')
    ax.grid(axis='y')
    ax.legend(fontsize=12)
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=12)
    
    fig.tight_layout()
    
    # Center the chart in Streamlit
    col1, col2, col3 = st.columns([0.5, 6, 0.5])
    with col2:
        st.pyplot(fig)
    
    # --- Motivation based on progress ---
    if total_cals_burnt >= total_goal_cals:
        st.success("🔥 You're smashing your calorie goals — keep it rolling!")
    elif total_cals_burnt >= 0.7 * total_goal_cals:
        st.info("💪 You're almost there — a strong finish will do it!")
    else:
        st.warning("🚀 Let’s fire it up! Burn a bit more to hit your weekly target.")


if "Step Goal Achievements" in analytics_options:
    st.header("🎯 Step Goal Achievements")
    goal_colors = ['green' if met else 'gray' for met in goal_achieved]

    fig, ax = plt.subplots(figsize=(20, 9))

    if selected_days <= 7:
        ax.bar(dates, steps_counts, color=goal_colors)
    else:
        ax.plot(dates, steps_counts, marker='o', linestyle='-', color='green', linewidth=2, label='Steps')
        ax.axhline(y=goal_steps, color='orange', linestyle='--', label='Goal')

    ax.set_title('Daily Step Count vs Goal', fontsize=16)
    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Steps", fontsize=14)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha='right')
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=12)

    if selected_days > 7:
        ax.legend(fontsize=12)

    ax.grid(axis='y')
    fig.tight_layout()

    col1, col2, col3 = st.columns([0.5, 6, 0.5])
    with col2:
        st.pyplot(fig)

if "Streak Tracker" in analytics_options:
    st.subheader("🔥 Step Streak Tracker")
    current_streak = longest_streak = 0
    for achieved in goal_achieved:
        if achieved:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
    st.markdown(f"✅ **Current Streak:** {current_streak} days")
    st.markdown(f"🏆 **Longest Streak:** {longest_streak} days")


# When button clicked, show the summary on main page
if generate_summary:
    
    total_steps = sum(steps_counts)
    avg_heart_rate = round(sum(heart_rates) / len(heart_rates), 1) if heart_rates else 0
    total_calories = sum(calories_burned)
    days_tracked = len(dates)
    st.header(f"🎉 Your Fitness Summary in last {days_tracked}!")
   
    st.markdown("---")

    
    st.metric(
    label="🚶 Steps summary",
    value=f"{total_steps:,} steps in last {days_tracked} days",
    delta="")
    st.caption(f"🎯 Step goals: {goal_steps * days_tracked:,} steps")

    if total_steps >= goal_steps * days_tracked:
        step_msg = "🚀 Wow! You've blasted through your step goals like a marathon champ!"
    elif total_steps >= goal_steps * days_tracked * 0.7:
        step_msg = "👍 Great hustle! You're almost at your step goal — keep moving!"
    else:
        step_msg = "👣 Every step counts. Let's step it up a notch next week!"
    st.write(step_msg)
    
    st.metric("🔥 Total Calories Burned last {days_tracked} days", f"{total_calories:.1f} kcal", delta="")
    st.caption(f"Calories Goal: {total_goal_cals} for {days_tracked} DAYS")

    if total_calories >= total_goal_cals:
        cal_msg = "🔥 Your calorie burn is on fire! 🔥 Keep that metabolism roaring!"
    else:
        cal_msg = "🌟 Calories burned are climbing — just a little more to hit that goal!"
    st.write(cal_msg)
    
    
