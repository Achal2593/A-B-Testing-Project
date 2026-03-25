# Data Directory

This directory contains the raw and processed A/B experiment data.

## Structure

```
data/
├── raw/
│   ├── ab_test_raw.csv          ← Full raw data (generated locally, gitignored)
│   └── ab_test_raw_sample.csv   ← 30-row sample for reference (tracked)
└── processed/
    └── ab_test_cleaned.csv      ← Cleaned data (generated locally, gitignored)
```

## Generating Data Locally

```bash
python src/utils/data_loader.py --generate
```

This creates both `ab_test_raw.csv` (48,239 rows) and `ab_test_cleaned.csv` (~40,000 rows after novelty-effect filter).

## Column Reference

| Column | Type | Description |
|---|---|---|
| user_id | str | Unique user identifier |
| variant | str | `control` or `treatment` |
| device | str | `mobile`, `desktop`, `tablet` |
| user_type | str | `new` or `returning` |
| experiment_day | int | Day 1–14 of experiment |
| converted | int | 1 = purchased, 0 = did not |
| order_value | float | Order total ($); 0 if not converted |
| returned | int | 1 = item returned/refunded |
| bounced | int | 1 = bounced from checkout page |
| session_duration_sec | int | Time on page in seconds |

**Processed-only columns:**

| Column | Description |
|---|---|
| is_treatment | Binary flag (1 = treatment) |
| revenue | order_value × (1 − returned) |
