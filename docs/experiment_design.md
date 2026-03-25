# Experiment Design Document

**Experiment ID:** EXP-2024-011  
**Status:** Complete  
**Owner:** Data Science Team  
**Stakeholders:** Product, Engineering, Marketing  
**Last Updated:** 2024-11-15

---

## 1. Business Context

The checkout funnel is the most revenue-critical part of our platform. Current analytics show that **38% of users who add items to cart do not complete checkout**. The hypothesis is that our existing grey "Proceed" button is visually weak and lacks urgency — contributing to cart abandonment.

---

## 2. Hypothesis

**H₀ (Null):** Changing the checkout button has no effect on conversion rate.  
**H₁ (Alternative):** The orange "Buy Now — Secure Checkout" button increases conversion rate.

---

## 3. Variants

| Variant | Description | Traffic |
|---|---|---|
| A (Control) | Grey button, text: "Proceed" | 50% |
| B (Treatment) | Orange (#FF6B35) button, text: "Buy Now — Secure Checkout" | 50% |

---

## 4. Metrics

### Primary Metric
- **Conversion Rate** — % of checkout-page visitors who complete purchase

### Secondary Metrics (guardrail)
- **Average Order Value (AOV)** — must not decrease
- **Return/Refund Rate** — must not increase
- **Bounce Rate** — informational

---

## 5. Statistical Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Significance Level (α) | 0.05 | Standard industry threshold |
| Power (1-β) | 0.80 | Acceptable false-negative rate |
| MDE (relative) | 2% | Minimum business-relevant lift |
| Test Type | Two-sided | Detect both positive and negative effects |
| Required n (per group) | 21,000 | From power analysis |

---

## 6. Validity & Bias Controls

- **Randomization unit:** User ID (cookie-based, consistent across sessions)
- **Novelty effect buffer:** First 3 days of data excluded from final analysis
- **SRM check:** Chi-squared test on traffic split before analysis
- **No interaction effects:** Experiment isolated from other active tests

---

## 7. Duration

- **Start date:** 2024-10-15
- **End date:** 2024-10-29
- **Duration:** 14 days (covers 2 full weekday/weekend cycles)

---

## 8. Rollout Plan

- If significant positive result → 100% rollout within 1 sprint
- If null result → revert, consider alternative treatments
- If negative result → revert immediately, investigate cause
