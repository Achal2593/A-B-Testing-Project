"""
test_frequentist.py
-------------------
Unit tests for frequentist hypothesis testing functions.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis.frequentist import (
    test_conversion_rate,
    test_continuous_metric,
    bonferroni_correction,
)


class TestConversionRate:
    def test_significant_difference(self):
        result = test_conversion_rate(
            n_control=24_000, conv_control=917,
            n_treatment=24_000, conv_treatment=1082,
        )
        assert result["significant"] is True
        assert result["p_value"] < 0.05
        assert result["relative_lift_pct"] > 0

    def test_no_difference(self):
        result = test_conversion_rate(
            n_control=10_000, conv_control=500,
            n_treatment=10_000, conv_treatment=503,
        )
        assert result["significant"] is False
        assert result["p_value"] > 0.05

    def test_lift_calculation(self):
        result = test_conversion_rate(
            n_control=1000, conv_control=100,
            n_treatment=1000, conv_treatment=120,
        )
        assert abs(result["relative_lift_pct"] - 20.0) < 0.01
        assert abs(result["absolute_lift"] - 0.02) < 1e-6

    def test_output_keys_present(self):
        result = test_conversion_rate(1000, 50, 1000, 60)
        required_keys = ["p_value", "z_statistic", "significant", "relative_lift_pct",
                         "ci_control_95", "ci_treatment_95"]
        for key in required_keys:
            assert key in result


class TestContinuousMetric:
    def test_significant_means(self):
        rng = np.random.default_rng(42)
        control = pd.Series(rng.normal(67, 18, 5000))
        treatment = pd.Series(rng.normal(80, 18, 5000))  # Large difference
        result = test_continuous_metric(control, treatment, "Test Metric")
        assert result["significant"] is True

    def test_equal_means_not_significant(self):
        rng = np.random.default_rng(42)
        control = pd.Series(rng.normal(67, 18, 5000))
        treatment = pd.Series(rng.normal(67.1, 18, 5000))  # Tiny difference
        result = test_continuous_metric(control, treatment, "Test Metric")
        assert result["significant"] is False

    def test_output_structure(self):
        rng = np.random.default_rng(0)
        c = pd.Series(rng.normal(50, 10, 200))
        t = pd.Series(rng.normal(55, 10, 200))
        result = test_continuous_metric(c, t, "My Metric")
        assert result["metric"] == "My Metric"
        assert result["n_control"] == 200
        assert result["n_treatment"] == 200


class TestBonferroniCorrection:
    def test_correction_applied(self):
        p_values = [0.02, 0.04, 0.001]
        results = bonferroni_correction(p_values, alpha=0.05)
        assert len(results) == 3
        # With 3 tests, corrected alpha = 0.0167
        assert results[0]["corrected_alpha"] == pytest.approx(0.05 / 3, rel=1e-4)

    def test_significance_after_correction(self):
        p_values = [0.001, 0.04, 0.60]
        results = bonferroni_correction(p_values, alpha=0.05)
        assert results[0]["significant_after_correction"] is True   # 0.001 < 0.0167
        assert results[1]["significant_after_correction"] is False  # 0.04 > 0.0167
        assert results[2]["significant_after_correction"] is False

    def test_single_test_no_correction(self):
        results = bonferroni_correction([0.03], alpha=0.05)
        assert results[0]["corrected_alpha"] == pytest.approx(0.05)
