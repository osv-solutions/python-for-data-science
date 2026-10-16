"""Solutions to the Chapter 20 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch20_solutions.py

The explanations are in ch20_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ab = pd.read_csv("data/ab_checkout.csv")
new = ab.loc[ab["group"] == "new_checkout", "revenue"].to_numpy()
old = ab.loc[ab["group"] == "control", "revenue"].to_numpy()

# %% Exercise 20.1
def diff_means(x, y):
    return np.mean(x) - np.mean(y)


res = stats.permutation_test((new, old), diff_means, n_resamples=5000,
                             random_state=1)
t = stats.ttest_ind(new, old, equal_var=False)
print(f"permutation p = {res.pvalue:.4f}, t-test p = {t.pvalue:.4f}")

# %% Exercise 20.2
result = stats.binomtest(61, n=100, p=0.5)
print(f"p = {result.pvalue:.3f}")
ci = result.proportion_ci(confidence_level=0.95)
print(f"95% CI {ci.low:.2f} to {ci.high:.2f}")

# %% Exercise 20.3
orders = pd.read_parquet("data/shop_orders.parquet").dropna(
    subset=["state"])
table = pd.crosstab(orders["state"], orders["bag_size"] == "1kg")
chi2, p, dof, _ = stats.chi2_contingency(table)
print((table[True] / table.sum(axis=1)).round(2).to_frame("1kg").T)
print(f"chi-square {chi2:.1f}, {dof} degrees of freedom, p = {p:.3f}")

# %% Exercise 20.4
h = proportion_effectsize(0.033, 0.030)
power = NormalIndPower().power(effect_size=h, nobs1=12000, alpha=0.05)
print(f"power {power:.0%}")

# %% Exercise 20.5
flats = pd.read_csv("data/apartments.csv")
flats["per_sqft"] = flats["rent"] / flats["sqft"]
with_p = flats.loc[flats["parking"], "per_sqft"].dropna().to_numpy()
without = flats.loc[~flats["parking"], "per_sqft"].dropna().to_numpy()
res = stats.permutation_test(
    (with_p, without), lambda x, y: np.median(x) - np.median(y),
    n_resamples=5000, random_state=2)
print(f"difference {np.median(with_p) - np.median(without):.3f}, "
      f"p = {res.pvalue:.4f}")

# %% Exercise 20.6
def peeking(check_days, tests=1000, seed=3):
    rng = np.random.default_rng(seed)
    alarms = 0
    for _ in range(tests):
        a = rng.random((14, 850)) < 0.03
        b = rng.random((14, 850)) < 0.03
        ca = a.cumsum(axis=0).sum(axis=1)[check_days]
        cb = b.cumsum(axis=0).sum(axis=1)[check_days]
        n = 850 * (np.array(check_days) + 1)
        pooled = (ca + cb) / (2 * n)
        z = (cb - ca) / n / np.sqrt(pooled * (1 - pooled) * 2 / n)
        alarms += (np.abs(z) > 1.96).any()
    return alarms / tests


print(f"daily: {peeking(list(range(14))):.1%}, weekly: "
      f"{peeking([6, 13]):.1%}, once: {peeking([13]):.1%}")

# %% Exercise 20.7
rng = np.random.default_rng(4)
hits = 0
for _ in range(1000):
    a = (rng.random(4000) < 0.030).sum()
    b = (rng.random(4000) < 0.036).sum()
    table = [[a, 4000 - a], [b, 4000 - b]]
    hits += stats.chi2_contingency(table)[1] < 0.05
h = proportion_effectsize(0.036, 0.030)
print(f"simulated power {hits / 1000:.0%}, statsmodels "
      f"{NormalIndPower().power(h, nobs1=4000, alpha=0.05):.0%}")
