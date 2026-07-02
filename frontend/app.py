import streamlit as st
import pandas as pd
from datetime import date, datetime, time
from decimal import Decimal
from frontend.utils.api_client import api_client
from frontend.utils.charts import COLORS, create_timeline_chart, apply_sleek_theme

# Page Config
st.set_page_config(
    page_title="Personal Analytics System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling
st.markdown("""
<style>
    /* Main body background styling */
    .reportview-container {
        background: #121214;
    }
    
    /* Sleek metric card styling */
    .metric-card {
        background: rgba(30, 30, 36, 0.65);
        border: 1px solid rgba(108, 92, 231, 0.15);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        transition: transform 0.2s ease-in-out;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(108, 92, 231, 0.4);
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(45deg, #6C5CE7, #00CEC9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    
    .metric-label {
        font-size: 14px;
        color: #A4A4AB;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Subtitle and headings styling */
    .glow-header {
        font-size: 40px;
        font-weight: 900;
        background: linear-gradient(135deg, #A29BFE 0%, #6C5CE7 50%, #00CEC9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    /* Style supplement pill */
    .supp-pill {
        display: inline-block;
        background: rgba(108, 92, 231, 0.15);
        border: 1px solid rgba(108, 92, 231, 0.3);
        border-radius: 20px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 13px;
        color: #E1E1E6;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("<h1 class='glow-header'>📊 Personal Analytics System</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #A4A4AB; font-size: 16px; margin-top: -15px;'>Self-hosted tracking of habits, physical health, work, and finances.</p>", unsafe_allow_html=True)
st.write("---")

# Sidebar Status
st.sidebar.markdown("### 🔌 System Connections")
try:
    backend_status = api_client._get("/")
    if backend_status.get("status") == "healthy":
        st.sidebar.success("Backend: Connected ✅")
    else:
        st.sidebar.error("Backend: Error ⚠️")
except Exception:
    st.sidebar.error("Backend: Disconnected ❌")

st.sidebar.markdown("### ⚙️ Navigation Tips")
st.sidebar.info(
    "Use the sidebar navigation pages to view detailed dashboards and charts for Physical Activity, Finances, Learning, and Goals."
)

# Initialize Session State for Supplements
if "supplements_list" not in st.session_state:
    st.session_state.supplements_list = []

# Main Page Layout: Three Tabs
tab1, tab2, tab3 = st.tabs(["📝 Daily Questionnaire", "📈 Quick Insights & Summary", "📖 Daily Logs Explorer"])

# ==================== TAB 1: DAILY QUESTIONNAIRE ====================
with tab1:
    st.subheader("Daily Subjective Log")
    
    # Form Date
    log_date = st.date_input("Select Date", date.today())
    
    # Check if a log already exists for this date to pre-populate
    existing_log = None
    existing_nutrition = None
    try:
        existing_log = api_client.get_daily_log(log_date)
    except Exception:
        pass # Not found or backend down

    try:
        existing_nutrition = api_client.get_nutrition_log(log_date)
    except Exception:
        pass

    # Pre-populate defaults
    def_diary = ""
    def_workout_type = "None"
    def_sleep_start = datetime.combine(log_date, time(23, 0))
    def_sleep_end = datetime.combine(log_date, time(7, 0))

    # Nutrition defaults
    def_water = None
    def_coffee = None
    def_coffee_type = "Filter"
    def_fruits = None
    def_vegetables = None
    def_harmful = ""

    if existing_nutrition:
        def_water = existing_nutrition.get("water_cups")
        def_coffee = existing_nutrition.get("coffee_cups")
        def_coffee_type = existing_nutrition.get("coffee_type") or "Filter"
        def_fruits = existing_nutrition.get("fruits_servings")
        def_vegetables = existing_nutrition.get("vegetables_servings")
        def_harmful = existing_nutrition.get("harmful_foods") or ""

    if existing_log:
        st.info(f"ℹ️ A log for {log_date} already exists. Submitting will update the entry.")
        def_diary = existing_log.get("diary_text") or ""
        def_workout_type = existing_log.get("workout_type") or "None"
        
        # Load times
        if existing_log.get("sleep_start"):
            def_sleep_start = datetime.fromisoformat(existing_log["sleep_start"].replace("Z", "+00:00"))
        if existing_log.get("sleep_end"):
            def_sleep_end = datetime.fromisoformat(existing_log["sleep_end"].replace("Z", "+00:00"))
            
        # Load existing supplements into session state on date change (if changed)
        if "loaded_date" not in st.session_state or st.session_state.loaded_date != log_date:
            st.session_state.supplements_list = [
                {"name": s["name"], "dosage": float(s["dosage"]), "unit": s["unit"]}
                for s in existing_log.get("supplements", [])
            ]
            st.session_state.loaded_date = log_date
    else:
        if "loaded_date" not in st.session_state or st.session_state.loaded_date != log_date:
            st.session_state.supplements_list = []
            st.session_state.loaded_date = log_date

    # Columns for organized form layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧠 Mood & Work")
        has_mood = st.checkbox("Record Subjective Mood Score?", value=(existing_log is not None and existing_log.get("mood_score") is not None))
        if has_mood:
            default_mood = existing_log.get("mood_score") if (existing_log and existing_log.get("mood_score") is not None) else 7
            mood_score = st.slider("Subjective experience of the day (1-10)", 1, 10, int(default_mood), help="1 = Terrible, 10 = Outstanding")
        else:
            mood_score = None
        
        diary_text = st.text_area(
            "Diary entry / Notes for NLP analysis", 
            def_diary, 
            placeholder="Write about your thoughts, feelings, correlations, events..."
        )
        
        has_work = st.checkbox("Record Work Hours?", value=(existing_log is not None and existing_log.get("work_hours") is not None))
        if has_work:
            default_work = existing_log.get("work_hours") if (existing_log and existing_log.get("work_hours") is not None) else 8.0
            work_hours = st.slider("Hours worked", 0.0, 24.0, float(default_work), step=0.5)
        else:
            work_hours = None

        st.markdown("### 🛌 Sleep Timing & Quality")
        log_sleep = st.checkbox(
            "Log Sleep Window today?", 
            value=(existing_log is not None and (existing_log.get("sleep_start") is not None or existing_log.get("sleep_end") is not None))
        )
        if log_sleep:
            sleep_start_time = st.time_input("Going to sleep time", def_sleep_start.time(), step=300)
            sleep_end_time = st.time_input("Waking up time", def_sleep_end.time(), step=300)
            
            sleep_start_dt = datetime.combine(log_date, sleep_start_time)
            sleep_end_dt = datetime.combine(log_date, sleep_end_time)
            
            sleep_start_iso = sleep_start_dt.isoformat()
            sleep_end_iso = sleep_end_dt.isoformat()
            
            default_sleep_quality = existing_log.get("sleep_quality") if (existing_log and existing_log.get("sleep_quality") is not None) else 7
            sleep_quality = st.slider("Sleep Quality (1-10)", 1, 10, int(default_sleep_quality), help="1 = Terrible, 10 = Outstanding")
        else:
            sleep_start_iso = None
            sleep_end_iso = None
            sleep_quality = None

    with col2:
        st.markdown("### 🏃 Physical Activity")
        has_steps = st.checkbox("Record Steps Count?", value=(existing_log is not None and existing_log.get("steps") is not None))
        if has_steps:
            default_steps = existing_log.get("steps") if (existing_log and existing_log.get("steps") is not None) else 8000
            steps = st.number_input("Steps count", min_value=0, value=int(default_steps), step=1)
        else:
            steps = None
            
        has_workout = st.checkbox("Record Workout Duration?", value=(existing_log is not None and existing_log.get("workout_minutes") is not None))
        if has_workout:
            default_workout = existing_log.get("workout_minutes") if (existing_log and existing_log.get("workout_minutes") is not None) else 45
            workout_minutes = st.slider("Dedicated workout duration (minutes)", 0, 180, int(default_workout), step=5)
            
            workout_type = st.selectbox(
                "Workout Type", 
                ["None", "strength", "moderate intensity aerobic workouts", "HIIT"],
                index=["None", "strength", "moderate intensity aerobic workouts", "HIIT"].index(def_workout_type) if def_workout_type in ["None", "strength", "moderate intensity aerobic workouts", "HIIT"] else 0
            )
        else:
            workout_minutes = None
            workout_type = None
            
        has_snacks = st.checkbox("Record Exercise Snacks?", value=(existing_log is not None and existing_log.get("exercise_snacks_count") is not None))
        if has_snacks:
            default_snacks = existing_log.get("exercise_snacks_count") if (existing_log and existing_log.get("exercise_snacks_count") is not None) else 0
            exercise_snacks_count = st.slider("Exercise snacks count (<5 mins, squats/pushups)", 0, 20, int(default_snacks), step=1)
        else:
            exercise_snacks_count = None

        st.markdown("### 💊 Supplements & Dosage")
        
        # Predefined mapping for easy dosage/unit suggestions
        supp_defaults = {
            "Vitamin D3": (2000.0, "UI"),
            "Omega 3": (1000.0, "mg"),
            "Creatine": (5.0, "g"),
            "Glycine": (3.0, "g"),
            "L-theanine": (200.0, "mg"),
            "multivitamins": (1.0, "pills"),
        }
        
        supp_choice = st.selectbox(
            "Select Supplement",
            ["Choose...", "Vitamin D3", "Omega 3", "Creatine", "Glycine", "L-theanine", "multivitamins", "Custom..."],
            key="supp_choice_input"
        )

        # Determine defaults based on selection
        default_dose = 0.0
        default_unit_idx = 0
        units_list = ["UI", "mg", "g", "mcg", "pills"]

        if supp_choice in supp_defaults:
            dose, unit = supp_defaults[supp_choice]
            default_dose = dose
            if unit in units_list:
                default_unit_idx = units_list.index(unit)

        supp_col1, supp_col2, supp_col3 = st.columns([2, 1, 1])
        with supp_col1:
            if supp_choice == "Custom...":
                supp_name = st.text_input("Custom Supplement Name", placeholder="e.g. Magnesium", key="supp_name_custom_input")
            else:
                supp_name = supp_choice if supp_choice != "Choose..." else ""
                st.text_input("Supplement Name", value=supp_name, disabled=True, key="supp_name_disabled")
        with supp_col2:
            supp_dose = st.number_input("Dosage", min_value=0.0, value=default_dose, step=1.0 if default_dose < 10.0 else 50.0, key=f"supp_dose_{supp_choice}")
        with supp_col3:
            supp_unit = st.selectbox("Unit", units_list, index=default_unit_idx, key=f"supp_unit_{supp_choice}")

        if st.button("➕ Add Supplement"):
            if supp_name.strip() and supp_dose > 0:
                st.session_state.supplements_list.append({
                    "name": supp_name.strip(),
                    "dosage": supp_dose,
                    "unit": supp_unit
                })
                st.toast(f"Added {supp_name} {supp_dose} {supp_unit}!")
            else:
                st.warning("Please specify both a supplement name and a dosage greater than 0.")

        # Show currently added supplements
        if st.session_state.supplements_list:
            st.write("Current supplements for today:")
            for idx, item in enumerate(st.session_state.supplements_list):
                st.markdown(
                    f"<span class='supp-pill'>{item['name']} - {item['dosage']} {item['unit']}</span>", 
                    unsafe_allow_html=True
                )
            if st.button("🧹 Clear Supplements"):
                st.session_state.supplements_list = []
                st.rerun()

    # Nutrition & Hydration Section
    st.write("---")
    st.markdown("### 🥦 Nutrition & Hydration")
    col_nut1, col_nut2 = st.columns(2)

    with col_nut1:
        has_water = st.checkbox("Record Water Intake?", value=(existing_nutrition is not None and existing_nutrition.get("water_cups") is not None))
        if has_water:
            default_water = existing_nutrition.get("water_cups") if (existing_nutrition and existing_nutrition.get("water_cups") is not None) else 8.0
            water_cups = st.slider("Water intake (cups)", 0.0, 20.0, float(default_water), step=0.5, key="water_cups_input")
        else:
            water_cups = None
            
        has_coffee = st.checkbox("Record Coffee Intake?", value=(existing_nutrition is not None and existing_nutrition.get("coffee_cups") is not None))
        if has_coffee:
            default_coffee = existing_nutrition.get("coffee_cups") if (existing_nutrition and existing_nutrition.get("coffee_cups") is not None) else 1.0
            coffee_cups = st.slider("Coffee intake (cups)", 0.0, 10.0, float(default_coffee), step=0.5, key="coffee_cups_input")
            
            coffee_type = st.selectbox(
                "Coffee Type",
                ["Filter", "Espresso", "Instant", "Decaf"],
                index=["Filter", "Espresso", "Instant", "Decaf"].index(def_coffee_type) if def_coffee_type in ["Filter", "Espresso", "Instant", "Decaf"] else 0,
                key="coffee_type_input"
            )
        else:
            coffee_cups = None
            coffee_type = None

    with col_nut2:
        has_fruits = st.checkbox("Record Fruits?", value=(existing_nutrition is not None and existing_nutrition.get("fruits_servings") is not None))
        if has_fruits:
            default_fruits = existing_nutrition.get("fruits_servings") if (existing_nutrition and existing_nutrition.get("fruits_servings") is not None) else 2.0
            fruits_servings = st.slider("Fruits intake (servings)", 0.0, 10.0, float(default_fruits), step=0.5, key="fruits_servings_input")
        else:
            fruits_servings = None
            
        has_veggies = st.checkbox("Record Vegetables?", value=(existing_nutrition is not None and existing_nutrition.get("vegetables_servings") is not None))
        if has_veggies:
            default_veggies = existing_nutrition.get("vegetables_servings") if (existing_nutrition and existing_nutrition.get("vegetables_servings") is not None) else 3.0
            vegetables_servings = st.slider("Vegetables intake (servings)", 0.0, 10.0, float(default_veggies), step=0.5, key="vegetables_servings_input")
        else:
            vegetables_servings = None
            
        harmful_foods = st.text_input(
            "Harmful / Junk foods notes",
            value=def_harmful,
            placeholder="e.g. 2 cookies, 1 slice of pizza",
            key="harmful_foods_input"
        )

    # Form Submission & Deletion
    st.write("---")
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        if st.button("💾 Submit Daily Log", use_container_width=True):
            payload = {
                "date": log_date.isoformat(),
                "mood_score": mood_score,
                "sleep_quality": sleep_quality,
                "diary_text": diary_text.strip() if diary_text.strip() else None,
                "sleep_start": sleep_start_iso,
                "sleep_end": sleep_end_iso,
                "steps": steps,
                "workout_minutes": workout_minutes,
                "workout_type": workout_type if workout_type != "None" else None,
                "exercise_snacks_count": exercise_snacks_count,
                "work_hours": work_hours,
                "supplements": st.session_state.supplements_list
            }
            nutrition_payload = {
                "date": log_date.isoformat(),
                "water_cups": water_cups,
                "coffee_cups": coffee_cups,
                "coffee_type": coffee_type if coffee_cups else None,
                "fruits_servings": fruits_servings,
                "vegetables_servings": vegetables_servings,
                "harmful_foods": harmful_foods.strip() if harmful_foods.strip() else None
            }
            try:
                api_client.upsert_daily_log(payload)
                api_client.upsert_nutrition_log(nutrition_payload)
                st.success(f"🎉 Daily Log & Nutrition for {log_date} successfully saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit daily log/nutrition: {e}")
                
    with col_sub2:
        if existing_log or existing_nutrition:
            if st.button("🗑️ Delete Daily Log for Selected Date", use_container_width=True, type="secondary"):
                try:
                    if existing_log:
                        api_client.delete_daily_log(log_date)
                    if existing_nutrition:
                        api_client.delete_nutrition_log(log_date)
                    st.warning(f"🗑️ Daily Log and Nutrition for {log_date} successfully deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete daily log: {e}")

# ==================== TAB 2: INSIGHTS & SUMMARY ====================
with tab2:
    st.subheader("Recent Trends & Summary Statistics")
    
    # Load past logs
    recent_logs = []
    try:
        recent_logs = api_client.get_daily_logs()
    except Exception:
        st.warning("Could not load recent logs from the backend. Make sure the database is up.")

    if not recent_logs:
        st.info("No logs collected yet. Submit your first Daily Log to see summary statistics here!")
    else:
        df_logs = pd.DataFrame(recent_logs)
        df_logs['date'] = pd.to_datetime(df_logs['date'])
        
        # Calculate summary metrics for the last 7 entries (drop nulls to represent correct statistics)
        df_last_7 = df_logs.head(7)
        avg_mood = df_last_7['mood_score'].dropna().mean()
        avg_steps = df_last_7['steps'].dropna().mean()
        avg_workouts = df_last_7['workout_minutes'].dropna().mean()
        avg_work = df_last_7['work_hours'].dropna().mean()

        # Display beautifully styled cards
        card_col1, card_col2, card_col3, card_col4 = st.columns(4)
        
        with card_col1:
            val = f"{avg_mood:.1f} / 10" if pd.notna(avg_mood) else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">Avg Mood (7d)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col2:
            val = f"{int(avg_steps):,}" if pd.notna(avg_steps) else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">Avg Steps (7d)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col3:
            val = f"{avg_workouts:.1f} m" if pd.notna(avg_workouts) else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">Avg Workout (7d)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col4:
            val = f"{avg_work:.1f} h" if pd.notna(avg_work) else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">Avg Work (7d)</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")

        # Display Mood vs Steps Timeline Chart
        chart_df = df_logs.head(30) # Show last 30 days
        st.subheader("Last 30 Days Mood vs. Daily Steps")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            df_m_plot = chart_df[['date', 'mood_score']].dropna()
            if df_m_plot.empty:
                st.info("No mood records available to plot.")
            else:
                fig_mood = create_timeline_chart(df_m_plot, "date", "mood_score", "Daily Mood Rating", "Mood (1-10)", COLORS["primary"])
                st.plotly_chart(fig_mood, use_container_width=True)
        with col_c2:
            df_s_plot = chart_df[['date', 'steps']].dropna()
            if df_s_plot.empty:
                st.info("No steps records available to plot.")
            else:
                fig_steps = create_timeline_chart(df_s_plot, "date", "steps", "Daily Steps Count", "Steps", COLORS["accent"], is_bar=True)
                st.plotly_chart(fig_steps, use_container_width=True)

# ==================== TAB 3: DAILY LOGS EXPLORER ====================
with tab3:
    st.subheader("📖 Past Daily Logs Search & Explorer")
    
    # Fetch all logs
    try:
        all_logs = api_client.get_daily_logs()
    except Exception:
        all_logs = []
        
    if not all_logs:
        st.info("No daily logs recorded yet. Start entering them in the questionnaire!")
    else:
        # Search filter
        search_query = st.text_input("🔍 Search logs by keyword (diary notes, workout type, supplement name)", "")
        
        filtered_logs = []
        for log in all_logs:
            match = False
            # Check date
            date_str = str(log.get("date"))
            # Check diary notes
            diary = (log.get("diary_text") or "").lower()
            # Check workout type
            w_type = (log.get("workout_type") or "").lower()
            # Check supplements names
            supps = " ".join([s.get("name", "").lower() for s in log.get("supplements", [])])
            
            combined_text = f"{date_str} {diary} {w_type} {supps}"
            
            if not search_query.strip() or search_query.lower() in combined_text:
                filtered_logs.append(log)
                
        if not filtered_logs:
            st.warning("No matches found for your search query.")
        else:
            st.write(f"Showing {len(filtered_logs)} logs:")
            
            for log in filtered_logs:
                log_date_val = datetime.strptime(log["date"], "%Y-%m-%d").date()
                with st.expander(f"📅 Log for {log['date']} (Mood: {log.get('mood_score') or 'N/A'}, Sleep Quality: {log.get('sleep_quality') or 'N/A'})"):
                    col_l1, col_l2 = st.columns(2)
                    with col_l1:
                        st.markdown(f"**🧠 Subjective Mood**: `{log.get('mood_score') or 'N/A'}`")
                        st.markdown(f"**🛌 Sleep Quality**: `{log.get('sleep_quality') or 'N/A'}`")
                        st.markdown(f"**💼 Work time**: `{log.get('work_hours') or 'N/A'}` hours")
                    with col_l2:
                        # Sleep window
                        if log.get("sleep_start") and log.get("sleep_end"):
                            st.markdown(f"**⏰ Sleep Window**: {log['sleep_start'][11:16]} to {log['sleep_end'][11:16]}")
                        else:
                            st.markdown("**⏰ Sleep Window**: Not recorded")
                        st.markdown(f"**🏃 Physical**: `{log.get('steps') or 'N/A'}` steps, `{log.get('workout_minutes') or 'N/A'}` min workout (`{log.get('workout_type') or 'None'}`)")
                        st.markdown(f"**⏰ Exercise snacks count**: `{log.get('exercise_snacks_count') or 'N/A'}`")
                            
                        # Supplements
                        supps_list = log.get("supplements", [])
                        if supps_list:
                            st.markdown("**💊 Supplements**:")
                            for s in supps_list:
                                st.markdown(f"- {s['name']}: {float(s['dosage']):g} {s['unit']}")
                        else:
                            st.markdown("**💊 Supplements**: None")
                            
                    # Diary Text
                    if log.get("diary_text"):
                        st.info(f"**Notes**:\n{log['diary_text']}")
                    
                    # Delete button directly inside explorer!
                    if st.button("🗑️ Delete Log Entry", key=f"del_explorer_{log['date']}", type="primary"):
                        try:
                            api_client.delete_daily_log(log_date_val)
                            st.warning(f"🗑️ Daily Log for {log['date']} successfully deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete daily log: {e}")
