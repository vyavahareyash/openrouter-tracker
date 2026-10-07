# Calculations & Metrics Specifications

This document details the mathematical rules and formatting algorithms used to compute OpenRouter credit usage, balance, and burn indicators.

---

## 1. Credit Usage Percentage

When an OpenRouter key has an explicit non-null limit defined:

$$\text{Usage Ratio} = \frac{\text{Usage}}{\text{Limit}}$$

$$\text{Burn Percentage} = \min(1.0, \max(0.0, \text{Usage Ratio})) \times 100\%$$

- **Gauge Invariant**: Clamped between $0\%$ and $100\%$ to prevent visual overflow in UI bars.
- **Null Limit Handling**: If `limit == nil` or `limit <= 0`, usage percentage is treated as indeterminate (progress bar omitted or filled with neutral accent).

---

## 2. Low Balance Warning Thresholds

The application flags keys when available balance or limits cross critical thresholds:

- **Critical Depletion**: $\text{Remaining Balance} \le \$2.00$ or $\text{Burn Percentage} \ge 95\%$
- **Warning State**: $\text{Remaining Balance} \le \$5.00$ or $\text{Burn Percentage} \ge 85\%$
- **Healthy State**: $\text{Remaining Balance} > \$5.00$ and $\text{Burn Percentage} < 85\%$

---

## 3. Rate-Limit Headroom

From `/api/v1/auth/key`, OpenRouter returns `rate_limit`:

$$\text{Requests Per Second} = \frac{\text{Requests Per Interval}}{\text{Interval Seconds}}$$

Displayed cleanly as:
- Requests per second (e.g. `10 req/s`)
- Requests per minute (e.g. `600 req/min`)
