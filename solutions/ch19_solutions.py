"""Solutions to the Chapter 19 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch19_solutions.py

The explanations are in ch19_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import numpy as np
import pandas as pd
from scipy import stats

flats = pd.read_csv("data/apartments.csv")
flats.loc[flats["sqft"] > 4000, "sqft"] //= 10
flats["per_sqft"] = flats["rent"] / flats["sqft"]
penguins = pd.read_csv("data/penguins.csv")
gentoo = penguins[penguins["species"] == "Gentoo"]


def bootstrap_ci(values, stat=np.median, reps=5000, seed=1):
    rng = np.random.default_rng(seed)
    values = np.asarray(values)
    boots = [stat(rng.choice(values, len(values)))
             for _ in range(reps)]
    return np.percentile(boots, [2.5, 97.5])

# %% Exercise 19.1
mass = gentoo["body_mass_g"].dropna()
print(f"mean {mass.mean():.0f}, median {mass.median():.0f}, "
      f"sd {mass.std():.0f}, IQR {stats.iqr(mass):.0f}, "
      f"skew {stats.skew(mass):.2f}")

# %% Exercise 19.2
flipper = gentoo["flipper_length_mm"].dropna()
mu, sigma = stats.norm.fit(flipper)
expected = 1 - stats.norm.cdf(225, mu, sigma)
actual = (flipper > 225).mean()
print(f"expected {expected:.1%}, actual {actual:.1%}")

# %% Exercise 19.3
tickets = stats.poisson(10.5)
p = 1 - tickets.cdf(17)
print(f"P(18 or more) = {p:.3f}, about once every {1 / p:.0f} days")

# %% Exercise 19.4
orders = pd.read_parquet("data/shop_orders.parquet")
rev = (orders["quantity"] * orders["unit_price"]).dropna().astype(float)
low, high = stats.t.interval(0.95, len(rev) - 1, rev.mean(),
                             stats.sem(rev))
print(f"mean {rev.mean():.2f}, 95% CI {low:.2f} to {high:.2f}")
print(f"median {rev.median():.2f}, 95% CI",
      np.round(bootstrap_ci(rev), 2))

# %% Exercise 19.5
population = flats["per_sqft"].dropna().to_numpy()
rng = np.random.default_rng(5)
true_mean = population.mean()
for n in [10, 40]:
    hits = 0
    for _ in range(2000):
        s = rng.choice(population, n)
        lo, hi = stats.t.interval(0.95, n - 1, s.mean(), stats.sem(s))
        hits += lo <= true_mean <= hi
    print(f"n = {n}: {hits / 2000:.1%} of intervals cover the mean")

# %% Exercise 19.6
harbor = flats.loc[flats["district"] == "Harbor", "per_sqft"].dropna()
central = flats.loc[flats["district"] == "Central",
                    "per_sqft"].dropna()
rng = np.random.default_rng(6)
diffs = [np.median(rng.choice(harbor, len(harbor)))
         - np.median(rng.choice(central, len(central)))
         for _ in range(5000)]
low, high = np.percentile(diffs, [2.5, 97.5])
print(f"difference {harbor.median() - central.median():.3f}, "
      f"95% CI {low:.3f} to {high:.3f}")

# %% Exercise 19.7
def summary_with_ci(df):
    rows = {}
    for col in df.select_dtypes("number"):
        x = df[col].dropna().to_numpy(dtype=float)
        lo, hi = stats.t.interval(0.95, len(x) - 1, x.mean(),
                                  stats.sem(x))
        b_lo, b_hi = bootstrap_ci(x, reps=1000)
        rows[col] = {"mean": x.mean(), "mean_lo": lo, "mean_hi": hi,
                     "median": np.median(x), "med_lo": b_lo,
                     "med_hi": b_hi}
    return pd.DataFrame(rows).T


cols = ["rent", "sqft", "per_sqft", "days_on_market"]
print(summary_with_ci(flats[cols]).round(2))
