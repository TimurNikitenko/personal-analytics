import streamlit as st
import pandas as pd
from datetime import date
import httpx
from frontend.utils.api_client import api_client, BACKEND_URL

st.set_page_config(page_title="Goals & Settings", page_icon="🎯", layout="wide")

# Custom header
st.markdown("<h1 style='background: linear-gradient(135deg, #6C5CE7, #A29BFE); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;'>🎯 Goals & Advanced Settings</h1>", unsafe_allow_html=True)
st.write("Set flexible personal targets and manage your system backups and data exports.")

tab1, tab2, tab3 = st.tabs(["🏆 Personal Goals Tracker", "🎯 Create New Goal", "💾 System Backups & Export"])

# ==================== TAB 1: GOALS TRACKER ====================
with tab1:
    st.subheader("Current and Historical Goals")
    
    # Fetch goals
    try:
        goals = api_client.get_goals()
    except Exception:
        goals = []
        st.error("Could not fetch goals from the backend.")

    if not goals:
        st.info("No goals set yet! Go to the 'Create New Goal' tab to define your targets.")
    else:
        df_goals = pd.DataFrame(goals)
        
        # Split into Active vs Completed/Failed
        active_goals = df_goals[df_goals["status"] == "Active"]
        past_goals = df_goals[df_goals["status"] != "Active"]

        st.write("### 🚀 Active Goals")
        if active_goals.empty:
            st.info("No active goals right now.")
        else:
            for idx, row in active_goals.iterrows():
                with st.container():
                    st.markdown(f"#### {row['description']}")
                    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
                    with col1:
                        st.markdown(f"**Area**: `{row['area']}`")
                    with col2:
                        st.markdown(f"**Target**: `{row['target_value']}` (`{row['target_metric'] or 'N/A'}`)")
                    with col3:
                        st.markdown(f"📅 `{row['start_date']}` to `{row['end_date']}`")
                    with col4:
                        # Quick status changes
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("✅ Done", key=f"done_{row['id']}"):
                                payload = dict(row)
                                payload["status"] = "Completed"
                                del payload["id"]
                                api_client.update_goal(int(row['id']), payload)
                                st.success("Goal completed!")
                                st.rerun()
                        with col_b2:
                            if st.button("❌ Fail", key=f"fail_{row['id']}"):
                                payload = dict(row)
                                payload["status"] = "Failed"
                                del payload["id"]
                                api_client.update_goal(int(row['id']), payload)
                                st.warning("Goal marked as failed.")
                                st.rerun()
                    # Show flex data if present
                    if row.get("flex_data"):
                        st.caption(f"Additional details: {row['flex_data']}")
                    st.write("---")

        st.write("### 📜 Past Goals")
        if not past_goals.empty:
            for idx, row in past_goals.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
                with col1:
                    st.write(f"~~{row['description']}~~")
                with col2:
                    st.write(f"`{row['area']}`")
                with col3:
                    st.write(f"Ended: {row['end_date']}")
                with col4:
                    if row["status"] == "Completed":
                        st.success("Completed ✅")
                    else:
                        st.error("Failed ❌")
                    if st.button("🗑️ Delete", key=f"del_goal_{row['id']}"):
                        api_client.delete_goal(int(row['id']))
                        st.success("Deleted goal!")
                        st.rerun()

