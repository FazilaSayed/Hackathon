import streamlit as st
import http.client
import json
import requests
import pandas as pd
import plotly.graph_objects as go
import random
import plotly.express as px

# API Keys
API_ID = "00b1404a"
API_KEY = "b563211867bc021d51476b07eeab5a27"
RAPIDAPI_KEY = "9028d9d0cbmsha063286417ea661p18eda3jsn952984914b8c"

# Init session state
if "food_log" not in st.session_state:
    st.session_state.food_log = []
if "water_intake" not in st.session_state:
    st.session_state.water_intake = 0.0
if "nutrition_plans" not in st.session_state:
    st.session_state.nutrition_plans = []

# Page config
st.set_page_config(page_title="Personalized Nutrition & Hydration Tracker", layout="wide")

st.markdown("<h1 style='text-align:center;'>🥗 Personalized Nutrition & Hydration Advisor</h1>", unsafe_allow_html=True)
st.sidebar.header("🧭 Feature Navigation")
selected_tab = st.sidebar.radio("Choose Feature:", ["📘 Calorie Tracker", "📗 Nutrition Planner"])
selected_tab = selected_tab.split(" ", 1)[1]

# ========== Calorie Tracker ==========
if selected_tab == "Calorie Tracker":
    st.header("📘 Calorie Tracker")
    with st.expander("Log Food Intake & Water", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            food_item = st.text_input("Food Item:")
            unit = st.selectbox("Unit", ["cup", "slice", "gram", "piece", "tablespoon", "teaspoon"])
            qty = st.number_input("Quantity", min_value=1, step=1)
            brand = st.text_input("Brand (Optional):")
        with col2:
            water_intake = st.number_input("Water Intake (liters)", min_value=0.0, step=0.1)
            add_food = st.button("Add Entry")

        if add_food and food_item:
            query = f"{qty} {unit} {food_item}" + (f" {brand}" if brand else "")
            headers = {
                "x-app-id": API_ID,
                "x-app-key": API_KEY,
                "Content-Type": "application/json"
            }
            res = requests.post("https://trackapi.nutritionix.com/v2/natural/nutrients",
                                headers=headers, json={"query": query})
            if res.status_code == 200:
                fdata = res.json()["foods"][0]
                st.session_state.food_log.append({
                    "Food Name": fdata["food_name"],
                    "Quantity": fdata["serving_qty"],
                    "Unit": fdata["serving_unit"],
                    "Calories": fdata["nf_calories"],
                    "Carbohydrates (g)": fdata["nf_total_carbohydrate"],
                    "Protein (g)": fdata["nf_protein"],
                    "Fat (g)": fdata["nf_total_fat"],
                    "Cholesterol (mg)": fdata.get("nf_cholesterol", 0),
                    "Sodium (mg)": fdata.get("nf_sodium", 0),
                    "Potassium (mg)": fdata.get("nf_potassium", 0),
                    

                })
                st.session_state.water_intake += water_intake
                st.success(f"{food_item} added to your daily log!")
            else:
                st.error("Failed to fetch nutrition data.")


    
    if st.session_state.food_log:
        st.subheader("📝 Daily Log")
        df_log = pd.DataFrame(st.session_state.food_log)
        st.dataframe(df_log)

        if st.button("Generate Summary"):
            summary = df_log[["Calories", "Carbohydrates (g)", "Protein (g)", "Fat (g)"]].sum()
        
            # Create 3 sections: left spacer, main content, right spacer
            left, main, right = st.columns([1, 2, 1])  # 1:2:1 ratio for centering
        
            with main:
                # Create 4 columns inside the centered section
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Calories", f"{summary['Calories']:.0f} kcal")
                col2.metric("Carbs", f"{summary['Carbohydrates (g)']:.1f} g")
                col3.metric("Protein", f"{summary['Protein (g)']:.1f} g")
                col4.metric("Fat", f"{summary['Fat (g)']:.1f} g")
        
                st.subheader("Summary of Intake")
                st.write(summary)

            
            # Macronutrient Pie Chart
            st.subheader("Macronutrient Distribution")
            pie_fig = px.pie(
                names=["Carbohydrates", "Protein", "Fat"],
                values=summary[["Carbohydrates (g)", "Protein (g)", "Fat (g)"]],
                title="Macronutrient Distribution"
            )
            pie_fig.update_layout(width=1000, height=500)  # ~20x10 inches in pixels (1 inch ≈ 50 px)
            st.plotly_chart(pie_fig)
            
            # Micronutrient Bar Chart
            micronutrients = df_log[["Cholesterol (mg)", "Sodium (mg)", "Potassium (mg)"]].sum()
            bar_fig = px.bar(
                x=micronutrients.index,
                y=micronutrients.values,
                title="Micronutrient Levels",
                labels={"x": "Micronutrient", "y": "Amount"}
            )
            bar_fig.update_layout(width=1000, height=500)
            st.subheader("Micronutrient Levels")
            st.plotly_chart(bar_fig)
            
            # Water Intake Gauge Chart
            st.subheader("💧 Water Intake")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=st.session_state.water_intake,
                title={'text': "Water Intake (L)"},
                gauge={
                    'axis': {'range': [0, 5]},
                    'bar': {'color': "blue"},
                    'steps': [
                        {'range': [0, 2], 'color': "lightgray"},
                        {'range': [2, 4], 'color': "lightblue"},
                        {'range': [4, 5], 'color': "skyblue"}
                    ]
                }
            ))
            fig.update_layout(width=1000, height=500)
            st.plotly_chart(fig, use_container_width=False)

