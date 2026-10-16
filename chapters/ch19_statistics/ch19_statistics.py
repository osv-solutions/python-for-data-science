"""Chapter 19: Statistics for Data Science

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch19_statistics.py

or open the notebook and run the cells in order.
"""

# %% 19.1 Samples and populations
import numpy as np
import pandas as pd
from scipy import stats

flats = pd.read_csv("data/apartments.csv")
flats.loc[flats["sqft"] > 4000, "sqft"] //= 10
flats["per_sqft"] = flats["rent"] / flats["sqft"]
harbor = flats.loc[flats["district"] == "Harbor", "per_sqft"].dropna()
print(len(harbor), "Harbor listings with a size")

# %% 19.2 Describing data: center, spread and shape
center = {"mean": harbor.mean(), "median": harbor.median(),
          "trimmed mean": stats.trim_mean(harbor, 0.1)}
spread = {"std": harbor.std(), "IQR": stats.iqr(harbor),
          "range": harbor.max() - harbor.min()}
for name, value in {**center, **spread}.items():
    print(f"{name:<13}{value:.3f}")
print("skew:", round(stats.skew(harbor), 2))

# %% 19.2 Describing data: center, spread and shape
z = (harbor - harbor.mean()) / harbor.std()
print(z.describe()[["mean", "std", "min", "max"]].round(2))
print((z.abs() > 2).mean().round(3), "beyond 2 standard deviations")

# %% 19.3 Distributions
import matplotlib.pyplot as plt

penguins = pd.read_csv("data/penguins.csv")
flipper = penguins.loc[penguins["species"] == "Gentoo",
                       "flipper_length_mm"].dropna()
mu, sigma = stats.norm.fit(flipper)
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.hist(flipper, bins=np.arange(200.5, 233, 2), density=True,
        color="#2a9bb0", edgecolor="white")
x = np.linspace(flipper.min() - 5, flipper.max() + 5, 200)
ax.plot(x, stats.norm.pdf(x, mu, sigma), color="#c0582b", lw=2)
ax.set_xlabel("Gentoo flipper length (mm)")
plt.show()
print(f"mean {mu:.1f} mm, sd {sigma:.1f} mm")

# %% 19.3 Distributions
purchases = stats.binom(n=1000, p=0.03)
print(f"expected: {purchases.mean():.0f}, sd: {purchases.std():.1f}")
print("P(25 or fewer):", round(purchases.cdf(25), 3))
print("middle 95%:", purchases.ppf([0.025, 0.975]))

# %% 19.4 Samples of samples: the sampling distribution
population = flats["per_sqft"].dropna().to_numpy()
rng = np.random.default_rng(19)
for n in [10, 40, 160]:
    means = [rng.choice(population, n).mean() for _ in range(5000)]
    print(f"n = {n:>3}: sample means spread with sd "
          f"{np.std(means):.3f}")
print(f"population sd {population.std():.3f}")

# %% 19.4 Samples of samples: the sampling distribution
means = np.array([rng.choice(population, 40).mean()
                  for _ in range(5000)])
fig, axes = plt.subplots(1, 2, figsize=(7, 2.6))
axes[0].hist(population, bins=40, color="#2a9bb0", edgecolor="white")
axes[0].set_title("Population: rent per sq ft", fontsize=9)
axes[1].hist(means, bins=40, color="#1d5c8c", edgecolor="white")
axes[1].set_title("5,000 means of samples of 40", fontsize=9)
plt.show()
print("skew:", round(stats.skew(population), 2), "->",
      round(stats.skew(means), 2))

# %% 19.5 Confidence intervals
n = len(harbor)
se = harbor.std() / np.sqrt(n)
low, high = stats.t.interval(0.95, df=n - 1, loc=harbor.mean(),
                             scale=se)
print(f"mean {harbor.mean():.3f}, standard error {se:.3f}")
print(f"95% confidence interval: {low:.3f} to {high:.3f}")

# %% 19.5 Confidence intervals
true_mean = population.mean()
hits = 0
for _ in range(2000):
    s = rng.choice(population, 40)
    lo, hi = stats.t.interval(0.95, 39, s.mean(), stats.sem(s))
    hits += lo <= true_mean <= hi
print(f"{hits / 2000:.1%} of intervals contain the true mean")

# %% 19.5 Confidence intervals
pets = flats["pets_allowed"]
p, n = pets.mean(), len(pets)
se = np.sqrt(p * (1 - p) / n)
print(f"{p:.1%} allow pets, 95% CI {p - 1.96 * se:.1%} to "
      f"{p + 1.96 * se:.1%}")

# %% 19.6 The bootstrap
def bootstrap_ci(values, stat=np.median, reps=5000, seed=1):
    rng = np.random.default_rng(seed)
    values = np.asarray(values)
    boots = [stat(rng.choice(values, len(values)))
             for _ in range(reps)]
    return np.percentile(boots, [2.5, 97.5])


low, high = bootstrap_ci(harbor)
print(f"median {harbor.median():.3f}, 95% CI {low:.3f} to {high:.3f}")

# %% 19.6 The bootstrap
res = stats.bootstrap((harbor.to_numpy(),), np.median,
                      confidence_level=0.95, n_resamples=5000,
                      random_state=1)
print(np.round(res.confidence_interval, 3))

# %% 19.7 Putting it together: rents with honest uncertainty
two = flats[flats["bedrooms"] == 2]
rows = []
for district, rents in two.groupby("district")["rent"]:
    low, high = bootstrap_ci(rents)
    rows.append({"district": district, "listings": len(rents),
                 "median": rents.median(), "low": low, "high": high})
table = pd.DataFrame(rows).sort_values("median")
print(table.round(0).to_string(index=False))

# %% 19.7 Putting it together: rents with honest uncertainty
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.errorbar(table["median"], table["district"],
            xerr=[table["median"] - table["low"],
                  table["high"] - table["median"]],
            fmt="o", color="#1d5c8c", capsize=4)
ax.set_xlabel("Median rent of a 2-bedroom ($ per month), 95% CI")
ax.set_title("Two bedrooms cost most in Harbor and Central")
plt.show()
