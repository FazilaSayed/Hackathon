import requests
import streamlit as st
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="AI Workout Planner", page_icon="💪", layout="wide")
st.title("Personalized Workout Planner")
st.markdown("Get a **smart, personalized workout plan**. Select your preferences and hit generate!")
st.image("https://i0.wp.com/www.muscleandfitness.com/wp-content/uploads/2019/07/Hands-Clapping-Chaulk-Kettlebell.jpg?quality=86&strip=all", use_container_width=True)

# Cache with a unique key for input combo to avoid repeated API calls
@st.cache_data(show_spinner="Fetching your customized workout plan...")
def call_ai_workout_api(goal, fitness_level, preferences, days_per_week, session_duration, plan_duration_weeks):
    payload = {
        "goal": goal,
        "fitness_level": fitness_level,
        "preferences": preferences,
        "health_conditions": ["None"],
        "schedule": {
            "days_per_week": days_per_week,
            "session_duration": session_duration
        },
        "plan_duration_weeks": plan_duration_weeks,
        "lang": "en"
    }

    url = "https://ai-workout-planner-exercise-fitness-nutrition-guide.p.rapidapi.com/generateWorkoutPlan"
    headers = {
        "x-rapidapi-key": "19eb26f807msh7728f6f69d08bd7p15da6djsn52e1b70e5329",
        "x-rapidapi-host": "ai-workout-planner-exercise-fitness-nutrition-guide.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, params={"noqueue": "1"})
        data = response.json()
        return data
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Sidebar Inputs
with st.sidebar:

    st.subheader("⚙️ Workout Preferences")
    goal = st.selectbox("🎯 Goal", ["Build muscle", "Lose weight", "Increase endurance"])
    fitness_level = st.selectbox("💪 Fitness Level", ["Beginner", "Intermediate", "Advanced"])
    preferences = st.multiselect("🏋️ Preferences", ["Weight training", "Cardio", "Yoga", "HIIT", "Pilates"])
    days_per_week = st.slider("🗓️ Days per Week", 1, 7, 4)
    session_duration = st.slider("⏱️ Session Duration (min)", 20, 120, 45)
    plan_duration_weeks = st.slider("⌚ Plan Duration (Weeks)", 1, 12, 4)

    submit = st.button("🌟 Submit")

# Toggle tabs after user submits
tabs = st.tabs(["📊 Generate Workout Plan", "🔢 Workout Summary"])

# Tab 1: Generate Plan
with tabs[0]:
    if submit:
        if not preferences:
            st.warning("Please select at least one workout preference.")
        else:
            plan = call_ai_workout_api(goal, fitness_level, preferences, days_per_week, session_duration, plan_duration_weeks)

            if plan.get("status") == "success":
                result = plan.get("result", {})
                schedule = result.get("schedule", {})
                exercises_by_day = result.get("exercises", [])

                st.success("✅ Workout plan generated successfully!")

                # Summary
                st.subheader("📋 Plan Summary")
                st.markdown(f"**Goal:** {result.get('goal', goal)}")
                st.markdown(f"**Fitness Level:** {result.get('fitness_level', fitness_level)}")
                st.markdown(f"**Duration:** {result.get('total_weeks', plan_duration_weeks)} weeks | "
                            f"**Days/Week:** {schedule.get('days_per_week', days_per_week)} | "
                            f"**Session:** {schedule.get('session_duration', session_duration)} mins")

                # Weekly Plan
                st.markdown("### 🗓️ Weekly Workout Plan")
                for day_plan in exercises_by_day:
                    with st.expander(f"🗓️ {day_plan['day']}"):
                        for ex in day_plan.get('exercises', []):
                            reps = ex.get('repetitions', 12)
                            sets = ex.get('sets', 3)
                            st.markdown(f"""
                            **🏋️ {ex['name']}**
                            - ⏱️ Duration: {ex['duration']}
                            - 🔁 Reps: {reps}
                            - 🧰 Sets: {sets}
                            - 💪 Equipment: {ex['equipment']}
                            """)

                # Summary Insights
                all_exercises = [ex['name'] for day in exercises_by_day for ex in day.get('exercises', [])]
                all_equipment = [ex['equipment'] for day in exercises_by_day for ex in day.get('exercises', []) if ex['equipment'] != "None"]

                st.markdown("### 📊 Insights")
                st.markdown(f"🧟 Unique Exercises: **{len(set(all_exercises))}**")
                st.markdown(f"🛠️ Equipment Needed: **{', '.join(set(all_equipment)) or 'None'}**")

            else:
                st.error(f"❌ Failed to generate workout plan. API status: **{plan.get('status', 'unknown')}**")
                st.code(plan)

# Tab 2: Workout Summary
with tabs[1]:
    st.subheader("🔢 Track Your Progress")

    st.subheader("👤 Personal Info")
    age = st.number_input("Age", min_value=10, max_value=100, value=25)
    gender = st.selectbox("Gender", ["Male", "Female"])
    height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
    weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=200, value=70)

    if st.button("🌟 Calculate BMR and BMI", key="bmr_bmi"):
        col1, col2 = st.columns(2)
        with col1:
            bmi = weight_kg / ((height_cm / 100) ** 2)
        
            # Categorize BMI
            if bmi < 18.5:
                bmi_status = "Underweight"
                bmi_color = "⚠️"
                bmi_msg = "You're a bit underweight. Focus on balanced nutrition and strength training."
            elif 18.5 <= bmi <= 24.9:
                bmi_status = "Healthy"
                bmi_color = "✅"
                bmi_msg = "Your BMI is in the healthy range. Keep it up!"
            elif 25 <= bmi <= 29.9:
                bmi_status = "Overweight"
                bmi_color = "🔶"
                bmi_msg = "You're slightly above the healthy range. Moderate exercise and mindful eating can help."
            else:
                bmi_status = "Obese"
                bmi_color = "🚨"
                bmi_msg = "BMI is high. Start with low-impact workouts and consult a health expert."
        
            # Display BMI metric with message and color emoji
            st.metric(f"{bmi_color} BMI ({bmi_status})", f"{bmi:.2f}")
            st.caption(bmi_msg)

        with col2:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == "Male" else -161)
            st.metric("BMR", f"{int(bmr)} cal/day")

        with st.expander("ℹ️ What are BMR and BMI?"):
            st.markdown("""
            - **BMR (Basal Metabolic Rate):** The number of calories your body burns at rest to maintain basic functions like breathing and heartbeat.
            - **BMI (Body Mass Index):** A simple number based on your height and weight that helps classify if you're underweight, normal, overweight, or obese.

            **BMI Categories (WHO):**
            - Underweight: BMI < 18.5  
            - Normal weight: 18.5 – 24.9  
            - Overweight: 25 – 29.9  
            - Obese: 30 and above

            *Ideal BMI range depends on age, muscle mass, and body type, but generally 18.5–24.9 is considered healthy.*  
            *BMR varies by gender, muscle mass, and age.*  
            """)

    st.subheader("🏋️ Completion Tracker")
    total_days = days_per_week * plan_duration_weeks
    completed_days = st.number_input("Number of Days You Completed the Workout", 0, total_days, 0)

    if st.button("📊 Generate Progress Summary", key="progress_summary"):
        progress = (completed_days / total_days) * 100 if total_days > 0 else 0
        st.markdown(f"### 🚀 You completed **{progress:.2f}%** of your plan!")

        if progress == 100:
            st.success("Incredible discipline! You've nailed every session. Time to level up your training!")
        elif progress > 75:
            st.info("Great job! You’re consistent and on track. Keep pushing!")
        elif progress > 50:
            st.warning("Good effort, but there’s room for more consistency. Stay focused!")
        else:
            st.error("You’ve started, but consistency is key. Let’s aim higher next week!")

        # 🎯 Personalized Workout Suggestions
        st.markdown("### 🎯 Personalized Suggestions Just for You")
        suggestion = ""

        if gender == "Male":
            if age < 18:
                suggestion = "Try bodyweight training (pushups, squats, planks). Make it fun—no heavy lifting needed yet!"
            elif 18 <= age <= 30:
                if weight_kg < 60:
                    suggestion = "Go for lean bulking: focus on compound lifts (bench, squats, deadlifts) + high-protein meals."
                elif weight_kg <= 80:
                    suggestion = "Great base! Alternate strength and HIIT days. Creatine and protein can help optimize results."
                else:
                    suggestion = "Focus on fat-burn and stamina—HIIT + moderate weights. Consider intermittent fasting if advised by a professional."
            elif age > 30:
                suggestion = "Mobility + strength + cardio balance is key. Mix yoga, resistance bands, and power walks."

        elif gender == "Female":
            if age < 18:
                suggestion = "Dance, yoga, and fun circuits are awesome! Build healthy habits without pressure."
            elif 18 <= age <= 30:
                if weight_kg < 50:
                    suggestion = "Glute bridges, resistance bands, and bodyweight HIIT can help tone and shape."
                elif weight_kg <= 70:
                    suggestion = "A mix of strength training (like dumbbell lunges), core focus, and Pilates works wonders."
                else:
                    suggestion = "Walking + low-impact HIIT (Zumba, kickboxing) + mindful eating = great combo!"
            elif age > 30:
                suggestion = "Core strengthening, light weights, flexibility routines (like Barre or yoga), and walking daily keep you sharp!"

        # Add based on height
        if height_cm < 150:
            suggestion += " Bonus tip: Shorter frame? Focus on posture and form—it makes all the difference!"
        elif height_cm > 185:
            suggestion += " Since you're tall, balance is important. Strengthen your core to support that extra leverage!"

        st.info(suggestion)

        st.markdown("**Tips:**")
        st.markdown("- Set workout reminders\n- Choose fun workouts\n- Track your mood and energy levels\n- Reward yourself for staying on track")
