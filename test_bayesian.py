"""
test_bayesian.py
----------------
Unit tests for Bayesian analysis functions.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis.bayesian import beta_binomial_analysis, _hdi


class TestBetaBinomialAnalysis:
    def test_treatment_clearly_better(self):
        result = beta_binomial_analysis(
            n_control=10_000, conv_control=300,
            n_treatment=10_000, conv_treatment=500,
        )
        assert result["prob_treatment_better"] > 0.99
        assert result["decision"] == "treatment"

    def test_control_clearly_better(self):
        result = beta_binomial_analysis(
            n_control=10_000, conv_control=500,
            n_treatment=10_000, conv_treatment=300,
        )
        assert result["prob_treatment_better"] < 0.01
        assert result["decision"] == "control"

    def test_uncertain_case(self):
        result = beta_binomial_analysis(
            n_control=1_000, conv_control=50,
            n_treatment=1_000, conv_treatment=52,
        )
        # Should be uncertain — probability near 50%
        assert 0.3 < result["prob_treatment_better"] < 0.8

    def test_output_keys(self):
        result = beta_binomial_analysis(1000, 50, 1000, 60)
        required = [
            "prob_treatment_better", "prob_control_better",
            "expected_relative_lift_mean", "decision",
            "posterior_control_mean", "posterior_treatment_mean",
        ]
        for key in required:
            assert key in result

    def test_probabilities_sum_to_one(self):
        result = beta_binomial_analysis(5000, 200, 5000, 250)
        total = result["prob_treatment_better"] + result["prob_control_better"]
        assert abs(total - 1.0) < 1e-6

    def test_reproducibility(self):
        r1 = beta_binomial_analysis(5000, 200, 5000, 250, seed=0)
        r2 = beta_binomial_analysis(5000, 200, 5000, 250, seed=0)
        assert r1["prob_treatment_better"] == r2["prob_treatment_better"]


class TestHDI:
    def test_hdi_contains_mode(self):
        rng = np.random.default_rng(0)
        samples = rng.normal(0, 1, 100_000)
        low, high = _hdi(samples, prob=0.95)
        assert low < 0 < high

    def test_hdi_width(self):
        rng = np.random.default_rng(0)
        samples = rng.normal(0, 1, 100_000)
        low, high = _hdi(samples, prob=0.95)
        # For standard normal, 95% interval is approx ±1.96
        assert abs(low - (-1.96)) < 0.05
        assert abs(high - 1.96) < 0.05
