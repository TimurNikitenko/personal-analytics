import streamlit as st
import pandas as pd
from datetime import date, timedelta
from frontend.utils.api_client import api_client
from frontend.utils.charts import COLORS, create_timeline_chart, create_correlation_timeline_chart

st.set_page_config(page_title="Learning & Work", page_icon="💻", layout="wide")

# Custom header
st.markdown("<h1 style='background: linear-gradient(135deg, #A29BFE, #6C5CE7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;'>💻 Learning & Work Analytics</h1>", unsafe_allow_html=True)
st.write("Monitor work productivity hours and analyze your self-education, reading, and skill practice.")

# Date filter
st.sidebar.markdown("### 📅 Date Filters")
start_date = st.sidebar.date_input("Start Date", date.today() - timedelta(days=30))
end_date = st.sidebar.date_input("End Date", date.today())

tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "📝 Log Learning Session"])

# Load daily logs (for work hours) and learning logs
try:
    daily_logs = api_client.get_daily_logs(start_date=start_date, end_date=end_date)
except Exception:
    daily_logs = []
try:
    learning_logs = api_client.get_learning_logs(start_date=start_date, end_date=end_date)
except Exception:
    learning_logs = []

df_daily = pd.DataFrame(daily_logs)
df_learn = pd.DataFrame(learning_logs)

# ==================== TAB 1: ANALYTICS DASHBOARD ====================
with tab1:
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.subheader("Work Hours Trend")
        if df_daily.empty or "work_hours" not in df_daily.columns:
            st.info("No work hours recorded. Set them in your Daily Questionnaire!")
        else:
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            fig_work = create_timeline_chart(
                df_daily, "date", "work_hours", "Hours Worked per Day", "Hours", COLORS["primary"], is_bar=True
            )
            st.plotly_chart(fig_work, use_container_width=True)
            
            # Simple stats
            tot_work = df_daily["work_hours"].sum()
            avg_work = df_daily["work_hours"].mean()
            st.markdown(f"- **Total Hours Worked**: `{tot_work:.1f} hrs`  \n- **Average Hours/Day**: `{avg_work:.1f} hrs`")

    with col_w2:
        st.subheader("Education: Learning vs. Practice Hours")
        if df_learn.empty:
            st.info("No learning logs recorded in this period. Use the second tab to log some sessions!")
        else:
            df_learn['date'] = pd.to_datetime(df_learn['date'])
            
            # Group by topic and calculate sum
            topic_summary = df_learn.groupby("topic")[["learning_hours", "practice_hours"]].sum().reset_index()
            
            import plotly.graph_objects as go
            fig_learn = go.Figure()
            fig_learn.add_trace(go.Bar(x=topic_summary['topic'], y=topic_summary['learning_hours'], name='Theory (Learning)', marker_color=COLORS['accent']))
            fig_learn.add_trace(go.Bar(x=topic_summary['topic'], y=topic_summary['practice_hours'], name='Practice', marker_color=COLORS['success']))
            fig_learn.update_layout(barmode='stack')
            
            from frontend.utils.charts import apply_sleek_theme
            apply_sleek_theme(fig_learn, "Hours Logged by Skill/Topic")
            st.plotly_chart(fig_learn, use_container_width=True)

    if not df_learn.empty:
        st.write("---")
        st.subheader("Recent Learning Logs")
        for idx, row in df_learn.iterrows():
            l_col1, l_col2, l_col3, l_col4 = st.columns([1, 2, 2, 1])
            with l_col1:
                st.write(pd.to_datetime(row['date']).strftime('%Y-%m-%d'))
            with l_col2:
                st.write(f"📚 **{row['topic']}**")
            with l_col3:
                st.write(f"Theory: `{row['learning_hours']:.1f}h` | Practice: `{row['practice_hours']:.1f}h`  \n*{row['notes'] or ''}*")
            with l_col4:
                if st.button("🗑️ Delete", key=f"del_learn_{row['id']}"):
                    try:
                        api_client.delete_learning(int(row['id']))
                        st.success("Deleted log entry!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==================== TAB 2: LOG LEARNING SESSION ====================
with tab2:
    st.subheader("Log Study/Practice Session")
    
    l_date = st.date_input("Session Date", date.today(), key="learn_date")
    
    # Common suggestions
    common_topics = ["Programming & Dev", "Mathematics", "Machine Learning & AI", "Music / Guitar", "Health & Nutrition", "Foreign Languages", "Writing", "Others"]
    l_topic = st.selectbox("Topic/Skill", common_topics, key="learn_topic")
    custom_topic = st.text_input("Or input a custom Topic (overrides select box)", "", key="learn_custom_topic")
    
    l_learn_hours = st.number_input("Theory/Learning Hours", min_value=0.0, max_value=24.0, value=1.0, step=0.5, key="learn_hrs")
    l_prac_hours = st.number_input("Practice Hours", min_value=0.0, max_value=24.0, value=0.5, step=0.5, key="prac_hrs")
    l_notes = st.text_area("Session Notes / What did you achieve?", "", placeholder="e.g. read chapters 2-3, completed programming exercise...", key="learn_notes")

    if st.button("Save Learning Session", use_container_width=True):
        final_topic = custom_topic.strip() if custom_topic.strip() else l_topic
        payload = {
            "date": l_date.isoformat(),
            "topic": final_topic,
            "learning_hours": float(l_learn_hours),
            "practice_hours": float(l_prac_hours),
            "notes": l_notes.strip() or None
        }
        try:
            api_client.create_learning(payload)
            st.success(f"🎉 Learning session for '{final_topic}' saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save learning session: {e}")
