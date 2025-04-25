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

    # Date Range Selection
    st.sidebar.subheader("📅 Select Date Range")
    start_date = st.sidebar.date_input("Start Date", min_value=datetime(2020, 1, 1), value=datetime.today() - timedelta(days=7))
    end_date = st.sidebar.date_input("End Date", min_value=start_date, value=datetime.today())

    # Add button for generating summary in the sidebar
    if st.sidebar.button("📊 Generate Summary"):
        st.session_state.generate_summary = True
        st.session_state.start_date = start_date
        st.session_state.end_date = end_date

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
                st.success("Profile saved! Enter your name to log in.")
                st.stop()
        else:
            meta = sleep_data[username].get("meta", {})
            st.success(f""Hey {username.capitalize()}, are you well-rested and ready to conquer the day?")

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
                    if duration == 0:
                        feedback.append("No sleep? Rest is crucial to recharge your body and mind!")
                    elif duration < required:
                        feedback.append("🛌 You slept less than recommended. Try to get more rest!")
                    else:
                        feedback.append("✅ Great! You met your sleep goal!")

                    if 21 <= sleep_time.hour < 24:
                        feedback.append("✅ Perfect! You went to bed on time or earlier. Great sleep discipline!")
                    elif sleep_time.hour <= 5:
                        feedback.append("⚠️ You were past your bedtime. Try to sleep earlier for better rest.")
                    else:
                        feedback.append("⚠️ Bedtime seems unusual. Try to sleep between 9 PM and 12 AM.")

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

            # Generate Summary based on selected date range
            if st.session_state.get("generate_summary", False):
                st.subheader("📈 Sleep Duration based on Custom Date Range")
                entries_in_range = [
                    e for e in entries if start_date <= datetime.strptime(e["date"], "%Y-%m-%d").date() <= end_date
                ]
                if not entries_in_range:
                    st.warning(f"No sleep data available between {start_date} and {end_date}.")
                else:
                    entries_sorted = sorted(entries_in_range, key=lambda x: x['date'])
                    dates = [e["date"] for e in entries_sorted]
                    durations = [e["duration"] for e in entries_sorted]

                    # Calculate average sleep duration
                    avg_sleep = round(sum(durations) / len(durations), 2)

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
                            bar_colors.append('teal')
                        else:
                            bar_colors.append('darkgreen')

                    # Plot bar or line graph based on the number of entries
                    if len(durations) <= 7:
                        fig, ax = plt.subplots()
                        ax.bar(dates, durations, color=bar_colors)
                        ax.axhspan(min_sleep, max_sleep, facecolor='lightgreen', alpha=0.3, label=f"Ideal: {min_sleep}-{max_sleep} hrs")

                        # Add legend outside the plot
                        legend_patches = [
                            Patch(facecolor='grey', label='Below Ideal'),
                            Patch(facecolor='teal', label='Within Ideal'),
                            Patch(facecolor='darkgreen', label='Above Ideal'),
                            Patch(facecolor='green', alpha=0.3, label=f'Ideal Range {min_sleep}-{max_sleep} hrs')
                        ]
                        ax.legend(handles=legend_patches, bbox_to_anchor=(1.02, 1), loc='upper left')

                        ax.set_xlabel('Dates')
                        ax.set_ylabel('Duration (hrs)')
                        ax.set_title('Sleep Duration Over Selected Range')
                        st.pyplot(fig)
                    else:
                        import matplotlib.dates as mdates
                        import numpy as np

                        fig, ax = plt.subplots(figsize=(10, 5))

                        x = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
                        y = durations

                        ax.plot(x, y, color='mediumslateblue', marker='o', linewidth=2, label="Sleep Duration")
                        ax.axhline(y=min_sleep, color='orangered', linestyle='--', linewidth=1.5, label=f"Min Recommended ({min_sleep} hrs)")
                        ax.axhline(y=max_sleep, color='seagreen', linestyle='--', linewidth=1.5, label=f"Max Recommended ({max_sleep} hrs)")
                        ax.fill_between(x, min_sleep, max_sleep, color='green', alpha=0.2, label='Ideal Range')
                        
                        for i, txt in enumerate(y):
                            ax.annotate(f"{txt:.1f}", (x[i], y[i]), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, color='black')

                        ax.set_title(f"🌙 Sleep Trend from {start_date.strftime('%b %d')} to {end_date.strftime('%b %d')}", fontsize=14, fontweight='bold')
                        ax.set_ylabel("Sleep Duration (hrs)", fontsize=12)
                        ax.set_xlabel("Date", fontsize=12)
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
                        ax.xaxis.set_major_locator(mdates.DayLocator())
                        fig.autofmt_xdate()

                        ax.legend(loc="upper left", frameon=True)
                        st.pyplot(fig)

                     # Additional sleep summary
                    # Calculate the number of days in the selected range
                    days_in_range = (end_date - start_date).days + 1  # Including both start and end dates
                    #Calculate the required sleep for the total days in the range
                    required_sleep_week = get_required_sleep(meta["age"], meta["gender"]) * days_in_range

                    total_sleep_week = sum(durations)
                   
                    # Calculate longest streak
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
                    recommended_start_range = count_days*min_sleep
                    recommended_end_range = count_days*max_sleep
                   
                # Generate sleep feedback based on the total sleep for the week
                    if recommended_start_range <= total_sleep_week <= recommended_end_range:
                        sleep_feedback = "✅ Great! You're on track!"
                    elif total_sleep_week < recommended_start_range:
                        sleep_feedback = """
                        🛌 Let's aim to improve your weekly sleep total!
                        
                        ✨ Tips:
                        
                        1. **Unplug Before Bed** 📴  
                        Power down screens at least 30 minutes before sleeping. Your brain needs a break from that blue light!
                        
                        2. **Cool & Cozy** ❄️  
                        Keep your room cool (around 18°C or 65°F) for the perfect sleep environment—it's like nature’s sleep hack.
                        
                        3. **Sleep Schedule = Power** ⏰  
                        Go to bed and wake up at the same time every day—even on weekends! Consistency is key to feeling refreshed.
                        
                        4. **Dreamy Snacks** 🍓  
                        Try a light bedtime snack like bananas or almonds. They're rich in magnesium, helping your muscles relax and unwind.
                        
                        5. **Stretch it Out** 🧘‍♂️  
                        A few minutes of gentle stretching or yoga before bed can help your body release tension and ease into sleep. 
                        """
                    else:
                        sleep_feedback = "Sleep is the golden chain that ties our bodies and good health together!"  # Add a default value for sleep_feedback

                    # Construct the summary
                    streak_display = f"Your longest streak of meeting the sleep goal is **{longest_streak} day(s)**, between {streak_start_date} and {streak_end_date}." if longest_streak > 0 else "No sleep goals met yet. Let's work on that!"

                    summary = f"""
                    🌟 Hey {username.capitalize()}! Here's your sleep snapshot for this week:

                    - Recommended total sleep for this period of {count_days} days is **{recommended_start_range}-{recommended_end_range} hrs**, you slept a total of **{total_sleep_week} hrs** in this duration of {count_days} day(s).
                    - Your average sleep during the period of {count_days} days is **{avg_sleep} hrs** and the recommended sleep for a {meta['age']} year old ({meta['gender']}) is **{min_sleep}-{max_sleep} hrs**.
                    - {streak_display}
                    
                    {sleep_feedback}
                    """

                  # Display the sleep feedback and summary
                   # st.write(sleep_feedback)  # This will show the feedback (including the new message for exceeding)
                    st.markdown(summary)      # This will display the detailed summary without repeating the quote

                    st.session_state.generate_summary = False

                   # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()



# ------------------------
# Main Page Logic
# ------------------------

if "username" not in st.session_state:
    # App description
    st.markdown("""
    ## 🌙 Welcome to **Sleep Tracker**   
    Track your sleep, build streaks, and get personalized feedback to become a **Sleep Superstar**!  
    Just log your bedtime & wake time – we’ll take care of the rest 💤✨
    """)
    st.image("https://i.pinimg.com/originals/56/62/36/566236fb87c21b6f23512a429dd6476b.jpg", width=800)

    st.markdown("#### 👋 Let's get started!")
    st.markdown("Type your name to log in or create a profile. This helps us personalize your sleep journey. 😴")
    raw_username = st.text_input("Enter your name to continue:", key="username_input").strip()
    normalized_username = raw_username.lower()

    if raw_username:
        st.session_state["username"] = normalized_username
        st.session_state["display_name"] = raw_username  # keep original casing for display
        st.rerun()

# Once username is in session state, continue as normal
if "username" in st.session_state:
    username = st.session_state["username"]
    display_name = st.session_state.get("display_name", username.title())
    
    
    if username in sleep_data:
        main_page(username)
    else:
        st.subheader("🆕 New user detected! Let’s create your profile 👇")
        st.markdown("We use this info to give you **accurate sleep recommendations** based on your age & gender.")        
        with st.form("new_user_form", clear_on_submit=False):
            gender = st.selectbox("Select your gender:", ["Male", "Female"])
            age = st.number_input("Enter your age:", min_value=1, max_value=100, step=1)
            submit = st.form_submit_button("Save Profile")
        
        if submit:
            sleep_data[username] = {
                "meta": {"gender": gender, "age": age},
                "entries": []
            }
            save_data()
            st.success("Profile saved! Redirecting to login...")
            st.rerun()