# ========== Nutrition Planner ==========
elif selected_tab == "Nutrition Planner":
    st.header("📗 Nutrition Planner")

    # Basic Inputs
    goal = st.selectbox("Your goal:", ["Lose weight", "Maintain weight", "Gain weight"])
    gender = st.selectbox("Gender", ["Male", "Female"])
    age = st.number_input("Age", min_value=5, max_value=100, step=1)
    height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, step=0.5)
    dietary_restrictions = st.multiselect("Dietary restrictions?", ["Vegetarian", "Vegan", "Keto", "Gluten-Free", "Dairy-Free"])
    current_weight = st.number_input("Current Weight (kg)", min_value=30.0, step=0.5)
    target_weight = st.number_input("Target Weight (kg)", min_value=30.0, step=0.5)
    activity_level = st.selectbox("Daily Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])
    days_plan = st.slider("Number of days", min_value=1, max_value=7, value=1)

    def calculate_bmr(gender, weight, height, age, activity):
        # Mifflin-St Jeor BMR
        base_bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == "Male" else -161)

        # Gender and age adjustments
        if gender == "Male" and age < 18:
            base_bmr *= 1.1
        elif gender == "Male" and 18 <= age <= 50:
            base_bmr *= 1.05
        elif gender == "Male" and age > 50:
            base_bmr *= 0.98
        elif gender == "Female" and age < 18:
            base_bmr *= 1.05
        elif gender == "Female" and 18 <= age <= 50:
            base_bmr *= 0.9
        elif gender == "Female" and age > 50:
            base_bmr *= 0.85

        # Activity multiplier
        activity_factor = {
            "Sedentary": 1.2,
            "Light": 1.375,
            "Moderate": 1.55,
            "Active": 1.725,
            "Very Active": 1.9
        }.get(activity, 1.2)

        return int(base_bmr * activity_factor)

    if st.button("Get Nutrition Plan"):
        st.session_state.nutrition_plans.clear()
        with st.spinner("Fetching personalized plans..."):
            for i in range(days_plan):
                try:
                    calorie_adjustment = calculate_bmr(gender, current_weight, height, age, activity_level)
                    conn = http.client.HTTPSConnection("ai-workout-planner-exercise-fitness-nutrition-guide.p.rapidapi.com")
                    payload = json.dumps({
                        "goal": goal,
                        "dietary_restrictions": dietary_restrictions,
                        "current_weight": current_weight,
                        "target_weight": target_weight,
                        "daily_activity_level": activity_level,
                        "manual_calorie_override": calorie_adjustment,
                        "lang": "en"
                    })
                    headers = {
                        'x-rapidapi-key': RAPIDAPI_KEY,
                        'x-rapidapi-host': "ai-workout-planner-exercise-fitness-nutrition-guide.p.rapidapi.com",
                        'Content-Type': "application/json"
                    }
                    conn.request("POST", "/nutritionAdvice?noqueue=1", payload, headers)
                    res = conn.getresponse()
                    data = res.read()
                    conn.close()
                    response = json.loads(data.decode("utf-8"))

                    if response.get("status") == "success":
                        plan = response.get("result", {})
                        if plan.get("meal_suggestions"):
                            plan["gender"] = gender
                            plan["age"] = age
                            plan["height"] = height
                            plan["calorie_override"] = calorie_adjustment
                            st.session_state.nutrition_plans.append(plan)
                        else:
                            st.warning(f"Day {i+1} returned no meal suggestions.")
                    else:
                        st.error(f"Error for Day {i+1}: {response.get('message', 'Unknown')}")
                except Exception as e:
                    st.error(f"Day {i+1} failed: {str(e)}")

    # Display Plans
    if st.session_state.nutrition_plans:
        day_options = [f"Day {i+1}" for i in range(len(st.session_state.nutrition_plans))]
        selected_day = st.selectbox("View Nutrition Plan:", day_options)
        idx = int(selected_day.split(" ")[1]) - 1
        plan = st.session_state.nutrition_plans[idx]

        st.subheader(f"📅 {selected_day}")
        st.markdown(f"**Goal:** {plan.get('goal')}")
        st.markdown(f"**Calories Requirement (based on age, gender, height):** `{plan.get('calorie_override')} kcal`")
        st.markdown(f"**Gender:** {plan.get('gender')}")
        st.markdown(f"**Age:** {plan.get('age')}")
        st.markdown(f"**Height:** {plan.get('height')} cm")

        # Macronutrients
        macros = plan.get("macronutrients", {})
        st.markdown("### Macronutrient Breakdown")
        st.write(f"🍚 Carbs: {macros.get('carbohydrates')}")
        st.write(f"🥩 Proteins: {macros.get('proteins')}")
        st.write(f"🥑 Fats: {macros.get('fats')}")

        # Meal Suggestions
        st.markdown("### 🍽️ Meal Suggestions")
        for meal in plan.get("meal_suggestions", []):
            st.markdown(f"#### 🍴 {meal['meal']}")
            for suggestion in meal["suggestions"]:
                st.markdown(f"**{suggestion['name']}** - `{suggestion['calories']} kcal`")
                st.markdown("Ingredients:")
                st.markdown("\n".join([f"- {item}" for item in suggestion["ingredients"]]))

        # Fun SEO Section
        st.markdown("### 📝 Tip of the day!")
        st.markdown(f"**SEO Tip:** {plan.get('seo_title')}")
        st.markdown(f"**Description:** {plan.get('seo_content')}")
        # Detailed Fun Summary
        st.markdown("### 📊 Personalized Summary")
        st.success(f"""
        🔍 Based on your inputs:
        
        - **Age:** {plan.get('age')} years
        - **Gender:** {plan.get('gender')}
        - **Height:** {plan.get('height')} cm
        - **Current Weight:** {current_weight} kg
        - **Target Weight:** {target_weight} kg
        - **Activity Level:** {activity_level}
        - **Goal:** {goal}

        💡 Your estimated **Basal Metabolic Rate (BMR)** is: **{int(plan.get('calorie_override') / {
            "Sedentary": 1.2,
            "Light": 1.375,
            "Moderate": 1.55,
            "Active": 1.725,
            "Very Active": 1.9
        }[activity_level])} kcal/day** — the calories you'd burn doing nothing all day!

        🔥 But with your **{activity_level.lower()} lifestyle**, your actual daily calorie need is: **{plan.get('calorie_override')} kcal**.

        🍱 A perfect meal plan has been crafted for **Day {idx+1}** that aligns with your **{goal.lower()}** goal and dietary preference of **{' / '.join(dietary_restrictions) if dietary_restrictions else 'No restrictions'}**.

        Keep going, your health goals are within reach! 💪
        """)

