import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random
import pytz
import http.client
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

st.set_page_config(page_title="🛌 Sleep Tracker", layout="centered")

# ------------------------
# Load Sleep Data
# ------------------------

if os.path.exists("sleep_data.json"):
    with open("sleep_data.json", "r") as f:
        sleep_data = json.load(f)
else:
    sleep_data = {}

# ------------------------
# Save Sleep Data
# ------------------------

def save_data():
    with open("sleep_data.json", "w") as f:
        json.dump(sleep_data, f, indent=4)

# ------------------------
# Sidebar Components
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

# Main app page
def main_page(username):
    st.title("🛌 Sleep Tracker")
    st.image("https://i.pinimg.com/originals/56/62/36/566236fb87c21b6f23512a429dd6476b.jpg", width=800)

    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4151/4151070.png", width=100)
    st.sidebar.title("Your Sleep Assistant")
    st.sidebar.markdown("Track your sleep habits and build healthy routines.")

    st.sidebar.subheader("💡 Daily Motivation")
    if "motivation" not in st.session_state:
        st.session_state.motivation = get_motivational_quote()
    if st.sidebar.button("🔄 Refresh Motivation"):
        st.session_state.motivation = get_motivational_quote()
    st.sidebar.info(st.session_state.motivation)

    st.sidebar.subheader("⚙️ Settings")

    # ⏰ Delete Time Entry Section
    st.sidebar.subheader("⏰ Delete Time Entry")
    username_input = st.session_state.get("username", "")
    deletable_dates = []
    if username_input and username_input in sleep_data:
        deletable_dates = [entry["date"] for entry in sleep_data[username_input].get("entries", [])]

    delete_date = st.sidebar.date_input("Select Date", value=datetime.today(), key="delete_date")
    if st.sidebar.button("Delete Entry"):
        delete_str = delete_date.strftime("%Y-%m-%d")
        if delete_str in deletable_dates:
            sleep_data[username_input]["entries"] = [
                entry for entry in sleep_data[username_input]["entries"]
                if entry["date"] != delete_str
            ]
            save_data()
            st.sidebar.success(f"Entry for {delete_str} deleted successfully!")

    # Add button for generating summary in the sidebar
    if st.sidebar.button("📊 Generate Weekly Summary"):
        st.session_state.generate_summary = True

    # Main Page content

    def get_required_sleep(age, gender):
        if age <= 5:
            return 11
        elif age <= 13:
            return 10
        elif age <= 18:
            return 9
        elif age <= 64:
            return 7
        else:
            return 7

    if username:
        if username not in sleep_data:
            st.subheader("New user detected! Please complete your profile:")
            gender = st.selectbox("Select your gender:", ["Male", "Female", "Other"])
            age = st.number_input("Enter your age:", min_value=1, max_value=100, step=1)
            if st.button("Save Profile"):
                sleep_data[username] = {
                    "meta": {"gender": gender, "age": age},
                    "entries": []
                }
                save_data()
                st.success("Profile saved! Reload the app to begin logging.")
                st.stop()
        else:
            meta = sleep_data[username].get("meta", {})
            st.success(f"Welcome back, {username}! 🌙")

            st.subheader("🛌 Log your sleep")
            date = st.date_input("Select the date", datetime.today())
            if date > datetime.today().date():
                st.error("You cannot log sleep for a future date!")
                st.stop()

            entries = sleep_data[username].get("entries", [])
            if any(e["date"] == date.strftime("%Y-%m-%d") for e in entries):
                st.warning(f"You've already logged sleep for {date.strftime('%Y-%m-%d')}. Please delete the entry first to modify.")
            else:
                sleep_time = st.time_input("What time did you go to sleep?")
                wake_time = st.time_input("What time did you wake up?")

                if st.button("Add Entry"):
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
                    save_data()
                    st.success(f"Logged {duration} hours of sleep on {today_str}!")

                    required = get_required_sleep(meta["age"], meta["gender"])
                    feedback = []
                    if duration < required:
                        feedback.append("🛌 You slept less than recommended. Try to get more rest!")
                    else:
                        feedback.append("✅ Great! You met your sleep goal!")

                    if 21 <= sleep_time.hour < 24:
                        feedback.append("✅ Perfect! You went to bed on time or earlier. Great sleep discipline!")
                    elif sleep_time.hour < 12:
                        feedback.append("⚠️ You were past your bedtime. Try to sleep earlier for better rest.")
                    else:
                        feedback.append("⚠️ Sleep time seems unusual. Try to keep it between 9 PM and 12 AM.")

                    st.markdown("<br>".join(feedback), unsafe_allow_html=True)

            st.subheader("📆 Your Sleep Entries")
            if not entries:
                st.warning("🛌 You haven’t logged any sleep yet. Start logging to track your sleep habits and unlock insights!")
                st.stop()

            entry_dates = [e['date'] for e in reversed(entries)]
            selected_date = st.selectbox("View your sleep entries:", entry_dates)
            selected_entry = next((e for e in entries if e['date'] == selected_date), None)
            if selected_entry:
                st.markdown(
                    f"On **{selected_entry['date']}** you slept at **{selected_entry['sleep_time']}**, "
                    f"woke at **{selected_entry['wake_time']}** which covers **{selected_entry['duration']} hrs** of sleep!"
                )

            # Generate Weekly Summary
            if st.session_state.get("generate_summary", False):
                st.subheader("📈 Sleep Duration (Last 7 Days)")
                entries_sorted = sorted(entries[-7:], key=lambda x: x['date'])
                dates = [e["date"] for e in entries_sorted]
                durations = [e["duration"] for e in entries_sorted]

                # Recommended sleep ranges by age
                if meta["age"] <= 5:
                    min_sleep, max_sleep = 10, 13
                elif meta["age"] <= 13:
                    min_sleep, max_sleep = 9, 11
                elif meta["age"] <= 18:
                    min_sleep, max_sleep = 8, 10
                elif meta["age"] <= 64:
                    min_sleep, max_sleep = 7, 9
                else:
                    min_sleep, max_sleep = 7, 8

                # Determine bar colors based on duration
                bar_colors = []
                for d in durations:
                    if d < min_sleep:
                        bar_colors.append('grey')
                    elif d <= max_sleep:
                        bar_colors.append('forestgreen')
                    else:
                        bar_colors.append('darkgreen')

                fig, ax = plt.subplots()
                ax.bar(dates, durations, color=bar_colors)
                ax.axhspan(min_sleep, max_sleep, facecolor='lightgreen', alpha=0.3, label=f"Ideal: {min_sleep}-{max_sleep} hrs")

                # Add legend outside the plot
                legend_patches = [
                    Patch(facecolor='grey', label='Below Ideal'),
                    Patch(facecolor='forestgreen', label='Within Ideal'),
                    Patch(facecolor='darkgreen', label='Above Ideal'),
                    Patch(facecolor='lightgreen', alpha=0.3, label=f'Ideal Range {min_sleep}-{max_sleep} hrs')
                ]
                ax.legend(handles=legend_patches, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

                plt.xticks(rotation=30)
                ax.set_ylabel("Hours Slept")
                ax.set_title("Last 7 Days Sleep Duration")
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)

                total_sleep_week = sum(durations)
                required_sleep_week = get_required_sleep(meta["age"], meta["gender"]) * 7
                st.subheader("📝 Custom Sleep Summary")
                summary = f"""
                🌟 Hey {username}! Here's your sleep snapshot for this week:

                - You slept **{total_sleep_week:.1f} hrs** this week.
                - Recommended sleep for a {meta['age']} year old ({meta['gender']}) is **{required_sleep_week} hrs** based on your profile.
                - { "✅ Great! You're on track!" if total_sleep_week >= required_sleep_week else "🛌 Let's aim to improve your weekly sleep total!" }

                ✨ Tips:
                - Try to keep a consistent bedtime each night.
                - Aim for 7-9 hours each night for best recovery.

                Keep tracking and you’ll be a sleep ninja soon!
                """
                st.markdown(summary)

                streak = 0
                today = datetime.today().date()
                for i in range(1, 8):
                    day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                    if any(e["date"] == day for e in entries):
                        streak += 1
                    else:
                        break
                st.subheader("🔥 Sleep Streak")
                st.markdown(f"**{streak} day streak** of sleep tracking! Keep it up! 🚀")

# ------------------------
# Main Page Logic
# ------------------------

username = st.text_input("Enter your name to continue:", key="username_input").strip()
st.session_state["username"] = username

if username:
    if username in sleep_data:
        main_page(username)
    else:
        st.subheader("New user detected! Please complete your profile:")
        with st.form("new_user_form", clear_on_submit=False):
            gender = st.selectbox("Select your gender:", ["Male", "Female", "Other"])
            age = st.number_input("Enter your age:", min_value=1, max_value=100, step=1)
            submit = st.form_submit_button("Save Profile")
        
        if submit:
            sleep_data[username] = {
                "meta": {"gender": gender, "age": age},
                "entries": []
            }
            save_data()
            st.success("Profile saved! Redirecting to login...")
            st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)
            st.stop()
