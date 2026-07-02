import streamlit as st
import pandas as pd
import numpy as np
import math
import random
import re
from collections import Counter
from datetime import date, timedelta
import plotly.graph_objects as go
import plotly.express as px

try:
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
except ImportError:
    morph = None
from frontend.utils.api_client import api_client
from frontend.utils.charts import (
    COLORS, 
    create_correlation_timeline_chart, 
    create_scatter_correlation,
    apply_sleek_theme
)

st.set_page_config(page_title="Global Overview", page_icon="🌐", layout="wide")

# Custom header
st.markdown("<h1 style='background: linear-gradient(135deg, #A29BFE, #6C5CE7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;'>🌐 Global Life Overview</h1>", unsafe_allow_html=True)
st.write("Cross-metric analysis, correlation heatmaps, selectable time trends, and text cloud analysis.")

# Filter Range
st.sidebar.markdown("### 📅 Date Filters")
start_date = st.sidebar.date_input("Start Date", date.today() - timedelta(days=90))
end_date = st.sidebar.date_input("End Date", date.today())

# Fetch Consolidated Dataset
try:
    ml_data = api_client.get_ml_dataset(start_date=start_date, end_date=end_date)
except Exception as e:
    st.error(f"Could not fetch data pipeline: {e}")
    ml_data = []

if not ml_data:
    st.info("No logs found for the selected date range. Try entering some daily questionnaires or biometrics first!")
