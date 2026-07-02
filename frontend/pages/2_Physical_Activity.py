import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, time
from frontend.utils.api_client import api_client
from frontend.utils.charts import COLORS, create_timeline_chart, create_pie_chart

st.set_page_config(page_title="Physical Activity", page_icon="🏃", layout="wide")

# Custom CSS for modern visual design
st.markdown("""
<style>
    /* Styling card containers */
    .glass-card {
        background: rgba(30, 30, 36, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .workout-header {
        font-size: 18px;
        font-weight: 700;
        color: #00CEC9;
    }
</style>
""", unsafe_allow_html=True)

# Title styling
st.markdown("<h1 style='background: linear-gradient(135deg, #00CEC9, #0984E3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;'>🏃 Physical Activity & Workouts</h1>", unsafe_allow_html=True)
st.write("Track steps, dedicated workouts, exercise snacks, and detailed strength training.")

# Date Filters
col_d1, col_d2 = st.columns(2)
with col_d1:
    start_date = st.date_input("Start Date", date.today() - timedelta(days=30))
with col_d2:
    end_date = st.date_input("End Date", date.today())

# Fetch Data
try:
    logs = api_client.get_daily_logs(start_date=start_date, end_date=end_date)
except Exception:
    st.error("Could not fetch daily logs. Make sure the database is running.")
    logs = []

# Tabs for separate views
view_tab1, view_tab2 = st.tabs(["📊 Analytics & Daily Logs", "🏋️ Strength Workout Tracker (Strong-like)"])

