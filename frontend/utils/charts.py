import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any, Optional

# Beautiful color palettes
COLORS = {
    "primary": "#6C5CE7",      # Sleek Purple
    "secondary": "#0984E3",    # Deep Blue
    "accent": "#00CEC9",       # Teal
    "warning": "#FDCB6E",      # Soft Yellow
    "danger": "#D63031",       # Coral Red
    "success": "#00B894",      # Emerald Green
    "background": "#1E1E24",   # Charcoal Dark
    "grid": "#2D2D35",
    "text": "#E1E1E6",
    "gradient_purple": ["#6C5CE7", "#A29BFE"],
    "gradient_teal": ["#00CEC9", "#81ECEC"],
    "gradient_blue": ["#0984E3", "#74B9FF"]
}

def apply_sleek_theme(fig: go.Figure, title: Optional[str] = None):
    """
    Applies a premium, modern dark theme to any Plotly figure.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Roboto, sans-serif", color=COLORS["text"]),
        title=dict(
            text=title if title else "",
            font=dict(size=18, color=COLORS["text"], weight="bold"),
            x=0.02,
            y=0.98
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            bgcolor="rgba(30, 30, 36, 0.6)",
            bordercolor=COLORS["grid"],
            borderwidth=1,
            font=dict(size=11, color=COLORS["text"])
        ),
        xaxis=dict(
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            tickfont=dict(color="#A4A4AB")
        ),
        yaxis=dict(
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            tickfont=dict(color="#A4A4AB")
        )
    )
    return fig

# 1. Timeline Chart (e.g., mood, steps, sleep over time)
def create_timeline_chart(
    df: pd.DataFrame, 
    x_col: str, 
    y_col: str, 
    title: str, 
    y_label: str,
    color_hex: str = COLORS["primary"],
    is_bar: bool = False
) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        apply_sleek_theme(fig, title)
        return fig

    # Sort by date
    df_sorted = df.sort_values(by=x_col)

    if is_bar:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=df_sorted[x_col],
                    y=df_sorted[y_col],
                    marker=dict(
                        color=color_hex,
                        line=dict(color=color_hex, width=1)
                    ),
                    name=y_label
                )
            ]
        )
    else:
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=df_sorted[x_col],
                    y=df_sorted[y_col],
                    mode="lines+markers",
                    line=dict(color=color_hex, width=3),
                    marker=dict(size=6, color=color_hex, symbol="circle"),
                    name=y_label
                )
            ]
        )

    apply_sleek_theme(fig, title)
    fig.update_yaxes(title_text=y_label)
    
    # Auto-scale x-axis to only cover dates where data actually exists
    if y_col in df_sorted.columns:
        df_non_null = df_sorted.dropna(subset=[y_col])
        if not df_non_null.empty:
            dates = pd.to_datetime(df_non_null[x_col])
            min_date = dates.min()
            max_date = dates.max()
            fig.update_xaxes(range=[min_date - pd.Timedelta(days=1), max_date + pd.Timedelta(days=1)])
            
    return fig

# 2. Multi-line Correlation / Trend Chart (e.g. Sleep vs. Mood vs. Work Hours)
def create_correlation_timeline_chart(
    df: pd.DataFrame,
    date_col: str,
    metrics_map: Dict[str, str], # {"mood_score": "Mood", "sleep_hours": "Sleep (Hours)"}
    title: str
) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        apply_sleek_theme(fig, title)
        return fig

    df_sorted = df.sort_values(by=date_col)
    
    color_list = [COLORS["primary"], COLORS["accent"], COLORS["warning"], COLORS["secondary"]]
    
    for i, (col, label) in enumerate(metrics_map.items()):
        if col in df_sorted.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_sorted[date_col],
                    y=df_sorted[col],
                    mode="lines+markers",
                    name=label,
                    line=dict(color=color_list[i % len(color_list)], width=2.5),
                    marker=dict(size=5)
                )
            )

    apply_sleek_theme(fig, title)
    
    # Auto-scale x-axis to only cover dates where at least one of the plotted metrics has data
    valid_cols = [col for col in metrics_map.keys() if col in df_sorted.columns]
    if valid_cols:
        df_non_null = df_sorted.dropna(subset=valid_cols, how='all')
        if not df_non_null.empty:
            dates = pd.to_datetime(df_non_null[date_col])
            min_date = dates.min()
            max_date = dates.max()
            fig.update_xaxes(range=[min_date - pd.Timedelta(days=1), max_date + pd.Timedelta(days=1)])
            
    return fig

# 3. Pie/Donut Chart for Finances
def create_pie_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    title: str
) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        apply_sleek_theme(fig, title)
        return fig

    # Group by category
    summary = df.groupby(category_col)[value_col].sum().reset_index()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=summary[category_col],
                values=summary[value_col],
                hole=0.4,
                marker=dict(
                    colors=[COLORS["primary"], COLORS["secondary"], COLORS["accent"], COLORS["warning"], COLORS["danger"], COLORS["success"]]
                ),
                textinfo="percent+label"
            )
        ]
    )

    apply_sleek_theme(fig, title)
    return fig

# 4. Correlation Scatter Plot
def create_scatter_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    title: str
) -> go.Figure:
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        fig = go.Figure()
        apply_sleek_theme(fig, title)
        return fig

    # Drop nulls for these columns
    df_clean = df.dropna(subset=[x_col, y_col])

    fig = px.scatter(
        df_clean,
        x=x_col,
        y=y_col,
        labels={x_col: x_label, y_col: y_label},
        trendline="ols",
        trendline_color_override=COLORS["danger"]
    )
    
    # Customise trace
    fig.update_traces(
        marker=dict(size=10, color=COLORS["accent"], opacity=0.7, line=dict(width=1, color="#fff"))
    )

    apply_sleek_theme(fig, title)
    return fig
