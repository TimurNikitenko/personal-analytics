import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go
from frontend.utils.api_client import api_client
from frontend.utils.charts import COLORS, apply_sleek_theme

# Page Config
st.set_page_config(
    page_title="Medical Tests Tracker",
    page_icon="🩺",
    layout="wide"
)

# Custom premium CSS styling
st.markdown("""
<style>
    .glow-header {
        font-size: 40px;
        font-weight: 900;
        background: linear-gradient(135deg, #FF7675 0%, #E84393 50%, #6C5CE7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .metric-card {
        background: rgba(30, 30, 36, 0.65);
        border: 1px solid rgba(232, 67, 147, 0.15);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(4px);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #E84393;
        margin-bottom: 2px;
    }
    .metric-label {
        font-size: 13px;
        color: #A4A4AB;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='glow-header'>🩺 Medical Tests & Biometrics</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #A4A4AB; font-size: 16px; margin-top: -15px;'>Log and track laboratory blood panels, lipid profiles, and cardiovascular metrics over time.</p>", unsafe_allow_html=True)
st.write("---")

# Predefined metrics and units
COMMON_METRICS = [
    # Lipids
    "LDL-C", "TC (Total Cholesterol)", "HDL-C", "TG (Triglycerides)", "apoB", "lp(a)", "apoA1",
    # Glycemic
    "HbA1c", "Fasting Glucose", "Fasting Insulin", "HOMA-IR",
    # Cardiovascular
    "Systolic Blood Pressure", "Diastolic Blood Pressure", "Resting Heart Rate",
    # Inflammation
    "CRP", "hs-CRP", "Homocysteine",
    # Hormones
    "Total Testosterone", "Free Testosterone",
    # Vitamins/Minerals
    "Vitamin D (25-OH)", "Vitamin B12", "Ferritin", "Iron", "Magnesium", "Zinc",
    # Kidney/Liver
    "Creatinine", "eGFR", "ALT", "AST", "GGT",
    # Custom option
    "Other (Custom)"
]

COMMON_UNITS = [
    "mg/dL", "mmol/L", "g/L", "nmol/L", "pmol/L", "pg/mL", "ng/mL", "mmHg", "%", "mg/L", "µmol/L", "µIU/mL", "U/L", "Other (Custom)"
]

# Fetch medical tests
tests = []
try:
    tests = api_client.get_medical_tests()
except Exception:
    st.warning("Could not connect to the backend database to fetch medical logs.")

df_tests = pd.DataFrame(tests)

# Build lookup maps
lookup_existing = {}
lookup_last_used = {}

if not df_tests.empty:
    # Sort by date ascending so that the last processed is the most recent
    for _, row in df_tests.sort_values(by="date", ascending=True).iterrows():
        t_date = str(row['date'])
        t_name = str(row['test_name'])
        lookup_existing[(t_date, t_name)] = row
        lookup_last_used[t_name] = row

# Layout Columns
col_form, col_chart = st.columns([1, 2])

with col_form:
    st.subheader("📝 Log Test Result")
    
    test_date = st.date_input("Date of Test", date.today(), key="test_date")
    
    selected_metric = st.selectbox("Metric Name", COMMON_METRICS, key="selected_metric")
    custom_metric = ""
    if selected_metric == "Other (Custom)":
        custom_metric = st.text_input("Enter Custom Metric Name", placeholder="e.g. apoB/apoA1 ratio", key="custom_metric_input")
        
    final_metric_name = custom_metric.strip() if selected_metric == "Other (Custom)" else selected_metric
    
    # Calculate defaults
    date_str = test_date.isoformat()
    existing_entry = lookup_existing.get((date_str, final_metric_name))
    last_used_entry = lookup_last_used.get(final_metric_name)
    
    if existing_entry is not None:
        st.info(f"ℹ️ An entry for **{final_metric_name}** on **{date_str}** already exists. Saving will update it.")
        def_val = float(existing_entry["value"])
        def_unit = existing_entry["unit"]
        def_ref = existing_entry["reference_range"] if (pd.notna(existing_entry["reference_range"]) and existing_entry["reference_range"]) else ""
    else:
        def_val = 0.0
        def_unit = last_used_entry["unit"] if last_used_entry is not None else "mg/dL"
        def_ref = last_used_entry["reference_range"] if (last_used_entry is not None and pd.notna(last_used_entry["reference_range"]) and last_used_entry["reference_range"]) else ""
        
    # Dynamic keys to force widget recreation when date or metric changes
    widget_suffix = f"{final_metric_name}_{date_str}"
    
    test_value = st.number_input(
        "Value", 
        min_value=0.0, 
        value=def_val, 
        step=0.01, 
        format="%.2f",
        key=f"val_{widget_suffix}"
    )
    
    # Setup Unit Index
    if def_unit in COMMON_UNITS:
        unit_index = COMMON_UNITS.index(def_unit)
    else:
        unit_index = COMMON_UNITS.index("Other (Custom)")
        
    selected_unit = st.selectbox(
        "Unit of Measurement", 
        COMMON_UNITS, 
        index=unit_index,
        key=f"unit_sel_{widget_suffix}"
    )
    
    custom_unit = ""
    if selected_unit == "Other (Custom)":
        custom_unit = st.text_input(
            "Enter Custom Unit", 
            value=def_unit if def_unit not in COMMON_UNITS else "", 
            placeholder="e.g. units/L",
            key=f"unit_cust_{widget_suffix}"
        )
        
    final_unit = custom_unit.strip() if selected_unit == "Other (Custom)" else selected_unit
    
    ref_range = st.text_input(
        "Reference Range (Optional)", 
        value=def_ref, 
        placeholder="e.g. < 100 mg/dL",
        key=f"ref_{widget_suffix}"
    )
    
    if st.button("💾 Save Test Result", use_container_width=True):
        if not final_metric_name:
            st.error("Please provide a valid metric name.")
        elif not final_unit:
            st.error("Please provide a valid unit.")
        else:
            payload = {
                "date": date_str,
                "test_name": final_metric_name,
                "value": test_value,
                "unit": final_unit,
                "reference_range": ref_range.strip() if ref_range.strip() else None
            }
            try:
                api_client.create_medical_test(payload)
                st.success(f"🎉 Saved {final_metric_name}: {test_value} {final_unit}!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save result: {e}")

# Chart & Trends section
with col_chart:
    st.subheader("📈 Biomarker Trends")
    
    if df_tests.empty:
        st.info("No medical tests logged yet. Log a test result on the left to see trends here!")
    else:
        # Get unique test names for plotting
        available_tests = sorted(df_tests['test_name'].unique())
        selected_trend_test = st.selectbox("Select Metric to Visualize", available_tests)
        
        # Filter data for chart
        df_chart = df_tests[df_tests['test_name'] == selected_trend_test].sort_values('date')
        
        if df_chart.empty:
            st.info("No historical data to chart.")
        else:
            # Get latest values for cards
            latest_row = df_chart.iloc[-1]
            unit_str = latest_row['unit']
            latest_val = latest_row['value']
            ref_str = latest_row['reference_range'] or "None defined"
            
            st.markdown(f"""
            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div class="metric-card" style="flex: 1;">
                    <div class="metric-value">{latest_val:.2f} {unit_str}</div>
                    <div class="metric-label">Latest Reading ({latest_row['date']})</div>
                </div>
                <div class="metric-card" style="flex: 1;">
                    <div class="metric-value" style="color: #6C5CE7;">{ref_str}</div>
                    <div class="metric-label">Reference Range</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Draw line plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_chart['date'],
                y=df_chart['value'],
                mode='lines+markers',
                line=dict(color='#E84393', width=3),
                marker=dict(size=8, color='#6C5CE7'),
                name=selected_trend_test,
                hovertemplate="<b>%{x}</b><br>Value: %{y:.2f} " + unit_str + "<extra></extra>"
            ))
            
            fig.update_layout(
                title=dict(text=f"Historical Timeline: {selected_trend_test}", font=dict(color="#E1E1E6")),
                xaxis=dict(title="Date", showgrid=True, gridcolor="#2D2D30", tickfont=dict(color="#A4A4AB"), titlefont=dict(color="#A4A4AB")),
                yaxis=dict(title=f"Value ({unit_str})", showgrid=True, gridcolor="#2D2D30", tickfont=dict(color="#A4A4AB"), titlefont=dict(color="#A4A4AB")),
                margin=dict(l=40, r=40, t=50, b=40),
                height=350
            )
            apply_sleek_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

