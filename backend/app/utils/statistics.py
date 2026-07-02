import math
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Tuple, Optional

def calculate_required_sample_size(std: float, mde: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculates the required sample size per group for a two-sample independent t-test.
    """
    if std <= 0 or mde <= 0:
        return 0
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    n = 2 * (std ** 2) * ((z_alpha + z_beta) ** 2) / (mde ** 2)
    return int(math.ceil(n))

def estimate_baseline_stats(values: List[float]) -> Tuple[float, float]:
    """
    Estimates the mean and standard deviation of baseline (historical) values.
    """
    clean_values = [v for v in values if v is not None and not np.isnan(v)]
    if not clean_values:
        return 0.0, 0.0
    return float(np.mean(clean_values)), float(np.std(clean_values, ddof=1)) if len(clean_values) > 1 else 0.0

def run_normality_test(data: List[float]) -> Dict[str, Any]:
    """
    Checks normality of a dataset using Shapiro-Wilk test.
    """
    clean_data = [v for v in data if v is not None and not np.isnan(v)]
    n = len(clean_data)
    if n < 3:
        return {"p_value": 0.0, "is_normal": False, "note": "Too few samples to test normality (minimum 3)"}
    
    stat, p = stats.shapiro(clean_data)
    return {
        "p_value": float(p),
        "is_normal": bool(p > 0.05),
        "note": "Normally distributed" if p > 0.05 else "Not normally distributed"
    }

def run_homogeneity_test(control: List[float], treatment: List[float]) -> Dict[str, Any]:
    """
    Checks equal variance between two groups using Levene's test.
    """
    clean_c = [v for v in control if v is not None and not np.isnan(v)]
    clean_t = [v for v in treatment if v is not None and not np.isnan(v)]
    
    if len(clean_c) < 2 or len(clean_t) < 2:
        return {"p_value": 0.0, "equal_variance": True, "note": "Too few samples to test variance (minimum 2 per group)"}
        
    stat, p = stats.levene(clean_c, clean_t)
    return {
        "p_value": float(p),
        "equal_variance": bool(p > 0.05),
        "note": "Equal variances" if p > 0.05 else "Unequal variances"
    }

def calculate_cohens_d(control: List[float], treatment: List[float]) -> float:
    """
    Calculates Cohen's d effect size for two independent samples.
    """
    clean_c = np.array([v for v in control if v is not None and not np.isnan(v)])
    clean_t = np.array([v for v in treatment if v is not None and not np.isnan(v)])
    
    nc, nt = len(clean_c), len(clean_t)
    if nc < 2 or nt < 2:
        return 0.0
        
    var_c = np.var(clean_c, ddof=1)
    var_t = np.var(clean_t, ddof=1)
    
    pooled_std = math.sqrt(((nc - 1) * var_c + (nt - 1) * var_t) / (nc + nt - 2))
    if pooled_std == 0:
        return 0.0
        
    diff = np.mean(clean_t) - np.mean(clean_c)
    return float(diff / pooled_std)

def run_bootstrap(control: List[float], treatment: List[float], n_iterations: int = 2000, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Runs a bootstrap simulation of the difference of means between treatment and control groups.
    """
    clean_c = np.array([v for v in control if v is not None and not np.isnan(v)])
    clean_t = np.array([v for v in treatment if v is not None and not np.isnan(v)])
    
    nc, nt = len(clean_c), len(clean_t)
    if nc == 0 or nt == 0:
        return {"bootstrap_means_diff": [], "ci_lower": 0.0, "ci_upper": 0.0}
        
    rng = np.random.default_rng(42)
    diffs = []
    
    for _ in range(n_iterations):
        boot_c = rng.choice(clean_c, size=nc, replace=True)
        boot_t = rng.choice(clean_t, size=nt, replace=True)
        diffs.append(float(np.mean(boot_t) - np.mean(boot_c)))
        
    diffs = sorted(diffs)
    lower_idx = int(n_iterations * (alpha / 2))
    upper_idx = int(n_iterations * (1 - alpha / 2))
    
    return {
        "bootstrap_means_diff": diffs,
        "ci_lower": diffs[lower_idx],
        "ci_upper": diffs[upper_idx]
    }

def analyze_experiment_data(control: List[float], treatment: List[float], alpha: float = 0.05, mde: Optional[float] = None) -> Dict[str, Any]:
    """
    Performs complete scientific statistical analysis on control and treatment groups.
    """
    clean_c = np.array([v for v in control if v is not None and not np.isnan(v)])
    clean_t = np.array([v for v in treatment if v is not None and not np.isnan(v)])
    
    nc, nt = len(clean_c), len(clean_t)
    
    # Calculate basic descriptive statistics
    mean_c = float(np.mean(clean_c)) if nc > 0 else 0.0
    mean_t = float(np.mean(clean_t)) if nt > 0 else 0.0
    median_c = float(np.median(clean_c)) if nc > 0 else 0.0
    median_t = float(np.median(clean_t)) if nt > 0 else 0.0
    std_c = float(np.std(clean_c, ddof=1)) if nc > 1 else 0.0
    std_t = float(np.std(clean_t, ddof=1)) if nt > 1 else 0.0
    
    abs_diff = mean_t - mean_c
    rel_diff = (abs_diff / mean_c * 100) if mean_c != 0 else 0.0
    
    if nc < 2 or nt < 2:
        return {
            "control_stats": {"n": nc, "mean": mean_c, "median": median_c, "std": std_c},
            "treatment_stats": {"n": nt, "mean": mean_t, "median": median_t, "std": std_t},
            "abs_diff": abs_diff,
            "rel_diff": rel_diff,
            "normality_check": {"control": {"is_normal": False}, "treatment": {"is_normal": False}},
            "homogeneity_check": {"equal_variance": True},
            "recommended_test": "None",
            "p_value": 1.0,
            "stat_significant": False,
            "cohens_d": 0.0,
            "confidence_interval": {"lower": 0.0, "upper": 0.0},
            "bootstrap": {"bootstrap_means_diff": [], "ci_lower": 0.0, "ci_upper": 0.0},
            "achieved_power": 0.0,
            "error": "Insufficient sample size (minimum 2 samples per group required for analysis)"
        }
        
    # Check assumptions
    norm_c = run_normality_test(clean_c)
    norm_t = run_normality_test(clean_t)
    var_check = run_homogeneity_test(clean_c, clean_t)
    
    is_normal = norm_c["is_normal"] and norm_t["is_normal"]
    equal_var = var_check["equal_variance"]
    
    # Run tests
    # 1. Student's t-test
    t_stat_stud, p_stud = stats.ttest_ind(clean_c, clean_t, equal_var=True)
    # 2. Welch's t-test
    t_stat_welch, p_welch = stats.ttest_ind(clean_c, clean_t, equal_var=False)
    # 3. Mann-Whitney U test
    u_stat, p_mw = stats.mannwhitneyu(clean_c, clean_t, alternative="two-sided")
    
    # Selection of recommended test
    if is_normal:
        if equal_var:
            rec_test = "Student's t-test"
            p_val = p_stud
        else:
            rec_test = "Welch's t-test"
            p_val = p_welch
    else:
        rec_test = "Mann-Whitney U test"
        p_val = p_mw
        
    stat_sig = bool(p_val < alpha)
    d = calculate_cohens_d(clean_c, clean_t)
    
    # Calculate analytical CI for the difference of means (Welch-Satterthwaite approximation)
    se = math.sqrt((std_c**2 / nc) + (std_t**2 / nt))
    if se > 0:
        # Degrees of freedom
        numerator = (std_c**2 / nc + std_t**2 / nt) ** 2
        denominator = ((std_c**2 / nc)**2 / (nc - 1)) + ((std_t**2 / nt)**2 / (nt - 1))
        df = numerator / denominator if denominator > 0 else (nc + nt - 2)
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        ci_lower = abs_diff - t_crit * se
        ci_upper = abs_diff + t_crit * se
    else:
        ci_lower, ci_upper = abs_diff, abs_diff
        
    # Bootstrapping
    boot_results = run_bootstrap(clean_c, clean_t, alpha=alpha)
    
    # Calculate achieved statistical power
    achieved_power = 0.0
    if mde and mde > 0:
        std_val = std_c if std_c > 0 else 1.0
        if nc > 1 and nt > 1:
            pooled_var = ((nc - 1) * std_c**2 + (nt - 1) * std_t**2) / (nc + nt - 2)
            if pooled_var > 0:
                std_val = math.sqrt(pooled_var)
        if std_val > 0:
            d_val = mde / std_val
            n_harm = (2 * nc * nt) / (nc + nt)
            lmbda = d_val * math.sqrt(n_harm / 2)
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            achieved_power = float(stats.norm.cdf(lmbda - z_alpha) + stats.norm.cdf(-lmbda - z_alpha))
    
    return {
        "control_stats": {"n": nc, "mean": mean_c, "median": median_c, "std": std_c},
        "treatment_stats": {"n": nt, "mean": mean_t, "median": median_t, "std": std_t},
        "abs_diff": abs_diff,
        "rel_diff": rel_diff,
        "normality_check": {
            "control": norm_c,
            "treatment": norm_t
        },
        "homogeneity_check": var_check,
        "recommended_test": rec_test,
        "p_value": float(p_val),
        "stat_significant": stat_sig,
        "cohens_d": float(d),
        "confidence_interval": {
            "lower": float(ci_lower),
            "upper": float(ci_upper)
        },
        "all_tests_p_values": {
            "students_t": float(p_stud),
            "welchs_t": float(p_welch),
            "mann_whitney_u": float(p_mw)
        },
        "bootstrap": boot_results,
        "achieved_power": achieved_power
    }