with view_tab1:
    if not logs:
        st.info("No physical logs found for the selected range. Enter daily logs in the main page!")
    else:
        df = pd.DataFrame(logs)
        df['date'] = pd.to_datetime(df['date'])

        # Section 1: Step tracking and workout duration
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Step Count Trend")
            fig_steps = create_timeline_chart(
                df, "date", "steps", "Daily Steps Count", "Steps", COLORS["accent"], is_bar=True
            )
            st.plotly_chart(fig_steps, use_container_width=True)
            
        with col_c2:
            st.subheader("Dedicated Workouts Duration")
            fig_workouts = create_timeline_chart(
                df, "date", "workout_minutes", "Workout Duration (Minutes)", "Minutes", COLORS["secondary"]
            )
            st.plotly_chart(fig_workouts, use_container_width=True)

        st.write("---")

        # Section 2: Workout Type Breakdown & Exercise snacks
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            st.subheader("Workout Type Distribution")
            df_workouts = df[df["workout_type"].notna() & (df["workout_type"] != "None")]
            if df_workouts.empty:
                st.info("No dedicated workouts recorded in this date range.")
            else:
                fig_pie = create_pie_chart(
                    df_workouts, "workout_type", "workout_minutes", "Share of Workout Duration by Type"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
        with col_b2:
            st.subheader("Exercise Snacks (<5 minutes)")
            fig_snacks = create_timeline_chart(
                df, "date", "exercise_snacks_count", "Daily Exercise Snacks Count", "Count", COLORS["warning"], is_bar=True
            )
            st.plotly_chart(fig_snacks, use_container_width=True)
            
            # Summary statistics
            total_snacks = df["exercise_snacks_count"].sum()
            avg_snacks = df["exercise_snacks_count"].mean()
            st.markdown(f"""
            - **Total Exercise Snacks**: `{total_snacks}`
            - **Average Snacks/Day**: `{avg_snacks:.2f}`
            """)

    # Rapid Physical Logger Form
    st.write("---")
    with st.expander("➕ Rapid Log steps / workouts for another day"):
        log_date_rap = st.date_input("Target Log Date", date.today(), key="rapid_date")
        
        # Pre-populate if possible
        existing_log = None
        try:
            existing_log = api_client.get_daily_log(log_date_rap)
        except Exception:
            pass
            
        rap_steps = st.number_input("Steps count", min_value=0, value=int(existing_log.get("steps") or 8000) if existing_log else 8000, step=1, key="rap_steps")
        rap_workout = st.slider("Workout minutes", min_value=0, max_value=180, value=int(existing_log.get("workout_minutes") or 0) if existing_log else 0, step=5, key="rap_work")
        rap_type = st.selectbox(
            "Workout Type", ["None", "strength", "moderate intensity aerobic workouts", "HIIT"], 
            index=["None", "strength", "moderate intensity aerobic workouts", "HIIT"].index(existing_log.get("workout_type") or "None") if existing_log and existing_log.get("workout_type") in ["None", "strength", "moderate intensity aerobic workouts", "HIIT"] else 0,
            key="rap_type"
        )
        rap_snacks = st.slider("Exercise snacks count", min_value=0, max_value=20, value=int(existing_log.get("exercise_snacks_count") or 0) if existing_log else 0, step=1, key="rap_snacks")
        
        if st.button("Save Physical Log", use_container_width=True):
            payload = {
                "date": log_date_rap.isoformat(),
                "steps": rap_steps,
                "workout_minutes": rap_workout,
                "workout_type": rap_type if rap_type != "None" else None,
                "exercise_snacks_count": rap_snacks,
                "mood_score": existing_log.get("mood_score") if existing_log else None,
                "sleep_quality": existing_log.get("sleep_quality") if existing_log else None,
                "diary_text": existing_log.get("diary_text") if existing_log else None,
                "sleep_start": existing_log.get("sleep_start") if existing_log else None,
                "sleep_end": existing_log.get("sleep_end") if existing_log else None,
                "work_hours": existing_log.get("work_hours") if existing_log else None,
                "supplements": [
                    {"name": s["name"], "dosage": float(s["dosage"]), "unit": s["unit"]}
                    for s in existing_log.get("supplements", [])
                ] if existing_log else []
            }
            
            try:
                api_client.upsert_daily_log(payload)
                st.success(f"Physical log for {log_date_rap} saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit physical log: {e}")

with view_tab2:
    st.subheader("🏋️ Strength Workout Session Logging")
    
    # Left column: log workout manually or upload CSV
    # Right column: view history of workouts
    col_str1, col_str2 = st.columns([1, 1])
    
    with col_str1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### 📥 Import Workouts from Strong CSV")
        uploaded_file = st.file_uploader("Select exported Strong CSV file", type=["csv"], key="strong_csv_uploader")
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            if st.button("🚀 Process and Import Workouts", use_container_width=True, type="primary"):
                try:
                    res = api_client.import_strength_workouts_csv(file_bytes, uploaded_file.name)
                    st.success(f"Imported successfully! {res.get('imported_count', 0)} new workouts added.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to import: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### ➕ Log a Strength Workout Manually")
        
        w_date = st.date_input("Workout Date", date.today(), key="w_date_input")
        w_time = st.time_input("Workout Start Time", datetime.now().time(), step=300, key="w_time_input")
        w_name = st.text_input("Workout Name", "Leg Day", placeholder="e.g. Upper Body, Chest & Back", key="w_name_input")
        w_duration_min = st.slider("Duration (minutes)", 0, 180, 60, step=5, key="w_duration_input")
        w_notes = st.text_area("Workout Notes (optional)", "", key="w_notes_input")
        
        st.write("---")
        st.write("**Sets in this Workout:**")
        
        # Builder Sets list in session state
        if "builder_sets" not in st.session_state:
            st.session_state.builder_sets = []
            
        if st.session_state.builder_sets:
            df_sets_show = pd.DataFrame(st.session_state.builder_sets)
            st.dataframe(df_sets_show, use_container_width=True)
            if st.button("Clear sets", key="clear_builder_sets"):
                st.session_state.builder_sets = []
                st.rerun()
        else:
            st.info("No sets added yet. Use the inputs below to add exercises and sets.")
            
        st.write("---")
        st.write("**Add a Set:**")
        add_ex_name = st.text_input("Exercise Name", placeholder="e.g. Bench Press (Barbell)", key="add_ex_name")
        col_set1, col_set2, col_set3 = st.columns(3)
        with col_set1:
            add_weight = st.number_input("Weight (kg)", min_value=0.0, value=20.0, step=2.5, key="add_weight")
        with col_set2:
            add_reps = st.number_input("Reps", min_value=0, value=10, step=1, key="add_reps")
        with col_set3:
            add_rpe = st.slider("RPE (1-10)", 1.0, 10.0, 8.0, step=0.5, key="add_rpe")
            
        if st.button("➕ Add Set to Workout", use_container_width=True):
            if not add_ex_name.strip():
                st.warning("Please enter an exercise name.")
            else:
                # Determine set order
                order = 1
                for s in st.session_state.builder_sets:
                    if s["exercise_name"] == add_ex_name.strip():
                        order = max(order, s["set_order"] + 1)
                        
                st.session_state.builder_sets.append({
                    "exercise_name": add_ex_name.strip(),
                    "set_order": order,
                    "weight_kg": float(add_weight),
                    "reps": int(add_reps),
                    "rpe": float(add_rpe)
                })
                st.toast(f"Added set {order} for {add_ex_name.strip()}")
                st.rerun()
                
        if st.session_state.builder_sets:
            st.write("---")
            if st.button("💾 Submit and Save Strength Workout", use_container_width=True, type="primary"):
                # Construct datetime
                start_dt = datetime.combine(w_date, w_time)
                payload = {
                    "date": start_dt.isoformat(),
                    "name": w_name.strip(),
                    "duration_seconds": w_duration_min * 60,
                    "notes": w_notes.strip() if w_notes.strip() else None,
                    "sets": st.session_state.builder_sets
                }
                try:
                    api_client.create_strength_workout(payload)
                    st.success("Strength workout logged successfully!")
                    st.session_state.builder_sets = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save workout: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_str2:
        st.markdown("### 📖 Strength Workouts Log History")
        
        # Load workouts
        workouts = []
        try:
            workouts = api_client.get_strength_workouts(start_date=start_date, end_date=end_date)
        except Exception:
            st.warning("Could not fetch strength workouts. Check backend connection.")
            
        if not workouts:
            st.info("No strength workouts logged in this date range.")
        else:
            st.write(f"Showing {len(workouts)} workout sessions:")
            
            for wk in workouts:
                # Parse datetime
                dt_val = datetime.fromisoformat(wk["date"].replace("Z", "+00:00"))
                formatted_dt = dt_val.strftime("%b %d, %Y at %H:%M")
                dur_min = int(wk["duration_seconds"] / 60)
                
                expander_label = f"🏋️ {wk['name']} - {formatted_dt} ({dur_min} mins)"
                if wk.get("workout_num"):
                    expander_label = f"#{wk['workout_num']} " + expander_label
                    
                with st.expander(expander_label):
                    if wk.get("notes"):
                        st.markdown(f"**Notes:** *{wk['notes']}*")
                        
                    # Group sets by exercise
                    df_sets = pd.DataFrame(wk["sets"])
                    if df_sets.empty:
                        st.write("No sets logged for this workout.")
                    else:
                        for exercise, group in df_sets.groupby("exercise_name"):
                            st.write(f"**{exercise}**")
                            # Display sets as clean strings
                            sets_strs = []
                            for _, row in group.sort_values("set_order").iterrows():
                                rpe_str = f" @ RPE {row['rpe']}" if pd.notna(row.get('rpe')) else ""
                                sets_strs.append(f"Set {row['set_order']}: **{row['weight_kg']:.1f} kg** x **{int(row['reps'])}** reps{rpe_str}")
                            st.write("  \n".join(sets_strs))
                            
                    st.write("")
                    if st.button("🗑️ Delete Workout", key=f"del_wk_{wk['id']}", type="secondary"):
                        try:
                            api_client.delete_strength_workout(wk["id"])
                            st.warning("Workout deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete workout: {e}")
