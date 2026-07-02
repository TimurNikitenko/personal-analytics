import os
import sys
import pandas as pd
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.utils.charts import create_timeline_chart, create_correlation_timeline_chart

def test_create_timeline_chart_autoscale():
    # Construct a dataset with data only on a few days, but dates extending far out
    data = {
        "date": ["2026-01-01", "2026-01-02", "2026-01-10", "2026-01-20"],
        "mood": [8.0, 7.5, None, None] # Data only present on Jan 1 and Jan 2
    }
    df = pd.DataFrame(data)
    
    # Create the chart
    fig = create_timeline_chart(df, "date", "mood", "Mood Over Time", "Mood Rating")
    
    # Check that x-axis range is set to cover Jan 1 to Jan 2 (with 1 day padding on each side)
    xaxis = fig.layout.xaxis
    assert xaxis.range is not None
    
    # Date values are represented as string formats or Timestamp formats
    start_range = pd.to_datetime(xaxis.range[0])
    end_range = pd.to_datetime(xaxis.range[1])
    
    assert start_range == pd.to_datetime("2026-01-01") - pd.Timedelta(days=1)
    assert end_range == pd.to_datetime("2026-01-02") + pd.Timedelta(days=1)

def test_create_correlation_timeline_chart_autoscale():
    data = {
        "date": ["2026-01-01", "2026-01-05", "2026-01-10", "2026-01-15"],
        "mood": [None, 8.0, None, None],
        "sleep": [None, None, 7.0, None] # Plotted data is on Jan 5 and Jan 10
    }
    df = pd.DataFrame(data)
    metrics_map = {"mood": "Mood", "sleep": "Sleep"}
    
    fig = create_correlation_timeline_chart(df, "date", metrics_map, "Multi-Metric Trend")
    
    xaxis = fig.layout.xaxis
    assert xaxis.range is not None
    
    start_range = pd.to_datetime(xaxis.range[0])
    end_range = pd.to_datetime(xaxis.range[1])
    
    assert start_range == pd.to_datetime("2026-01-05") - pd.Timedelta(days=1)
    assert end_range == pd.to_datetime("2026-01-10") + pd.Timedelta(days=1)
