"""
bayesian.py
-----------
Bayesian A/B analysis using Beta-Binomial conjugate model.
Provides probability of superiority, expected loss, and credible intervals
without requiring PyMC (uses pure NumPy Monte Carlo sampling).
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional


# ── Beta-Binomial Conjugate Model ──────────────────────────────────────────────
def beta_binomial_analysis(
    n_control: int,
    conv_control: int,
    n_treatment: int,
    conv_treatment: int,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
    n_samples: int = 100_000,
    seed: int = 42,
    hdi_prob: float = 0.95,
) -> dict:
    """
    Bayesian analysis of conversion rates using a Beta-Binomial model.

    Uses a Beta(alpha_prior, beta_prior) prior (default: uniform/non-informative).
    Posterior is analytically derived: Beta(alpha_prior + conversions, beta_prior + non-conversions).
    Inference is performed via Monte Carlo sampling.

    Parameters
    ----------
    n_control, conv_control : int
        Sample size and successes for control group.
    n_treatment, conv_treatment : int
        Sample size and successes for treatment group.
    alpha_prior, beta_prior : float
        Beta distribution prior parameters.
    n_samples : int
        Number of Monte Carlo samples.
    seed : int
        Random seed.
    hdi_prob : float
        Width of Highest Density Interval (e.g., 0.95 for 95% HDI).

    Returns
    -------
    dict
        Posterior statistics, probability of superiority, expected loss.
    """
    rng = np.random.default_rng(seed)

    # Posterior parameters
    alpha_c = alpha_prior + conv_control
    beta_c = beta_prior + (n_control - conv_control)

    alpha_t = alpha_prior + conv_treatment
    beta_t = beta_prior + (n_treatment - conv_treatment)

    # Posterior samples
    samples_c = rng.beta(alpha_c, beta_c, size=n_samples)
    samples_t = rng.beta(alpha_t, beta_t, size=n_samples)

    # Probability B > A
    prob_treatment_better = (samples_t > samples_c).mean()

    # Relative lift distribution
    relative_lift = (samples_t - samples_c) / samples_c
    lift_mean = relative_lift.mean()
    lift_std = relative_lift.std()

    # Expected loss (opportunity cost of choosing wrong variant)
    expected_loss_control = np.maximum(samples_t - samples_c, 0).mean()
    expected_loss_treatment = np.maximum(samples_c - samples_t, 0).mean()

    # Highest Density Interval
    hdi_c = _hdi(samples_c, prob=hdi_prob)
    hdi_t = _hdi(samples_t, prob=hdi_prob)
    hdi_lift = _hdi(relative_lift, prob=hdi_prob)

    return {
        "model": "Beta-Binomial (conjugate)",
        "prior": f"Beta({alpha_prior}, {beta_prior})",
        "n_samples": n_samples,
        # Posteriors
        "posterior_control_mean": round(samples_c.mean(), 6),
        "posterior_control_std": round(samples_c.std(), 6),
        f"hdi_{int(hdi_prob*100)}_control": tuple(round(x, 6) for x in hdi_c),
        "posterior_treatment_mean": round(samples_t.mean(), 6),
        "posterior_treatment_std": round(samples_t.std(), 6),
        f"hdi_{int(hdi_prob*100)}_treatment": tuple(round(x, 6) for x in hdi_t),
        # Decision metrics
        "prob_treatment_better": round(prob_treatment_better, 6),
        "prob_control_better": round(1 - prob_treatment_better, 6),
        "expected_relative_lift_mean": round(lift_mean, 6),
        "expected_relative_lift_std": round(lift_std, 6),
        f"hdi_{int(hdi_prob*100)}_relative_lift": tuple(round(x, 6) for x in hdi_lift),
        "expected_loss_if_control": round(expected_loss_control, 8),
        "expected_loss_if_treatment": round(expected_loss_treatment, 8),
        "decision": "treatment" if expected_loss_treatment < expected_loss_control else "control",
    }


def _hdi(samples: np.ndarray, prob: float = 0.95) -> tuple:
    """
    Compute the Highest Density Interval (HDI) for a 1D array of samples.

    Parameters
    ----------
    samples : np.ndarray
        Posterior samples.
    prob : float
        Coverage probability.

    Returns
    -------
    tuple
        (lower, upper) bounds of the HDI.
    """
    sorted_samples = np.sort(samples)
    n = len(sorted_samples)
    interval_idx_inc = int(np.floor(prob * n))
    n_intervals = n - interval_idx_inc

    interval_width = sorted_samples[interval_idx_inc:] - sorted_samples[:n_intervals]
    min_idx = np.argmin(interval_width)

    return (sorted_samples[min_idx], sorted_samples[min_idx + interval_idx_inc])


# ── Full Bayesian Pipeline ─────────────────────────────────────────────────────
def run_bayesian_analysis(df: pd.DataFrame, n_samples: int = 100_000) -> dict:
    """
    Run Bayesian conversion rate analysis on a cleaned A/B test DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned data from data_loader.preprocess().
    n_samples : int
        Monte Carlo sample count.

    Returns
    -------
    dict
        Full Bayesian results.
    """
    control = df[df["variant"] == "control"]
    treatment = df[df["variant"] == "treatment"]

    return beta_binomial_analysis(
        n_control=len(control),
        conv_control=int(control["converted"].sum()),
        n_treatment=len(treatment),
        conv_treatment=int(treatment["converted"].sum()),
        n_samples=n_samples,
    )


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
    from src.utils.data_loader import load_processed

    df = load_processed()
    results = run_bayesian_analysis(df)

    print("\n" + "=" * 60)
    print("  BAYESIAN A/B TEST RESULTS")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {k:<45} {v}")
