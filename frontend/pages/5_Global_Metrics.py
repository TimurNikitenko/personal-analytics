import streamlit as st
import pandas as pd
from datetime import date, timedelta
import math
import plotly.graph_objects as go
from frontend.utils.api_client import api_client
from frontend.utils.charts import COLORS, create_timeline_chart, apply_sleek_theme

st.set_page_config(page_title="Global Metrics", page_icon="🧬", layout="wide")

# Custom header
st.markdown("<h1 style='background: linear-gradient(135deg, #00CEC9, #81ECEC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;'>🧬 Global Life Metrics</h1>", unsafe_allow_html=True)
st.write("Track long-term biometrics and psychological test results (VO2Max, HRV, Weight, IQ, MBTI, Big Five).")

# Fetch all global metrics at page load
all_metrics = []
try:
    all_metrics = api_client.get_metrics()
except Exception:
    pass

# Build lookup maps
lookup_metrics = {}
for m in all_metrics:
    m_date = str(m["date"])
    m_name = str(m["metric_name"])
    lookup_metrics[(m_date, m_name)] = m

tab1, tab2, tab3 = st.tabs(["📊 Metric History & Plotter", "📝 Log Global Metric", "🧬 Population Distributions"])

# ==================== TAB 1: HISTORY & PLOTTER ====================
with tab1:
    # Fetch all unique metric names
    try:
        metric_names = api_client.get_metric_names()
    except Exception:
        metric_names = []

    if not metric_names:
        st.info("No global metrics recorded yet. Log your first metric to build charts!")
    else:
        selected_metric = st.selectbox("Select metric to plot", metric_names)
        
        # Date filter
        st.write("### 📅 Filter History")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("Start Date", date.today() - timedelta(days=365))
        with col_d2:
            end_date = st.date_input("End Date", date.today())
            
        # Filter metrics from cached loaded state
        filtered_metrics = [
            m for m in all_metrics 
            if m["metric_name"] == selected_metric 
            and start_date <= date.fromisoformat(str(m["date"])) <= end_date
        ]
            
        if not filtered_metrics:
            st.warning(f"No entries found for metric '{selected_metric}' in this date range.")
        else:
            df_m = pd.DataFrame(filtered_metrics)
            df_m['date'] = pd.to_datetime(df_m['date'])
            
            # Try to convert values to float for charting
            is_numeric = True
            try:
                df_m['numeric_value'] = df_m['metric_value'].astype(float)
            except ValueError:
                is_numeric = False
                
            if is_numeric:
                st.subheader(f"Timeline: {selected_metric}")
                fig_metric = create_timeline_chart(
                    df_m, "date", "numeric_value", f"{selected_metric} over time", selected_metric, COLORS["accent"]
                )
                st.plotly_chart(fig_metric, use_container_width=True)
            else:
                st.info(f"Metric '{selected_metric}' has non-numeric values (e.g. text/psychological scores). Listing records below:")
            
            # Show historical logs
            st.write("### Historical Log")
            st.dataframe(df_m[["date", "metric_value", "notes"]].sort_values(by="date", ascending=False), use_container_width=True)

# ==================== TAB 2: LOG GLOBAL METRIC ====================
with tab2:
    st.subheader("Log Bio/Psych Metric")
    
    met_date = st.date_input("Date of measurement", date.today(), key="metric_date")
    
    # Common metric names suggestions
    suggested_names = [
        "Weight (kg)", 
        "Heart Rate Variability (HRV)", 
        "VO2Max", 
        "Leg Press 1RM (kg)", 
        "Dumbell press 1RM (kg)", 
        "IQ Score", 
        "MBTI Personality", 
        "Big Five: Openness", 
        "Big Five: Conscientiousness", 
        "Big Five: Extraversion", 
        "Big Five: Agreeableness", 
        "Big Five: Neuroticism"
    ]
    met_name = st.selectbox("Metric Name", suggested_names, key="metric_name_select")
    custom_name = st.text_input("Or input a custom metric name (overrides select box)", "", key="metric_name_custom")
    
    final_name = custom_name.strip() if custom_name.strip() else met_name
    
    # Dynamic pre-population lookup
    date_str = met_date.isoformat()
    existing_met = lookup_metrics.get((date_str, final_name))
    
    if existing_met:
        st.info(f"ℹ️ An entry for **{final_name}** on **{date_str}** already exists (Value: `{existing_met['metric_value']}`). Saving will update it.")
        def_val = existing_met["metric_value"]
        def_notes = existing_met["notes"] or ""
    else:
        def_val = ""
        def_notes = ""
        
    widget_key = f"{final_name}_{date_str}"
    
    met_val = st.text_input("Metric Value", value=def_val, placeholder="e.g. 74.5, 68, INTJ, 85%...", key=f"val_{widget_key}")
    met_notes = st.text_area("Notes / Context", value=def_notes, placeholder="Measured in the morning, after fasting...", key=f"notes_{widget_key}")

    if st.button("Save Global Metric", use_container_width=True, key=f"save_{widget_key}"):
        if not met_val.strip():
            st.error("Please enter a metric value.")
        else:
            payload = {
                "date": date_str,
                "metric_name": final_name,
                "metric_value": met_val.strip(),
                "notes": met_notes.strip() or None
            }
            try:
                api_client.create_metric(payload)
                st.success(f"🎉 Metric '{final_name}' successfully saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save metric: {e}")