else:
    df_ml = pd.DataFrame(ml_data)
    df_ml['date'] = pd.to_datetime(df_ml['date'])
    
    # 1. Timeline Overview of Lifestyle Habits
    st.subheader("Multi-Metric Lifestyle Timeline")
    # Scaling steps to k
    if 'steps' in df_ml.columns and not df_ml['steps'].isna().all():
        df_ml['steps_scaled'] = df_ml['steps'].astype(float) / 1000.0
        steps_col = 'steps_scaled'
        steps_label = 'Steps (k)'
    else:
        steps_col = 'mood_score' # fallback if empty
        steps_label = 'Mood (Placeholder)'

    lifestyle_dims = {}
    if 'mood_score' in df_ml.columns:
        lifestyle_dims['mood_score'] = 'Mood'
    if 'sleep_hours' in df_ml.columns:
        lifestyle_dims['sleep_hours'] = 'Sleep (hrs)'
    if 'work_hours' in df_ml.columns:
        lifestyle_dims['work_hours'] = 'Work (hrs)'
    if steps_col in df_ml.columns and steps_col != 'mood_score':
        lifestyle_dims[steps_col] = steps_label

    if lifestyle_dims:
        fig_lifestyle = create_correlation_timeline_chart(
            df_ml, 
            "date", 
            lifestyle_dims,
            "Core Lifestyle Factors Over Time"
        )
        st.plotly_chart(fig_lifestyle, use_container_width=True)
    
    st.write("---")

    # 2. Dynamic Time Trend Selector
    st.subheader("📈 Dynamic Time Trend Selector")
    st.write("Select any numerical column from the entire merged database to analyze its standalone timeline.")
    
    # Extract numerical columns
    exclude_cols = ['date', 'diary_text', 'steps_scaled']
    numeric_cols = []
    for col in df_ml.columns:
        if col not in exclude_cols:
            # Check if column is numeric or can be parsed as such
            try:
                pd.to_numeric(df_ml[col].dropna(), errors='raise')
                numeric_cols.append(col)
            except (ValueError, TypeError):
                pass
                
    if numeric_cols:
        selected_trend_col = st.selectbox("Select metric to plot timeline", sorted(numeric_cols))
        
        df_trend = df_ml[['date', selected_trend_col]].dropna()
        if df_trend.empty:
            st.warning("No data points available for this metric in the selected date range.")
        else:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=df_trend['date'],
                y=df_trend[selected_trend_col],
                mode='lines+markers',
                line=dict(color=COLORS['primary'], width=3),
                marker=dict(size=8, color=COLORS['accent']),
                name=selected_trend_col
            ))
            apply_sleek_theme(fig_trend, f"Timeline of {selected_trend_col}")
            fig_trend.update_layout(yaxis_title=selected_trend_col)
            st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No numeric fields available to plot.")

    st.write("---")

    col_visual1, col_visual2 = st.columns(2)

    # 3. Correlation Heatmap
    with col_visual1:
        st.subheader("🧠 Correlation Heatmap")
        st.write("Pearson correlation matrix showing how all numerical metrics relate to each other.")
        
        if len(numeric_cols) > 1:
            df_numeric = df_ml[numeric_cols].apply(pd.to_numeric, errors='coerce')
            corr_matrix = df_numeric.corr(method='pearson')
            
            # Draw beautiful heatmap
            fig_heatmap = px.imshow(
                corr_matrix,
                text_auto=".2f",
                color_continuous_scale="Viridis",
                labels=dict(color="Correlation"),
                x=corr_matrix.columns,
                y=corr_matrix.columns
            )
            apply_sleek_theme(fig_heatmap, "Pearson Correlation Heatmap")
            fig_heatmap.update_layout(
                height=500,
                coloraxis_colorbar=dict(title="Correlation")
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Not enough numerical columns to compute correlation matrix.")

    # 4. Word Cloud Map
    with col_visual2:
        st.subheader("🔤 Diary Word Map")
        st.write("Word frequency map extracted from your daily log diaries, filtering out common stopwords.")
        
        # Word Frequency Processor
        import os
        import json
        
        stopwords = set()
        custom_stopwords = {
            "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "at", "by", 
            "from", "for", "in", "out", "on", "off", "over", "under", "again", "further", 
            "once", "here", "there", "why", "how", "all", "any", "both", "each", "few", 
            "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", 
            "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", 
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
            "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
            "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
            "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
            "have", "has", "had", "having", "do", "does", "did", "doing", "would", "could",
            # Russian stopwords
            "в", "на", "с", "и", "не", "что", "он", "она", "я", "меня", "мне", "как", "так", 
            "это", "был", "было", "была", "все", "всего", "еще", "но", "по", "у", "к", "для", 
            "о", "же", "за", "бы", "то", "из", "или", "быть", "себя", "свои", "очень", "были",
            "мои", "мне", "его", "ее", "их", "только", "уже", "также", "после", "хотя", "день",
            "сегодня", "сделать"
        }
        
        try:
            current_dir = os.path.dirname(__file__)
            json_path = os.path.abspath(os.path.join(current_dir, "..", "utils", "stopwords.json"))
            with open(json_path, "r", encoding="utf-8") as f:
                nltk_stopwords = json.load(f)
                stopwords.update(nltk_stopwords.get("russian", []))
                stopwords.update(nltk_stopwords.get("english", []))
        except Exception:
            pass
            
        stopwords.update(custom_stopwords)
        
        words = []
        if 'diary_text' in df_ml.columns:
            for text in df_ml['diary_text'].dropna():
                if isinstance(text, str):
                    # Clean text: remove non-alphabetical chars (supporting Cyrillic)
                    cleaned = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', ' ', text).lower()
                    for word in cleaned.split():
                        if word not in stopwords and len(word) > 2:
                            # Lemmatize Russian words
                            if morph and re.search(r'[а-яё]', word):
                                parsed = morph.parse(word)
                                if parsed:
                                    word = parsed[0].normal_form
                            # Check again after lemmatization
                            if word not in stopwords and len(word) > 2:
                                words.append(word)
                            
        word_counts = Counter(words).most_common(40)
        
        if not word_counts:
            st.info("No word data available. Write some descriptions in your daily questionnaire diary notes!")
        else:
            # Create Plotly Word Cloud
            w_words = [w[0] for w in word_counts]
            w_counts = [w[1] for w in word_counts]
            
            max_c = max(w_counts) if w_counts else 1
            min_c = min(w_counts) if w_counts else 1
            
            # Spiraling Math
            xs = []
            ys = []
            font_sizes = []
            colors = []
            
            for i, (word, count) in enumerate(word_counts):
                # Fermat's spiral
                r = math.sqrt(i + 1) * 1.5
                theta = i * 2.4
                xs.append(r * math.cos(theta))
                ys.append(r * math.sin(theta))
                
                # Font size logic
                if max_c == min_c:
                    fs = 20
                else:
                    fs = 14 + 28 * (count - min_c) / (max_c - min_c)
                font_sizes.append(fs)
                
                # Pick colors
                colors.append(random.choice([
                    COLORS['primary'], COLORS['accent'], COLORS['success'], 
                    "#FF7675", "#0984E3", "#E17055", "#00CEC9", "#FD79A8"
                ]))
                
            fig_cloud = go.Figure()
            fig_cloud.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode="text",
                text=w_words,
                textfont=dict(size=font_sizes, color=colors, family="Inter, Outfit, sans-serif"),
                hoverinfo="text",
                hovertext=[f"Word: <b>{w}</b><br>Frequency: {c} times" for w, c in word_counts]
            ))
            
            fig_cloud.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=500
            )
            st.plotly_chart(fig_cloud, use_container_width=True)

