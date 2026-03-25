"""
test_data_loader.py
--------------------
Unit tests for data generation and preprocessing.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.data_loader import generate_ab_data, preprocess


class TestGenerateAbData:
    def test_output_shape(self):
        df = generate_ab_data(n_users=1000)
        assert len(df) == 1000

    def test_columns_present(self):
        df = generate_ab_data(n_users=100)
        expected_cols = ["user_id", "variant", "device", "user_type",
                         "experiment_day", "converted", "order_value",
                         "returned", "bounced", "session_duration_sec"]
        for col in expected_cols:
            assert col in df.columns

    def test_variant_split_balanced(self):
        df = generate_ab_data(n_users=10_000, seed=42)
        ratio = df["variant"].value_counts(normalize=True)
        assert abs(ratio["control"] - 0.5) < 0.02
        assert abs(ratio["treatment"] - 0.5) < 0.02

    def test_conversion_rates_plausible(self):
        df = generate_ab_data(n_users=50_000, seed=42)
        for variant in ["control", "treatment"]:
            rate = df[df["variant"] == variant]["converted"].mean()
            assert 0.02 < rate < 0.08

    def test_order_value_zero_for_non_converters(self):
        df = generate_ab_data(n_users=5000)
        non_converters = df[df["converted"] == 0]
        assert (non_converters["order_value"] == 0).all()

    def test_reproducibility(self):
        df1 = generate_ab_data(n_users=500, seed=99)
        df2 = generate_ab_data(n_users=500, seed=99)
        pd.testing.assert_frame_equal(df1, df2)

    def test_unique_user_ids(self):
        df = generate_ab_data(n_users=1000)
        assert df["user_id"].nunique() == 1000


class TestPreprocess:
    def test_novelty_days_removed(self):
        df = generate_ab_data(n_users=5000, seed=42)
        clean = preprocess(df)
        assert clean["experiment_day"].min() > 3

    def test_is_treatment_column(self):
        df = generate_ab_data(n_users=1000, seed=42)
        clean = preprocess(df)
        assert "is_treatment" in clean.columns
        assert set(clean["is_treatment"].unique()).issubset({0, 1})

    def test_revenue_column(self):
        df = generate_ab_data(n_users=1000, seed=42)
        clean = preprocess(df)
        assert "revenue" in clean.columns
        # Revenue should be 0 when order_value is 0
        assert (clean[clean["order_value"] == 0]["revenue"] == 0).all()

    def test_no_negative_order_values(self):
        df = generate_ab_data(n_users=5000)
        clean = preprocess(df)
        assert (clean["order_value"] >= 0).all()