# ==================== TAB 3: POPULATION DISTRIBUTIONS ====================
with tab3:
    st.subheader("🧬 Population Distribution & Percentiles")
    st.write("Compare your biometrics and test scores against standard scientific population distributions.")
    
    # Normal distribution helper functions
    def get_normal_pdf(x, mean, sd):
        return (1 / (sd * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mean) / sd) ** 2)

    def get_normal_cdf(x, mean, sd):
        return 0.5 * (1 + math.erf((x - mean) / (sd * math.sqrt(2))))

    def generate_bell_curve(mean, sd, min_val, max_val, steps=150):
        xs = []
        ys = []
        step_size = (max_val - min_val) / steps
        for i in range(steps + 1):
            x = min_val + i * step_size
            xs.append(x)
            ys.append(get_normal_pdf(x, mean, sd))
        return xs, ys

    def get_latest_val(metric_name):
        matching = [m for m in all_metrics if m["metric_name"] == metric_name]
        if not matching:
            return None
        sorted_match = sorted(matching, key=lambda x: x["date"], reverse=True)
        val_str = sorted_match[0]["metric_value"]
        clean_val = val_str.replace("%", "").strip()
        try:
            return float(clean_val)
        except ValueError:
            return None

    # Choose metric category
    compare_metric = st.selectbox(
        "Select Metric to Analyze",
        ["VO2Max", "IQ Score", "Big Five Traits"]
    )
    
    # Setup distribution parameters based on choice
    if compare_metric == "VO2Max":
        gender = st.radio("Select Gender Norms", ["Male", "Female"], horizontal=True)
        if gender == "Male":
            mean, sd = 42.0, 8.0
            st.caption("General population male norm: Mean = 42.0 ml/kg/min, SD = 8.0")
        else:
            mean, sd = 36.0, 6.0
            st.caption("General population female norm: Mean = 36.0 ml/kg/min, SD = 6.0")
            
        min_p_val, max_p_val = 10.0, 75.0
        unit_label = "ml/kg/min"
        
        # Look up latest score
        latest_val = get_latest_val("VO2Max")
        default_input_val = latest_val if latest_val is not None else mean
        
        # User input slider (pre-populated)
        user_score = st.slider("Your VO2Max", min_value=10.0, max_value=80.0, value=float(default_input_val), step=0.5)
        
    elif compare_metric == "IQ Score":
        mean, sd = 100.0, 15.0
        min_p_val, max_p_val = 40.0, 160.0
        unit_label = "points"
        st.caption("Standardized IQ scale norm: Mean = 100, SD = 15")
        
        latest_val = get_latest_val("IQ Score")
        default_input_val = latest_val if latest_val is not None else mean
        
        user_score = st.slider("Your IQ Score", min_value=40, max_value=180, value=int(default_input_val), step=1)
        
    else: # Big Five
        trait = st.selectbox(
            "Select Big Five Personality Trait",
            ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
        )
        mean, sd = 50.0, 15.0
        min_p_val, max_p_val = 0.0, 100.0
        unit_label = "%"
        st.caption(f"Big Five {trait} percentile norm: Mean = 50, SD = 15")
        
        latest_val = get_latest_val(f"Big Five: {trait}")
        default_input_val = latest_val if latest_val is not None else mean
        
        user_score = st.slider(f"Your {trait} Score", min_value=0.0, max_value=100.0, value=float(default_input_val), step=1.0)
        
    # Generate bell curve
    xs, ys = generate_bell_curve(mean, sd, min_p_val, max_p_val)
    user_y = get_normal_pdf(user_score, mean, sd)
    percentile = get_normal_cdf(user_score, mean, sd) * 100
    
    # Text summary card
    st.markdown(f"""
    <div style="background: rgba(30, 30, 36, 0.65); border: 1px solid rgba(0, 206, 201, 0.2); border-radius: 16px; padding: 20px; margin-bottom: 25px;">
        <span style="color: #A4A4AB; font-size: 13px; text-transform: uppercase;">Percentile Ranking</span>
        <h2 style="margin: 0; color: #00CEC9; font-weight: 800;">{percentile:.1f}th Percentile</h2>
        <p style="margin: 5px 0 0 0; color: #E1E1E6; font-size: 15px;">
            Your score of <b>{user_score:.1f} {unit_label}</b> is higher than <b>{percentile:.1f}%</b> of the general population.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Plotly rendering
    fig = go.Figure()
    
    # PDF curve
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode='lines',
        line=dict(color='#00CEC9', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 206, 201, 0.12)',
        name='General Population',
        hoverinfo='skip'
    ))
    
    # Marker
    fig.add_trace(go.Scatter(
        x=[user_score],
        y=[user_y],
        mode='markers+text',
        marker=dict(color='#FF7675', size=14, line=dict(color='#FFFFFF', width=2)),
        text=[f"You ({user_score:.1f})"],
        textposition="top center",
        name='Your Position',
        hovertemplate="<b>Your Score</b>: %{x:.2f}<br>Percentile: " + f"{percentile:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        xaxis=dict(title=f"Score ({unit_label})", showgrid=True, gridcolor="#2D2D30", tickfont=dict(color="#A4A4AB"), titlefont=dict(color="#A4A4AB")),
        yaxis=dict(showgrid=False, showticklabels=False),
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
        showlegend=False
    )
    apply_sleek_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
