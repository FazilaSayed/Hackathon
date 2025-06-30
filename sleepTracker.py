import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random
import http.client
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.dates as mdates
import re
import uuid

# Set page configuration
st.set_page_config(page_title="🛌 Sleep Tracker", layout="centered")

# Initialize session state
if "motivation" not in st.session_state:
    st.session_state.motivation = None
if "generate_summary" not in st.session_state:
    st.session_state.generate_summary = False

# ------------------------
# Custom CSS for Styling
# ------------------------
def inject_custom_css():
    st.markdown("""
        <style>
        /* General styling */
        .stApp {
            background-color: #f0f4f8;
            font-family: 'Arial', sans-serif;
        }
        /* Button styling */
        .stButton>button {
            background-color: #4a90e2;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #357abd;
        }
        /* Input fields */
        .stTextInput>div>input, .stDateInput>div>input, .stTimeInput>div>input {
            border: 2px solid #4a90e2;
            border-radius: 5px;
            padding: 8px;
        }
        /* Headers */
        h1, h2, h3 {
            color: #2c3e50;
        }
        /* Sidebar */
        .css-1d391kg {
            background-color: #e6ecf3;
        }
        /* Expander */
        .stExpander {
            border: 1px solid #4a90e2;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

# ------------------------
# Load Sleep Data
# ------------------------
def load_data():
    if os.path.exists("sleep_data.json"):
        with open("sleep_data.json", "r") as f:
            return json.load(f)
    return {}

# ------------------------
# Save Sleep Data
# ------------------------
def save_data(sleep_data):
    with open("sleep_data.json", "w") as f:
        json.dump(sleep_data, f, indent=4)

# ------------------------
# Get Motivational Quote
# ------------------------
def get_motivational_quote():
    try:
        conn = http.client.HTTPSConnection("motivation-quotes4.p.rapidapi.com")
        headers = {
            'x-rapidapi-key': "9028d9d0cbmsha063286417ea661p18eda3jsn952984914b8c",
            'x-rapidapi-host': "motivation-quotes4.p.rapidapi.com"
        }
        conn.request("GET", "/api", headers=headers)
        res = conn.getresponse()
        data = res.read()
        quote_data = json.loads(data.decode("utf-8"))
        quote = quote_data.get("quote", "Stay strong!")
        author = quote_data.get("author", "Unknown")
        return f"“{quote}”\n\n— *{author}*"
    except Exception:
        fallback_quotes = [
            "Believe in yourself and all that you are.",
            "Push yourself, because no one else is going to do it for you.",
            "You are capable of amazing things.",
            "Every day is a fresh start.",
            "Progress, not perfection."
        ]
        return random.choice(fallback_quotes)

# ------------------------
# Get Required Sleep Range
# ------------------------
def get_required_sleep_range(age, gender):
    gender = gender.lower()
    if age <= 1:
        min_sleep, max_sleep = 14, 17
    elif age <= 2:
        min_sleep, max_sleep = 12, 15
    elif age <= 5:
        min_sleep, max_sleep = 10, 13
    elif age <= 13:
        min_sleep, max_sleep = 9, 11
    elif age <= 18:
        min_sleep, max_sleep = 8, 10
    elif age <= 64:
        min_sleep, max_sleep = 7, 9
    else:
        min_sleep, max_sleep = 7, 8
    if gender == "female":
        min_sleep += 0.5
        max_sleep += 0.5
    return round(min_sleep, 1), round(max_sleep, 1)

# ------------------------
# Get Required Sleep
# ------------------------
def get_required_sleep(age, gender):
    min_sleep, max_sleep = get_required_sleep_range(age, gender)
    return (min_sleep + max_sleep) / 2

# ------------------------
# Login Function
# ------------------------
def login(sleep_data):
    st.markdown("#### 🔐 Login to Your Account")
    raw_username = st.text_input(
        "Username:",
        key="login_username_input",
        placeholder="Enter your username",
        help="Enter your unique username to log in"
    ).strip().lower()
    login_button = st.button("🔓 Login")
    if login_button:
        if not raw_username:
            st.warning("Please enter your username.")
            return None
        elif raw_username not in sleep_data:
            st.error("❗ Username not found. Please check your ID or sign up.")
            return None
        else:
            st.session_state["username"] = raw_username
            st.session_state["display_name"] = sleep_data[raw_username]["meta"].get("name", raw_username.title())
            st.success("Logged in successfully!")
            st.rerun()
    return None

# ------------------------
# Register Function
# ------------------------
def register(sleep_data):
    st.markdown("#### 👋 Create Your Profile")
    st.markdown("""
    - **Name**: Letters and spaces only (e.g., John Doe).  
    - **Username**: Unique, letters, numbers, or underscores only.  
    - **Age & Gender**: Used to personalize sleep recommendations.
    """)
    col1, col2 = st.columns([1, 1])
    with col1:
        raw_name = st.text_input(
            "Name:",
            key="name_input",
            placeholder="Enter your full name",
            help="Your name (letters and spaces only)"
        ).strip()
    with col2:
        gender = st.selectbox("Gender:", ["Male", "Female"], help="Select your gender")
    col3, col4 = st.columns([1, 1])
    with col3:
        age = st.number_input("Age:", min_value=1, max_value=100, step=1, help="Enter your age")
    with col4:
        raw_username = st.text_input(
            "Username:",
            key="username_input",
            placeholder="Choose a unique username",
            help="Letters, numbers, or underscores only"
        ).strip()
    normalized_username = raw_username.lower()
    signup_button = st.button("📝 Sign Up")
    if signup_button:
        if not raw_name or not raw_username:
            st.warning("Please fill in all profile fields.")
            return None
        elif not re.match("^[A-Za-z ]+$", raw_name):
            st.error("❗ Name should only contain letters and spaces.")
            return None
        elif not re.match("^[A-Za-z0-9_]+$", normalized_username):
            st.error("❗ Username should only contain letters, numbers, or underscores.")
            return None
        elif normalized_username in sleep_data:
            st.error("❗ This username is already taken!")
            return None
        elif not gender or not age:
            st.warning("Please fill in all profile details.")
            return None
        else:
            st.session_state["username"] = normalized_username
            st.session_state["display_name"] = raw_name
            sleep_data[normalized_username] = {
                "meta": {
                    "gender": gender,
                    "age": age,
                    "name": raw_name,
                    "username": normalized_username
                },
                "entries": []
            }
            save_data(sleep_data)
            st.success("✅ Profile created! You are now logged in!")
            st.rerun()
    return None

# ------------------------
# Sleep Entry Function
# ------------------------
def sleep_entry(username, sleep_data, first_name):
    with st.container():
        st.subheader("🛌 Log Your Sleep")
        date = st.date_input("Date:", datetime.today(), help="Select the date of your sleep")
        
        col2, col3 = st.columns([1, 1])
        with col2:
            sleep_time = st.time_input("Sleep Time:", help="Time you went to bed")
        with col3:
            wake_time = st.time_input("Wake Time:", help="Time you woke up")
        
        if date > datetime.today().date():
            st.error("You cannot log sleep for a future date!")
            return
        entries = sleep_data[username].get("entries", [])
        if any(e["date"] == date.strftime("%Y-%m-%d") for e in entries):
            st.warning(f"You've already logged sleep for {date.strftime('%Y-%m-%d')}. Delete the entry first to modify.")
        elif st.button("Add Entry"):
            with st.spinner("Saving entry..."):
                sleep_dt = datetime.combine(date, sleep_time)
                wake_dt = datetime.combine(date, wake_time)
                if wake_dt <= sleep_dt:
                    wake_dt += timedelta(days=1)
                duration = round((wake_dt - sleep_dt).seconds / 3600, 2)
                today_str = date.strftime("%Y-%m-%d")
                sleep_data[username]["entries"].append({
                    "date": today_str,
                    "sleep_time": sleep_time.strftime("%H:%M"),
                    "wake_time": wake_time.strftime("%H:%M"),
                    "duration": duration
                })
                save_data(sleep_data)
                st.success(f"Logged {duration} hours of sleep on {today_str}!")
                meta = sleep_data[username].get("meta", {})
                required_min_sleep, required_max_sleep = get_required_sleep_range(meta["age"], meta["gender"])
                feedback = []
                if duration == 0:
                    feedback.append("No sleep?")
                elif duration < required_min_sleep:
                    feedback.append("🛌 You slept less than recommended. Try to get more rest!")
                elif required_min_sleep <= duration <= required_max_sleep:
                    feedback.append("✅ Great! You met your sleep goal!")
                else:
                    feedback.append("😴 You overslept today!")
                if duration == 0:
                    feedback.append(" Rest is crucial to recharge your body and mind!")
                elif 21 <= sleep_time.hour < 24:
                    feedback.append("✅ Perfect! You went to bed on time or earlier. Great sleep discipline!")
                elif sleep_time.hour <= 5:
                    feedback.append("⚠️ You were past your bedtime. Try to sleep earlier for better rest.")
                else:
                    feedback.append("⚠️ Bedtime seems unusual. Try to sleep between 9 PM and 12 AM.")
                st.markdown("<br>".join(feedback), unsafe_allow_html=True)

        st.subheader("📆 Your Sleep Entries")
        entries = sleep_data[username].get("entries", [])
        if not entries:
            st.warning("🛌 You haven’t logged any sleep yet. Start logging to track your sleep habits and unlock insights!")
            return
        with st.expander("View Past Entries"):
            entry_dates = [e['date'] for e in reversed(entries)]
            selected_date = st.selectbox("Select a date:", entry_dates, help="Choose a date to view details")
            selected_entry = next((e for e in entries if e['date'] == selected_date), None)
            if selected_entry:
                st.markdown(
                    f"On **{selected_entry['date']}** you slept at **{selected_entry['sleep_time']}**, "
                    f"woke at **{selected_entry['wake_time']}** which covers **{selected_entry['duration']} hrs** of sleep!"
                )

# ------------------------
# Delete Time Entry Function
# ------------------------
def delete_time_entry(username, sleep_data):
    st.sidebar.subheader("⏰ Delete Time Entry")
    entries = sleep_data.get(username, {}).get("entries", [])
    if not entries:
        st.sidebar.warning("No entries to delete.")
        return
    deletable_dates = sorted([entry["date"] for entry in entries], reverse=True)
    delete_str = st.sidebar.selectbox("Select Date to Delete", deletable_dates, help="Choose a date with a sleep entry")
    if delete_str:
        confirm = st.sidebar.checkbox(f"Confirm deletion for {delete_str}")
        if confirm and st.sidebar.button("Delete Entry"):
            with st.spinner("Deleting entry..."):
                sleep_data[username]["entries"] = [
                    entry for entry in sleep_data[username]["entries"]
                    if entry["date"] != delete_str
                ]
                save_data(sleep_data)
                st.sidebar.success(f"Entry for {delete_str} deleted successfully!")
                st.rerun()

# ------------------------
# Graph Plotting Function
# ------------------------

def plot_graph(entries_in_range, start_date, end_date, min_sleep, max_sleep):
    if not entries_in_range:
        return
    
    entries_sorted = sorted(entries_in_range, key=lambda x: x['date'])
    dates = [e["date"] for e in entries_sorted]
    durations = [e["duration"] for e in entries_sorted]
    days_in_range = len(durations)
    
    # Set figure size to (20, 9) for larger graphs
    fig, ax = plt.subplots(figsize=(20, 9))
    
    if days_in_range <= 8:
        bar_colors = []
        for d in durations:
            if d < min_sleep:
                bar_colors.append('grey')
            elif d <= max_sleep:
                bar_colors.append('teal')
            else:
                bar_colors.append('darkgreen')
        ax.bar(dates, durations, color=bar_colors)
        ax.axhspan(min_sleep, max_sleep, facecolor='lightgreen', alpha=0.3, label=f"Ideal: {min_sleep}-{max_sleep} hrs")
        legend_patches = [
            Patch(facecolor='grey', label='Below Ideal'),
            Patch(facecolor='teal', label='Within Ideal'),
            Patch(facecolor='darkgreen', label='Above Ideal'),
            Patch(facecolor='lightgreen', alpha=0.3, label=f'Ideal Range {min_sleep}-{max_sleep} hrs')
        ]
        ax.legend(handles=legend_patches, bbox_to_anchor=(1.02, 1), loc='upper left')
        ax.set_xlabel('Dates')
        ax.set_ylabel('Duration (hrs)')
        ax.set_title('Sleep Duration')
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha='right')
    else:
        x = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        y = durations
        ax.plot(x, y, color='mediumslateblue', marker='o', linewidth=2, label="Sleep Duration")
        ax.axhline(y=min_sleep, color='orangered', linestyle='--', linewidth=1.5, label=f"Min Recommended ({min_sleep} hrs)")
        ax.axhline(y=max_sleep, color='seagreen', linestyle='--', linewidth=1.5, label=f"Max Recommended ({max_sleep} hrs)")
        ax.fill_between(x, min_sleep, max_sleep, color='green', alpha=0.2, label='Ideal Range')
        for i, txt in enumerate(y):
            ax.annotate(f"{txt:.1f}", (x[i], y[i]), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, color='black')
        ax.set_title(f"🌙 Sleep Trend ({len(dates)} entries)", fontsize=14, fontweight='bold')
        ax.set_ylabel("Sleep Duration (hrs)", fontsize=12)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_xticks(x)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.legend(loc="upper left", frameon=True)
        fig.autofmt_xdate(rotation=45)
    
    fig.tight_layout()
    
    # Center the plot using Streamlit columns
    col1, col2, col3 = st.columns([0.5, 6, 0.5])
    with col2:
        st.pyplot(fig)
# ------------------------
# Summary Function
# ------------------------
def generate_summary(username, sleep_data, first_name, start_date, end_date):
    with st.container():
        st.subheader("📈 Sleep Summary")
        entries = sleep_data[username].get("entries", [])
        entries_in_range = [
            e for e in entries if start_date <= datetime.strptime(e["date"], "%Y-%m-%d").date() <= end_date
        ]
        if not entries_in_range:
            st.warning(f"No sleep data available between {start_date} and {end_date}.")
            return
        meta = sleep_data[username].get("meta", {})
        min_sleep, max_sleep = get_required_sleep_range(meta["age"], meta["gender"])
        plot_graph(entries_in_range, start_date, end_date, min_sleep, max_sleep)
        entries_sorted = sorted(entries_in_range, key=lambda x: x['date'])
        durations = [e["duration"] for e in entries_sorted]
        dates = [e["date"] for e in entries_sorted]
        avg_sleep = round(sum(durations) / len(durations), 2)
        days_in_range = (end_date - start_date).days + 1
        required_sleep_week = get_required_sleep(meta["age"], meta["gender"]) * days_in_range
        total_sleep_week = sum(durations)
        streak = 0
        longest_streak = 0
        streak_start_date = None
        streak_end_date = None
        for idx, duration in enumerate(durations):
            if duration >= min_sleep:
                if streak == 0:
                    streak_start_date = dates[idx]
                streak += 1
                if streak > longest_streak:
                    longest_streak = streak
                    streak_end_date = dates[idx]
            else:
                streak = 0
        count_days = len(durations)
        recommended_start_range = count_days * min_sleep
        recommended_end_range = count_days * max_sleep
        if recommended_start_range <= total_sleep_week <= recommended_end_range:
            sleep_feedback = "✅ Great! You're on track!"
        elif total_sleep_week < recommended_start_range:
            sleep_feedback = """
            🛌 Let's aim to improve your weekly sleep total!
            ✨ Tips:
            1. **Unplug Before Bed** 📴  
            Power down screens at least 30 minutes before sleeping.
            2. **Cool & Cozy** ❄️  
            Keep your room cool (between 23°C - 25°C).
            3. **Sleep Schedule** ⏰  
            Go to bed and wake up at the same time every day.
            4. **Dreamy Snacks** 🍓  
            Try a light bedtime snack like bananas or almonds.
            5. **Stretch it Out** 🧘‍♂️  
            Gentle stretching or yoga before bed can help.
            """
        else:
            sleep_feedback = "⏰ You’ve overslept! Try adjusting your bedtime, stay hydrated, and get some sunlight!"
        streak_display = f"Your longest streak of meeting the sleep goal is **{longest_streak} day(s)**, between {streak_start_date} and {streak_end_date}." if longest_streak > 0 else "No sleep goals met yet. Let's work on that!"
        summary = f"""
        🌟 Hey {first_name.capitalize()}! Here's your sleep snapshot:
        - Recommended total sleep for {count_days} days: **{recommended_start_range}-{recommended_end_range} hrs**. You slept **{round(total_sleep_week)} hrs**.
        - Average sleep/day: **{avg_sleep} hrs** (Recommended: **{min_sleep}-{max_sleep} hrs**).
        - {streak_display}
        - Sleep is the golden chain that ties health and happiness together!
        - {sleep_feedback}
        """
        st.markdown(summary)

# ------------------------
# Dashboard Function
# ------------------------
def show_dashboard(username, sleep_data, first_name):
    with st.container():
        st.subheader("📊 Your Sleep Dashboard")
        entries = sleep_data[username].get("entries", [])
        if not entries:
            st.info("No sleep data yet. Log your first entry to see your stats!")
            return
        durations = [e["duration"] for e in entries[-7:]]
        avg_sleep = round(sum(durations) / len(durations), 2) if durations else 0
        meta = sleep_data[username].get("meta", {})
        min_sleep, max_sleep = get_required_sleep_range(meta["age"], meta["gender"])
        streak = calculate_streak(entries, min_sleep)
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Sleep (Last 7 Days)", f"{avg_sleep} hrs")
        col2.metric("Recommended Sleep", f"{min_sleep}-{max_sleep} hrs")
        col3.metric("Longest Streak", f"{streak} days")
        if entries:
            st.markdown("#### Recent Entries")
            for entry in entries[-3:]:
                st.markdown(
                    f"**{entry['date']}**: Slept at {entry['sleep_time']}, woke at {entry['wake_time']} ({entry['duration']} hrs)"
                )

def calculate_streak(entries, min_sleep):
    streak = 0
    longest_streak = 0
    for entry in sorted(entries, key=lambda x: x['date']):
        if entry["duration"] >= min_sleep:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0
    return longest_streak

# ------------------------
# Main Function
# ------------------------
def main():
    #inject_custom_css()
    sleep_data = load_data()
    st.title("🛌 Sleep Tracker")
    st.image(
        "https://i.pinimg.com/originals/56/62/36/566236fb87c21b6f23512a429dd6476b.jpg",
        caption="Illustration of a person sleeping peacefully",
        width=800
    )

    # Sidebar
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4151/4151070.png", width=100)
    st.sidebar.title("Your Sleep Assistant")
    st.sidebar.markdown("Track your sleep habits and build healthy routines.")
    st.sidebar.subheader("💡 Daily Motivation")
    if st.session_state.motivation is None:
        st.session_state.motivation = get_motivational_quote()
    if st.sidebar.button("🔄 Refresh Motivation"):
        with st.spinner("Fetching new quote..."):
            st.session_state.motivation = get_motivational_quote()
    st.sidebar.info(st.session_state.motivation)

    # Main Content
    if "username" not in st.session_state:
        st.markdown("""
        ## 🌙 Welcome to **Sleep Tracker**   
        Track your sleep, build streaks, and get personalized feedback to become a **Sleep Superstar**!  
        Just log your bedtime & wake time – we’ll take care of the rest 💤✨
        """)
        tabs = st.tabs(["Login", "Sign Up"])
        with tabs[0]:
            login(sleep_data)
        with tabs[1]:
            register(sleep_data)
    else:
        username = st.session_state["username"]
        display_name = st.session_state.get("display_name", username.title())
        first_name = display_name.split()[0].capitalize()
        if username not in sleep_data:
            st.subheader("🆕 New user detected! Let’s complete your profile 👇")
            with st.form("new_user_form", clear_on_submit=False):
                gender = st.selectbox("Select your gender:", ["Male", "Female"])
                age = st.number_input("Enter your age:", min_value=1, max_value=100, step=1)
                submit = st.form_submit_button("Save Profile")
                if submit:
                    if not gender or not age:
                        st.warning("Please fill in all profile details.")
                    else:
                        sleep_data[username] = {
                            "meta": {"gender": gender, "age": age, "name": display_name},
                            "entries": []
                        }
                        save_data(sleep_data)
                        st.success("Profile saved! You are now logged in!")
                        st.rerun()
        else:
            st.success(f"Hey {first_name}, are you well-rested and ready to conquer the day?")
            tabs = st.tabs(["Dashboard", "Sleep Log", "Summary"])
            with tabs[0]:
                show_dashboard(username, sleep_data, first_name)
            with tabs[1]:
                sleep_entry(username, sleep_data, first_name)
            with tabs[2]:
                with st.container():
                    st.subheader("📅 Select Dates for Summary")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        start_date = st.date_input("Start Date", min_value=datetime(2020, 1, 1), value=datetime.today() - timedelta(days=7))
                    with col2:
                        end_date = st.date_input("End Date", min_value=start_date, value=datetime.today())
                    if st.button("Generate Summary"):
                        st.session_state.generate_summary = True
                        st.session_state.start_date = start_date
                        st.session_state.end_date = end_date
                    if st.session_state.get("generate_summary", False):
                        generate_summary(username, sleep_data, first_name, start_date, end_date)
                        st.session_state.generate_summary = False

            # Sidebar Settings
            st.sidebar.subheader("⚙️ Settings")
            delete_time_entry(username, sleep_data)
            if st.sidebar.button("🚪 Logout"):
                st.session_state.clear()
                st.rerun()

# Run the app
if __name__ == "__main__":
    main()
