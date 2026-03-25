"""
plots.py
--------
All visualization functions for the A/B test analysis report.
Produces publication-quality figures saved to results/figures/.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from scipy import stats

# ── Style ──────────────────────────────────────────────────────────────────────
PALETTE = {"control": "#4A90D9", "treatment": "#E8613C"}
FIGURES_DIR = Path(__file__).resolve().parents[2] / "results" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight"})


# ── 1. Conversion Rate Bar Chart ───────────────────────────────────────────────
def plot_conversion_rates(
    rate_control: float,
    rate_treatment: float,
    ci_control: tuple,
    ci_treatment: tuple,
    p_value: float,
    save: bool = True,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 5))

    labels = ["Control (A)\nGrey 'Proceed'", "Treatment (B)\nOrange 'Buy Now'"]
    rates = [rate_control * 100, rate_treatment * 100]
    errors = [
        (rate_control - ci_control[0]) * 100,
        (rate_treatment - ci_treatment[0]) * 100,
    ]
    colors = [PALETTE["control"], PALETTE["treatment"]]

    bars = ax.bar(labels, rates, color=colors, width=0.45, edgecolor="white", linewidth=1.5, yerr=errors,
                  capsize=8, error_kw={"elinewidth": 1.5, "ecolor": "#555"})

    # Annotation
    lift = (rate_treatment - rate_control) / rate_control * 100
    ax.annotate(
        f"+{lift:.1f}% lift\np = {p_value:.4f}",
        xy=(0.5, max(rates) + 0.15),
        xycoords=("axes fraction", "data"),
        ha="center", fontsize=12, fontweight="bold",
        color="#2A9D2A" if p_value < 0.05 else "#CC3333",
    )

    ax.set_ylabel("Conversion Rate (%)", fontsize=12)
    ax.set_title("A/B Test: Conversion Rate by Variant", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylim(0, max(rates) * 1.35)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{rate:.2f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")

    if save:
        fig.savefig(FIGURES_DIR / "01_conversion_rate_comparison.png")
    return fig


# ── 2. Bayesian Posterior Distributions ───────────────────────────────────────
def plot_bayesian_posteriors(
    n_control: int, conv_control: int,
    n_treatment: int, conv_treatment: int,
    n_samples: int = 100_000,
    save: bool = True,
) -> plt.Figure:
    rng = np.random.default_rng(42)

    samples_c = rng.beta(1 + conv_control, 1 + n_control - conv_control, size=n_samples)
    samples_t = rng.beta(1 + conv_treatment, 1 + n_treatment - conv_treatment, size=n_samples)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Panel 1: Overlapping posteriors
    ax = axes[0]
    ax.hist(samples_c * 100, bins=80, density=True, alpha=0.65,
            color=PALETTE["control"], label="Control (A)")
    ax.hist(samples_t * 100, bins=80, density=True, alpha=0.65,
            color=PALETTE["treatment"], label="Treatment (B)")
    ax.set_xlabel("Conversion Rate (%)", fontsize=11)
    ax.set_ylabel("Density", fontsize=11)
    ax.set_title("Posterior Distributions", fontsize=13, fontweight="bold")
    ax.legend()

    # Panel 2: Lift distribution
    ax2 = axes[1]
    lift = (samples_t - samples_c) / samples_c * 100
    ax2.hist(lift, bins=80, density=True, color="#7B4FD6", alpha=0.8)
    ax2.axvline(0, color="red", linestyle="--", linewidth=1.5, label="No effect")
    ax2.axvline(lift.mean(), color="black", linestyle="-", linewidth=1.5,
                label=f"Mean = {lift.mean():.1f}%")
    prob_pos = (lift > 0).mean()
    ax2.set_xlabel("Relative Lift (%)", fontsize=11)
    ax2.set_ylabel("Density", fontsize=11)
    ax2.set_title(f"P(Treatment > Control) = {prob_pos:.1%}", fontsize=13, fontweight="bold")
    ax2.legend()

    fig.suptitle("Bayesian Analysis — Beta-Binomial Model", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()

    if save:
        fig.savefig(FIGURES_DIR / "02_bayesian_posteriors.png")
    return fig


# ── 3. Daily Conversion Rate Over Time ────────────────────────────────────────
def plot_daily_conversions(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    daily = (
        df.groupby(["experiment_day", "variant"])["converted"]
        .agg(["mean", "count"])
        .reset_index()
    )
    daily.columns = ["day", "variant", "rate", "n"]
    daily["rate_pct"] = daily["rate"] * 100
    daily["se"] = np.sqrt(daily["rate"] * (1 - daily["rate"]) / daily["n"]) * 100 * 1.96

    fig, ax = plt.subplots(figsize=(11, 5))
    for variant, color in PALETTE.items():
        d = daily[daily["variant"] == variant]
        ax.plot(d["day"], d["rate_pct"], marker="o", color=color,
                linewidth=2, markersize=6, label=variant.title())
        ax.fill_between(d["day"], d["rate_pct"] - d["se"], d["rate_pct"] + d["se"],
                        alpha=0.15, color=color)

    ax.axvline(3, color="grey", linestyle=":", linewidth=1.5, label="Novelty cutoff (day 3)")
    ax.set_xlabel("Experiment Day", fontsize=11)
    ax.set_ylabel("Conversion Rate (%)", fontsize=11)
    ax.set_title("Daily Conversion Rates Over Experiment Duration", fontsize=13, fontweight="bold")
    ax.legend()

    if save:
        fig.savefig(FIGURES_DIR / "03_daily_conversion_rates.png")
    return fig


# ── 4. Segment Analysis ────────────────────────────────────────────────────────
def plot_segment_analysis(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, segment in zip(axes, ["device", "user_type"]):
        seg_data = (
            df.groupby([segment, "variant"])["converted"]
            .agg(["mean", "count"])
            .reset_index()
        )
        seg_data.columns = [segment, "variant", "rate", "n"]
        seg_data["rate_pct"] = seg_data["rate"] * 100

        categories = seg_data[segment].unique()
        x = np.arange(len(categories))
        width = 0.35

        for i, (variant, color) in enumerate(PALETTE.items()):
            rates = [seg_data[(seg_data[segment] == cat) & (seg_data["variant"] == variant)]["rate_pct"].values
                     for cat in categories]
            rates = [r[0] if len(r) > 0 else 0 for r in rates]
            bars = ax.bar(x + i * width - width / 2, rates, width, label=variant.title(), color=color, alpha=0.85)
            for bar, rate in zip(bars, rates):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                        f"{rate:.1f}%", ha="center", va="bottom", fontsize=8.5)

        ax.set_xticks(x)
        ax.set_xticklabels([c.title() for c in categories])
        ax.set_ylabel("Conversion Rate (%)", fontsize=11)
        ax.set_title(f"Conversion Rate by {segment.replace('_', ' ').title()}", fontsize=12, fontweight="bold")
        ax.legend()

    fig.suptitle("Segment Analysis — Consistency Check", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()

    if save:
        fig.savefig(FIGURES_DIR / "04_segment_analysis.png")
    return fig


# ── 5. AOV Distribution ────────────────────────────────────────────────────────
def plot_aov_distribution(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 5))

    for variant, color in PALETTE.items():
        data = df[(df["variant"] == variant) & (df["converted"] == 1)]["order_value"]
        ax.hist(data, bins=50, density=True, alpha=0.6, color=color, label=f"{variant.title()} (mean: ${data.mean():.2f})")
        mu, std = data.mean(), data.std()
        x = np.linspace(data.min(), data.max(), 300)
        ax.plot(x, stats.norm.pdf(x, mu, std), color=color, linewidth=2)

    ax.set_xlabel("Order Value ($)", fontsize=11)
    ax.set_ylabel("Density", fontsize=11)
    ax.set_title("Average Order Value Distribution (Converters Only)", fontsize=13, fontweight="bold")
    ax.legend()

    if save:
        fig.savefig(FIGURES_DIR / "05_aov_distribution.png")
    return fig


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils.data_loader import load_processed

    df = load_processed()
    control = df[df["variant"] == "control"]
    treatment = df[df["variant"] == "treatment"]

    print("⏳ Generating figures...")
    plot_conversion_rates(
        rate_control=control["converted"].mean(),
        rate_treatment=treatment["converted"].mean(),
        ci_control=(0.0367, 0.0397),
        ci_treatment=(0.0433, 0.0469),
        p_value=0.0003,
    )
    plot_bayesian_posteriors(len(control), int(control["converted"].sum()),
                              len(treatment), int(treatment["converted"].sum()))
    plot_daily_conversions(df)
    plot_segment_analysis(df)
    plot_aov_distribution(df)
    print(f"✅ All figures saved to {FIGURES_DIR}")
