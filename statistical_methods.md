# Statistical Methods

## 1. Frequentist Analysis

### Two-Proportion Z-Test
Used for the primary metric (conversion rate). Assumes large samples (n > 1000), uses Wilson score confidence intervals.

**Formula:**  
z = (p̂₁ - p̂₂) / √(p̂(1-p̂)(1/n₁ + 1/n₂))

### Welch's t-Test
Used for continuous secondary metrics (AOV, session duration). Does not assume equal variances.

### Multiple Comparisons
Bonferroni correction applied across all tested metrics to control family-wise error rate.

---

## 2. Bayesian Analysis

### Model
- **Prior:** Beta(1, 1) — uniform, non-informative
- **Likelihood:** Binomial
- **Posterior:** Beta(α + conversions, β + non-conversions) — analytically derived

### Inference
- **Monte Carlo sampling:** 100,000 draws from each posterior
- **Probability of superiority:** P(θ_treatment > θ_control)
- **Expected loss:** Average opportunity cost of choosing each variant
- **HDI:** Highest Density Interval (95%) — narrowest interval containing 95% of posterior mass

---

## 3. Validity Checks

### Sample Ratio Mismatch (SRM)
Chi-squared test on actual traffic split vs expected 50/50. p < 0.01 flags an instrumentation issue.

### Novelty Effect
First 3 days of experiment excluded to remove the novelty effect bias (inflated engagement from users who notice a UI change).

### Segment Consistency
Results checked across device type and user type to confirm treatment effect is consistent (not driven by one subgroup).
