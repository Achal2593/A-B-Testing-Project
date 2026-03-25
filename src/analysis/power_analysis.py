"""
power_analysis.py
-----------------
Pre-experiment sample size calculation and power analysis.
"""

import numpy as np
from scipy import stats
from statsmodels.stats.power import NormalIndPower, zt_ind_solve_power


def required_sample_size(
    baseline_rate: float,
    mde_relative: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_tailed: bool = True,
) -> dict:
    """
    Calculate the minimum sample size per variant for a two-proportion test.

    Parameters
    ----------
    baseline_rate : float
        Baseline conversion rate (control group, e.g. 0.038).
    mde_relative : float
        Minimum detectable effect as a relative lift (e.g. 0.05 for 5%).
    alpha : float
        Significance level (Type I error rate).
    power : float
        Desired statistical power (1 - Type II error rate).
    two_tailed : bool
        Whether to use a two-tailed test.

    Returns
    -------
    dict
        Sample size per variant, total, and effect size.
    """
    treatment_rate = baseline_rate * (1 + mde_relative)
    effect_size = _cohens_h(baseline_rate, treatment_rate)

    analysis = NormalIndPower()
    n_per_group = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        alternative="two-sided" if two_tailed else "larger",
    )
    n_per_group = int(np.ceil(n_per_group))

    return {
        "baseline_rate": baseline_rate,
        "treatment_rate": round(treatment_rate, 6),
        "mde_absolute": round(treatment_rate - baseline_rate, 6),
        "mde_relative": mde_relative,
        "cohens_h": round(effect_size, 6),
        "n_per_group": n_per_group,
        "n_total": n_per_group * 2,
        "alpha": alpha,
        "power": power,
        "two_tailed": two_tailed,
    }


def _cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions."""
    return abs(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2)))


def achieved_power(
    n_per_group: int,
    baseline_rate: float,
    treatment_rate: float,
    alpha: float = 0.05,
) -> float:
    """
    Compute the actual power achieved for a given sample size.

    Parameters
    ----------
    n_per_group : int
        Observed sample size per group.
    baseline_rate : float
        Control conversion rate.
    treatment_rate : float
        Treatment conversion rate.
    alpha : float
        Significance level.

    Returns
    -------
    float
        Statistical power.
    """
    effect_size = _cohens_h(baseline_rate, treatment_rate)
    analysis = NormalIndPower()
    return analysis.solve_power(
        effect_size=effect_size,
        nobs1=n_per_group,
        alpha=alpha,
        alternative="two-sided",
    )


def srm_check(n_control: int, n_treatment: int, expected_ratio: float = 0.5) -> dict:
    """
    Sample Ratio Mismatch (SRM) test using a chi-squared goodness-of-fit test.

    Detects whether the traffic split significantly deviates from the
    expected ratio — a sign of instrumentation bugs.

    Parameters
    ----------
    n_control : int
        Number of users in control group.
    n_treatment : int
        Number of users in treatment group.
    expected_ratio : float
        Expected fraction in treatment (default 0.5 for 50/50 split).

    Returns
    -------
    dict
        Chi-squared statistic, p-value, and whether SRM is detected.
    """
    n_total = n_control + n_treatment
    expected_treatment = n_total * expected_ratio
    expected_control = n_total * (1 - expected_ratio)

    chi2, p_value = stats.chisquare(
        f_obs=[n_control, n_treatment],
        f_exp=[expected_control, expected_treatment],
    )

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "n_total": n_total,
        "observed_ratio": round(n_treatment / n_total, 4),
        "expected_ratio": expected_ratio,
        "chi2_stat": round(chi2, 4),
        "p_value": round(p_value, 6),
        "srm_detected": p_value < 0.01,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  A/B TEST POWER ANALYSIS")
    print("=" * 60)

    result = required_sample_size(
        baseline_rate=0.0382,
        mde_relative=0.05,
        alpha=0.05,
        power=0.80,
    )
    for k, v in result.items():
        print(f"  {k:<25} {v}")

    print("\n  SRM CHECK")
    srm = srm_check(n_control=24_102, n_treatment=24_137)
    for k, v in srm.items():
        print(f"  {k:<25} {v}")
