"""
data_loader.py
--------------
Data ingestion, synthetic data generation, and preprocessing for A/B test.
"""

import numpy as np
import pandas as pd
import argparse
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


# ── Synthetic Data Generation ──────────────────────────────────────────────────
def generate_ab_data(
    n_users: int = 48_239,
    control_conv_rate: float = 0.0382,
    treatment_conv_rate: float = 0.0451,
    control_aov: float = 67.40,
    treatment_aov: float = 68.10,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a realistic A/B test dataset simulating a 14-day checkout experiment.

    Parameters
    ----------
    n_users : int
        Total number of unique users in the experiment.
    control_conv_rate : float
        True conversion rate for the control group.
    treatment_conv_rate : float
        True conversion rate for the treatment group.
    control_aov : float
        Mean average order value for the control group.
    treatment_aov : float
        Mean average order value for the treatment group.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Full experiment log with one row per user.
    """
    rng = np.random.default_rng(seed)

    # ── Assign variants ────────────────────────────────────────────────────────
    variants = rng.choice(["control", "treatment"], size=n_users, p=[0.5, 0.5])

    # ── User metadata ──────────────────────────────────────────────────────────
    devices = rng.choice(["mobile", "desktop", "tablet"], size=n_users, p=[0.54, 0.40, 0.06])
    user_types = rng.choice(["new", "returning"], size=n_users, p=[0.62, 0.38])

    # Assign experiment day (uniform over 14 days)
    days = rng.integers(1, 15, size=n_users)

    # ── Conversions ────────────────────────────────────────────────────────────
    conv_rate = np.where(variants == "control", control_conv_rate, treatment_conv_rate)
    converted = rng.binomial(1, conv_rate)

    # ── Average Order Value (only for converters) ──────────────────────────────
    aov_mean = np.where(variants == "control", control_aov, treatment_aov)
    order_value = np.where(
        converted == 1,
        rng.normal(aov_mean, 18.0),
        0.0,
    )
    order_value = np.maximum(order_value, 0)  # No negative orders

    # ── Return / Refund Rate ───────────────────────────────────────────────────
    return_prob = np.where(converted == 1, np.where(variants == "control", 0.082, 0.084), 0.0)
    returned = rng.binomial(1, return_prob)

    # ── Bounce Rate ────────────────────────────────────────────────────────────
    bounce_prob = np.where(variants == "control", 0.421, 0.418)
    bounced = rng.binomial(1, bounce_prob)

    # ── Session duration (seconds) ─────────────────────────────────────────────
    session_duration = rng.exponential(120, size=n_users).astype(int)
    session_duration = np.where(bounced == 1, rng.integers(5, 30, size=n_users), session_duration)

    # ── Assemble DataFrame ─────────────────────────────────────────────────────
    df = pd.DataFrame(
        {
            "user_id": [f"USR{str(i).zfill(6)}" for i in range(n_users)],
            "variant": variants,
            "device": devices,
            "user_type": user_types,
            "experiment_day": days,
            "converted": converted,
            "order_value": order_value.round(2),
            "returned": returned,
            "bounced": bounced,
            "session_duration_sec": session_duration,
        }
    )

    return df


# ── Preprocessing ──────────────────────────────────────────────────────────────
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and feature-engineer raw experiment data.

    Steps
    -----
    - Remove first 3 days (novelty effect buffer)
    - Clip extreme order values (> 99th percentile)
    - Encode binary flags as integers
    - Add convenience columns

    Parameters
    ----------
    df : pd.DataFrame
        Raw experiment data.

    Returns
    -------
    pd.DataFrame
        Cleaned and enriched dataset.
    """
    df = df.copy()

    # Remove novelty-effect days
    df = df[df["experiment_day"] > 3].reset_index(drop=True)

    # Clip extreme order values
    q99 = df.loc[df["order_value"] > 0, "order_value"].quantile(0.99)
    df["order_value"] = df["order_value"].clip(upper=q99)

    # Binary variant flag
    df["is_treatment"] = (df["variant"] == "treatment").astype(int)

    # Revenue column (order_value only if not returned)
    df["revenue"] = df["order_value"] * (1 - df["returned"])

    return df


# ── Loaders ────────────────────────────────────────────────────────────────────
def load_raw(path: Path | None = None) -> pd.DataFrame:
    path = path or RAW_DIR / "ab_test_raw.csv"
    return pd.read_csv(path)


def load_processed(path: Path | None = None) -> pd.DataFrame:
    path = path or PROCESSED_DIR / "ab_test_cleaned.csv"
    return pd.read_csv(path)


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate or preprocess A/B test data.")
    parser.add_argument("--generate", action="store_true", help="Generate synthetic data")
    parser.add_argument("--n_users", type=int, default=48_239)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.generate:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        print("⏳ Generating synthetic A/B test data...")
        raw = generate_ab_data(n_users=args.n_users, seed=args.seed)
        raw.to_csv(RAW_DIR / "ab_test_raw.csv", index=False)
        print(f"✅ Raw data saved → {RAW_DIR / 'ab_test_raw.csv'}  ({len(raw):,} rows)")

        print("⏳ Preprocessing...")
        clean = preprocess(raw)
        clean.to_csv(PROCESSED_DIR / "ab_test_cleaned.csv", index=False)
        print(f"✅ Clean data saved → {PROCESSED_DIR / 'ab_test_cleaned.csv'}  ({len(clean):,} rows)")
