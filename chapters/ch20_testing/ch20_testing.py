"""Chapter 20: Hypothesis Testing and A/B Tests

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch20_testing.py

or open the notebook and run the cells in order.
"""

# %% 20.1 The question
import numpy as np
import pandas as pd
from scipy import stats

ab = pd.read_csv("data/ab_checkout.csv")
summary = ab.groupby("group").agg(visitors=("visitor_id", "count"),
                                  orders=("converted", "sum"),
                                  rate=("converted", "mean"))
print(summary.round(4))
diff = summary.loc["new_checkout", "rate"] - summary.loc["control",
                                                          "rate"]
print(f"difference: {diff:.4f} ({diff * 100:.2f} percentage points)")

# %% 20.2 A test by simulation
rng = np.random.default_rng(20)
converted = ab["converted"].to_numpy()
is_new = (ab["group"] == "new_checkout").to_numpy()
shuffled = []
for _ in range(5000):
    labels = rng.permutation(is_new)
    shuffled.append(converted[labels].mean()
                    - converted[~labels].mean())
shuffled = np.array(shuffled)
print("differences by chance: sd", shuffled.std().round(4))
p = (np.abs(shuffled) >= abs(diff)).mean()
print(f"share at least as extreme as {diff:.4f}: {p:.4f}")

# %% 20.4 Standard tests in SciPy
table = pd.crosstab(ab["group"], ab["converted"])
print(table)
chi2, p_chi, dof, expected = stats.chi2_contingency(table)
print(f"chi-square {chi2:.2f}, p = {p_chi:.4f}")

# %% 20.4 Standard tests in SciPy
new = ab.loc[ab["group"] == "new_checkout", "revenue"]
old = ab.loc[ab["group"] == "control", "revenue"]
t = stats.ttest_ind(new, old, equal_var=False)
print(f"revenue per visitor: ${new.mean():.3f} vs ${old.mean():.3f}")
print(f"t = {t.statistic:.2f}, p = {t.pvalue:.4f}")

# %% 20.5 Effect sizes and confidence intervals
n1, n0 = summary.loc["new_checkout", "visitors"], summary.loc[
    "control", "visitors"]
p1, p0 = summary.loc["new_checkout", "rate"], summary.loc["control",
                                                          "rate"]
se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
low, high = diff - 1.96 * se, diff + 1.96 * se
print(f"lift {diff * 100:.2f} points, 95% CI {low * 100:.2f} to "
      f"{high * 100:.2f}")
print(f"relative lift {p1 / p0 - 1:.0%}, between "
      f"{low / p0:.0%} and {high / p0:.0%}")

# %% 20.6 Designing an A/B test: power and sample size
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

for target in [0.036, 0.034, 0.033]:
    h = proportion_effectsize(target, 0.030)
    n = NormalIndPower().solve_power(effect_size=h, alpha=0.05,
                                     power=0.8)
    print(f"3.0% -> {target:.1%}: {n:,.0f} visitors per group")

# %% 20.7 Traps: peeking and multiple comparisons
false_alarms = 0
for _ in range(1000):
    a = rng.random((14, 850)) < 0.03          # 14 days of visitors
    b = rng.random((14, 850)) < 0.03
    ca, cb = a.cumsum(axis=0).sum(axis=1), b.cumsum(axis=0).sum(
        axis=1)
    n = 850 * np.arange(1, 15)
    pooled = (ca + cb) / (2 * n)
    z = (cb - ca) / n / np.sqrt(pooled * (1 - pooled) * 2 / n)
    false_alarms += (np.abs(z) > 1.96).any()
print(f"{false_alarms / 1000:.0%} of A/A tests looked significant "
      "on some day")

# %% 20.7 Traps: peeking and multiple comparisons
by_device = ab.groupby(["device", "group"])["converted"].agg(
    ["sum", "count"]).unstack("group")
for device, row in by_device.iterrows():
    counts = [[row[("sum", g)], row[("count", g)] - row[("sum", g)]]
              for g in ["control", "new_checkout"]]
    p_dev = stats.chi2_contingency(counts)[1]
    rates = row["sum"] / row["count"]
    print(f"{device:<8} {rates['control']:.2%} -> "
          f"{rates['new_checkout']:.2%}  p = {p_dev:.3f}")

# %% 20.8 Putting it together: the checkout decision
def boot_diff(a, b, reps=4000, seed=2):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a), np.asarray(b)
    diffs = [rng.choice(a, len(a)).mean()
             - rng.choice(b, len(b)).mean() for _ in range(reps)]
    return np.percentile(diffs, [2.5, 97.5])


low_r, high_r = boot_diff(new, old)
print(f"revenue per visitor: +${new.mean() - old.mean():.3f}, "
      f"95% CI ${low_r:.3f} to ${high_r:.3f}")

# %% 20.8 Putting it together: the checkout decision
buyers = ab[ab["converted"] == 1]
aov = buyers.groupby("group")["revenue"].agg(["mean", "count"])
t_aov = stats.ttest_ind(buyers.loc[buyers["group"] == "new_checkout",
                                   "revenue"],
                        buyers.loc[buyers["group"] == "control",
                                   "revenue"], equal_var=False)
print(aov.round(2))
print(f"p = {t_aov.pvalue:.2f}")