# Table History view
st.write("---")
st.subheader("📋 Logged Medical Records")

if df_tests.empty:
    st.info("Log list is empty.")
else:
    # Filter controls for table
    col_f1, col_f2, _ = st.columns([1, 1, 2])
    with col_f1:
        f_name = st.selectbox("Filter by Test Name", ["All"] + sorted(df_tests['test_name'].unique().tolist()))
    with col_f2:
        f_unit = st.selectbox("Filter by Unit", ["All"] + sorted(df_tests['unit'].unique().tolist()))
        
    df_filtered = df_tests.copy()
    if f_name != "All":
        df_filtered = df_filtered[df_filtered['test_name'] == f_name]
    if f_unit != "All":
        df_filtered = df_filtered[df_filtered['unit'] == f_unit]
        
    # Render table nicely
    if df_filtered.empty:
        st.info("No matching records found.")
    else:
        for idx, row in df_filtered.iterrows():
            with st.container():
                cols = st.columns([2, 2, 2, 2, 2, 1])
                cols[0].write(f"📅 **{row['date']}**")
                cols[1].write(f"🔬 **{row['test_name']}**")
                cols[2].write(f"🔢 **{row['value']:.2f}**")
                cols[3].write(f"📏 **{row['unit']}**")
                cols[4].write(f"📋 Ref: *{row['reference_range'] or 'None'}*")
                
                # Delete button
                if cols[5].button("🗑️ Delete", key=f"del_test_{row['id']}"):
                    try:
                        api_client.delete_medical_test(row['id'])
                        st.success("Test record deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
            st.write("<hr style='margin: 8px 0; opacity: 0.15;' />", unsafe_allow_html=True)
