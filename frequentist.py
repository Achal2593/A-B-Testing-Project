"""
frequentist.py
--------------
Frequentist hypothesis tests for A/B experiment analysis.
Covers conversion rate (z-test), AOV (t-test), and multiple-metric corrections.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from typing import Optional


# ── Conversion Rate Test ───────────────────────────────────────────────────────
def test_conversion_rate(
    n_control: int,
    conv_control: int,
    n_treatment: int,
    conv_treatment: int,
    alpha: float = 0.05,
) -> dict:
    """
    Two-proportion Z-test for conversion rates.

    Parameters
    ----------
    n_control, conv_control : int
        Size and conversions in control group.
    n_treatment, conv_treatment : int
        Size and conversions in treatment group.
    alpha : float
        Significance level.

    Returns
    -------
    dict
        Test statistic, p-value, CIs, lift, and significance decision.
    """
    rate_control = conv_control / n_control
    rate_treatment = conv_treatment / n_treatment

    count = np.array([conv_control, conv_treatment])
    nobs = np.array([n_control, n_treatment])

    z_stat, p_value = proportions_ztest(count, nobs, alternative="two-sided")

    ci_control = proportion_confint(conv_control, n_control, alpha=alpha, method="wilson")
    ci_treatment = proportion_confint(conv_treatment, n_treatment, alpha=alpha, method="wilson")

    absolute_lift = rate_treatment - rate_control
    relative_lift = absolute_lift / rate_control

    return {
        "metric": "Conversion Rate",
        "control_rate": round(rate_control, 6),
        "treatment_rate": round(rate_treatment, 6),
        "absolute_lift": round(absolute_lift, 6),
        "relative_lift_pct": round(relative_lift * 100, 2),
        "z_statistic": round(z_stat, 4),
        "p_value": round(p_value, 6),
        "ci_control_95": tuple(round(x, 6) for x in ci_control),
        "ci_treatment_95": tuple(round(x, 6) for x in ci_treatment),
        "significant": p_value < alpha,
        "alpha": alpha,
    }


# ── Continuous Metric Test ─────────────────────────────────────────────────────
def test_continuous_metric(
    control_values: pd.Series,
    treatment_values: pd.Series,
    metric_name: str = "Metric",
    alpha: float = 0.05,
) -> dict:
    """
    Welch's two-sample t-test for continuous metrics (e.g., AOV, session duration).

    Parameters
    ----------
    control_values, treatment_values : pd.Series
        Metric values for each group.
    metric_name : str
        Human-readable metric name for reporting.
    alpha : float
        Significance level.

    Returns
    -------
    dict
        Test results including means, CIs, and significance.
    """
    t_stat, p_value = stats.ttest_ind(control_values, treatment_values, equal_var=False)

    mean_c = control_values.mean()
    mean_t = treatment_values.mean()
    n_c, n_t = len(control_values), len(treatment_values)

    sem_c = stats.sem(control_values)
    sem_t = stats.sem(treatment_values)

    ci_control = stats.t.interval(1 - alpha, df=n_c - 1, loc=mean_c, scale=sem_c)
    ci_treatment = stats.t.interval(1 - alpha, df=n_t - 1, loc=mean_t, scale=sem_t)

    absolute_diff = mean_t - mean_c
    relative_diff = absolute_diff / mean_c if mean_c != 0 else np.nan

    return {
        "metric": metric_name,
        "control_mean": round(mean_c, 4),
        "treatment_mean": round(mean_t, 4),
        "absolute_diff": round(absolute_diff, 4),
        "relative_diff_pct": round(relative_diff * 100, 2) if not np.isnan(relative_diff) else None,
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_value, 6),
        "ci_control_95": tuple(round(x, 4) for x in ci_control),
        "ci_treatment_95": tuple(round(x, 4) for x in ci_treatment),
        "n_control": n_c,
        "n_treatment": n_t,
        "significant": p_value < alpha,
        "alpha": alpha,
    }


# ── Multiple Comparisons Correction ───────────────────────────────────────────
def bonferroni_correction(p_values: list[float], alpha: float = 0.05) -> list[dict]:
    """
    Apply Bonferroni correction for multiple hypothesis tests.

    Parameters
    ----------
    p_values : list of float
        Raw p-values from individual tests.
    alpha : float
        Family-wise error rate.

    Returns
    -------
    list of dict
        Corrected threshold and significance for each test.
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests

    return [
        {
            "p_value": round(p, 6),
            "corrected_alpha": round(corrected_alpha, 6),
            "n_tests": n_tests,
            "significant_after_correction": p < corrected_alpha,
        }
        for p in p_values
    ]


# ── Full Pipeline ──────────────────────────────────────────────────────────────
def run_full_analysis(df: pd.DataFrame, alpha: float = 0.05) -> dict:
    """
    Run all frequentist tests on a cleaned A/B test DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned experiment data from data_loader.preprocess().
    alpha : float
        Significance level for all tests.

    Returns
    -------
    dict
        Results for all metrics.
    """
    control = df[df["variant"] == "control"]
    treatment = df[df["variant"] == "treatment"]

    # Conversion rate
    conv_result = test_conversion_rate(
        n_control=len(control),
        conv_control=control["converted"].sum(),
        n_treatment=len(treatment),
        conv_treatment=treatment["converted"].sum(),
        alpha=alpha,
    )

    # AOV (converters only)
    aov_result = test_continuous_metric(
        control_values=control.loc[control["converted"] == 1, "order_value"],
        treatment_values=treatment.loc[treatment["converted"] == 1, "order_value"],
        metric_name="Average Order Value",
        alpha=alpha,
    )

    # Session duration
    session_result = test_continuous_metric(
        control_values=control["session_duration_sec"],
        treatment_values=treatment["session_duration_sec"],
        metric_name="Session Duration (sec)",
        alpha=alpha,
    )

    # Multiple comparisons
    p_values = [conv_result["p_value"], aov_result["p_value"], session_result["p_value"]]
    bonferroni = bonferroni_correction(p_values, alpha=alpha)

    return {
        "conversion_rate": conv_result,
        "aov": aov_result,
        "session_duration": session_result,
        "bonferroni_corrections": bonferroni,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
    from src.utils.data_loader import load_processed

    df = load_processed()
    results = run_full_analysis(df)

    print("\n" + "=" * 60)
    print("  FREQUENTIST A/B TEST RESULTS")
    print("=" * 60)

    for metric, r in results.items():
        if metric == "bonferroni_corrections":
            continue
        print(f"\n  [{r['metric']}]")
        for k, v in r.items():
            if k != "metric":
                print(f"    {k:<30} {v}")