# ==================== TAB 2: CREATE NEW GOAL ====================
with tab2:
    st.subheader("Define a Flexible Goal")
    
    g_area = st.selectbox("Area of Life", ["Physical", "Finances", "Learning", "Health", "Mood", "Work", "Other"])
    g_desc = st.text_input("Goal Description", placeholder="e.g. Run 100km total, Save $2000, Study Python 20 hours...")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        g_metric = st.text_input("Target Metric (Optional)", placeholder="e.g. Steps, Savings, Hours")
    with col_t2:
        g_val = st.number_input("Target Value (Optional)", min_value=0.0, value=0.0, step=1.0)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        g_start = st.date_input("Start Date", date.today())
    with col_d2:
        g_end = st.date_input("End Date", date.today() + pd.Timedelta(days=30))

    # Flexible JSON criteria
    st.markdown("#### Flexible Criteria (Optional JSON Key-Values)")
    st.caption("You can add arbitrary attributes to this goal (e.g. frequency, partner, rewards).")
    
    flex_key = st.text_input("Attribute Name (Key)", placeholder="e.g. reward, difficulty, priority")
    flex_val = st.text_input("Attribute Value", placeholder="e.g. Buy new shoes, Hard, High")
    
    if st.button("Add Attribute"):
        if flex_key.strip():
            if "flex_store" not in st.session_state:
                st.session_state.flex_store = {}
            st.session_state.flex_store[flex_key.strip()] = flex_val.strip()
            st.toast(f"Added attribute: {flex_key}={flex_val}")
            
    if "flex_store" in st.session_state and st.session_state.flex_store:
        st.write("Stored attributes:")
        st.write(st.session_state.flex_store)
        if st.button("Clean Attributes"):
            st.session_state.flex_store = {}
            st.rerun()

    if st.button("Create Goal", use_container_width=True):
        if not g_desc.strip():
            st.error("Please provide a goal description.")
        else:
            flex_payload = st.session_state.get("flex_store", None)
            payload = {
                "area": g_area,
                "description": g_desc.strip(),
                "target_metric": g_metric.strip() if g_metric.strip() else None,
                "target_value": g_val if g_val > 0 else None,
                "start_date": g_start.isoformat(),
                "end_date": g_end.isoformat(),
                "status": "Active",
                "flex_data": flex_payload
            }
            try:
                api_client.create_goal(payload)
                st.success("🎉 Goal created successfully!")
                if "flex_store" in st.session_state:
                    st.session_state.flex_store = {}
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create goal: {e}")

# ==================== TAB 3: BACKUPS & EXPORT ====================
with tab3:
    st.subheader("Data Portability & Database Backups")
    st.write("Protect your data by exporting it regularly or creating safe PostgreSQL database backups.")

    st.write("---")
    st.markdown("### 📥 Export All Data")
    st.write("Download all tables (Daily Logs, Habits, Finances, Goals, Daily Nutrition, and Medical Tests) as a single ZIP file containing CSVs.")
    
    # Download Button using direct HTTP GET
    try:
        export_url = api_client.get_export_url()
        # Fetch zip content from backend
        response = httpx.get(export_url, timeout=30.0)
        response.raise_for_status()
        
        st.download_button(
            label="💾 Download ZIP of CSVs",
            data=response.content,
            file_name="personal_analytics_export.zip",
            mime="application/zip",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Could not prepare data export: {e}")

    st.write("---")
    st.markdown("### 📊 Machine Learning Pipeline")
    st.write("Download a flattened, date-indexed daily dataset merging all logged metrics, habits, pivoted supplements, expenses, and biometrics. Perfect for model training.")
    
    try:
        ml_data = api_client.get_ml_dataset()
        if ml_data:
            df_ml = pd.DataFrame(ml_data)
            csv_ml = df_ml.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download ML Flat CSV Dataset",
                data=csv_ml,
                file_name="personal_analytics_ml_dataset.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No daily logs or biometrics available yet to generate an ML dataset.")
    except Exception as e:
        st.error(f"Could not prepare ML dataset: {e}")

    st.write("---")
    st.markdown("### 🔌 Automated Database Backups")
    st.write(
        "A backup script is available at `scripts/backup.sh` which executes a `pg_dump` on the PostgreSQL container. You can trigger it manually below or set up a system cron job to run it regularly."
    )
    
    if st.button("🚀 Trigger Database Backup Now", use_container_width=True):
        try:
            # Send post request to backend /api/backup endpoint
            response = httpx.post(f"{BACKEND_URL}/api/backup", timeout=30.0)
            response.raise_for_status()
            res_json = response.json()
            st.success(f"🎉 Backup created successfully! File saved: `{res_json.get('backup_file')}`")
        except Exception as e:
            st.error(f"Could not trigger backup. Ensure that postgresql-client is installed in the backend container: {e}")

    st.write("---")
    st.markdown("### 🤖 Telegram Reminder Bot Settings")
    st.write("Verify that your Telegram integration is functioning. Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured in your Docker environment.")
    
    if st.button("🔔 Send Test Telegram Reminder", use_container_width=True):
        try:
            res = api_client.send_telegram_test_reminder()
            st.success(f"🎉 {res.get('detail', 'Test message sent!')}")
        except Exception as e:
            st.error(f"Failed to send test reminder: {e}")

