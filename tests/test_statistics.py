import os
import sys
import numpy as np
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.utils.statistics import (
    calculate_required_sample_size,
    estimate_baseline_stats,
    run_normality_test,
    run_homogeneity_test,
    calculate_cohens_d,
    run_bootstrap,
    analyze_experiment_data
)

def test_calculate_required_sample_size():
    # Theoretical value for std=1.0, mde=0.5, alpha=0.05, power=0.80 is 63 per group
    n = calculate_required_sample_size(std=1.0, mde=0.5, alpha=0.05, power=0.80)
    assert n == 63
    
    # Check invalid inputs return 0
    assert calculate_required_sample_size(std=0, mde=0.5) == 0
    assert calculate_required_sample_size(std=1.0, mde=0) == 0
    assert calculate_required_sample_size(std=-1.0, mde=0.5) == 0

def test_estimate_baseline_stats():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, std = estimate_baseline_stats(values)
    assert mean == 3.0
    assert pytest.approx(std) == 1.5811388  # sample standard deviation

    # Handle none and nan
    values_with_nans = [1.0, 2.0, None, np.nan, 3.0]
    mean_nan, std_nan = estimate_baseline_stats(values_with_nans)
    assert mean_nan == 2.0
    assert pytest.approx(std_nan) == 1.0

def test_run_normality_test():
    # Large normal sample should pass normality
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, 100).tolist()
    res = run_normality_test(normal_data)
    assert res["is_normal"] is True
    
    # Skewed sample should fail normality
    skewed_data = np.random.exponential(1.0, 100).tolist()
    res_skewed = run_normality_test(skewed_data)
    assert res_skewed["is_normal"] is False

    # Insufficient samples
    res_short = run_normality_test([1.0, 2.0])
    assert res_short["is_normal"] is False
    assert "Too few" in res_short["note"]

def test_run_homogeneity_test():
    np.random.seed(42)
    group1 = np.random.normal(0, 1.0, 50).tolist()
    group2 = np.random.normal(0, 1.0, 50).tolist()
    group3 = np.random.normal(0, 3.0, 50).tolist()
    
    # Equal variances
    res_equal = run_homogeneity_test(group1, group2)
    assert res_equal["equal_variance"] is True
    
    # Unequal variances
    res_unequal = run_homogeneity_test(group1, group3)
    assert res_unequal["equal_variance"] is False

def test_calculate_cohens_d():
    g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    g2 = [2.0, 3.0, 4.0, 5.0, 6.0]
    d = calculate_cohens_d(g1, g2)
    # Means are 3.0 and 4.0, std dev is pooled. Diff = 1.0. d = 1.0 / pooled_std
    assert d > 0
    assert pytest.approx(d, rel=1e-2) == 0.632  # Cohen's d value

def test_run_bootstrap():
    np.random.seed(42)
    g1 = np.random.normal(10.0, 1.0, 30).tolist()
    g2 = np.random.normal(12.0, 1.0, 30).tolist()
    
    res = run_bootstrap(g1, g2, n_iterations=500)
    assert len(res["bootstrap_means_diff"]) == 500
    assert res["ci_lower"] < res["ci_upper"]
    assert 1.5 < res["ci_lower"] < 2.5

def test_analyze_experiment_data():
    np.random.seed(42)
    # 1. Normal, equal variance -> Student's t-test
    g1 = np.random.normal(5.0, 1.0, 40).tolist()
    g2 = np.random.normal(6.0, 1.0, 40).tolist()
    
    report1 = analyze_experiment_data(g1, g2)
    assert report1["recommended_test"] == "Student's t-test"
    assert report1["stat_significant"] is True
    assert report1["p_value"] < 0.05
    assert report1["cohens_d"] > 0.5
    
    # 2. Normal, unequal variance -> Welch's t-test
    g3 = np.random.normal(6.0, 2.5, 40).tolist()
    report2 = analyze_experiment_data(g1, g3)
    assert report2["recommended_test"] == "Welch's t-test"
    
    # 3. Non-normal -> Mann-Whitney U test
    g_skewed = np.random.exponential(1.0, 40).tolist()
    report3 = analyze_experiment_data(g1, g_skewed)
    assert report3["recommended_test"] == "Mann-Whitney U test"

    # 4. Insufficient samples -> returns error report
    report_err = analyze_experiment_data([1.0], [2.0])
    assert "error" in report_err
    assert report_err["p_value"] == 1.0
