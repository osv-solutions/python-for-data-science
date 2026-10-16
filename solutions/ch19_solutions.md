# Solutions: Chapter 19, Statistics for Data Science

Worked solutions to the exercises at the end of Chapter 19 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch19_solutions.ipynb`](ch19_solutions.ipynb) or the script `ch19_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

The solutions use the chapter's apartment data with `per_sqft`, the penguins, and its `bootstrap_ci` function.

## Exercise 19.1

*For Gentoo penguins' body mass, compute the mean, median, standard deviation, IQR and skewness, and say whether the mean is a good summary.*

```python
mass = gentoo["body_mass_g"].dropna()
print(f"mean {mass.mean():.0f}, median {mass.median():.0f}, "
      f"sd {mass.std():.0f}, IQR {stats.iqr(mass):.0f}, "
      f"skew {stats.skew(mass):.2f}")
```

Output:

```text
mean 5076, median 5000, sd 504, IQR 800, skew 0.07
```

The mean and the median differ by 76 grams, little next to a standard deviation of about 500, and the skewness is close to zero, so the distribution is roughly symmetric and the mean is a good summary. The standard deviation of about 500 grams says that a typical Gentoo is within half a kilogram of the mean.

## Exercise 19.2

*Using the fitted normal distribution, what share of Gentoo penguins would you expect to have flippers longer than 225 mm? Compare with the actual share.*

```python
flipper = gentoo["flipper_length_mm"].dropna()
mu, sigma = stats.norm.fit(flipper)
expected = 1 - stats.norm.cdf(225, mu, sigma)
actual = (flipper > 225).mean()
print(f"expected {expected:.1%}, actual {actual:.1%}")
```

Output:

```text
expected 11.3%, actual 12.2%
```

`1 - cdf(225)` is the probability of a value above 225. The normal model expects about 11%, and the data has a similar share. The match isn't exact, because flipper lengths are recorded in whole millimeters and 225 itself is a common value: whether "longer than 225" includes 225 changes the actual share noticeably.

## Exercise 19.3

*A support desk receives an average of 10.5 tickets per day. Using the Poisson distribution, how unusual is a day with 18 or more tickets?*

```python
tickets = stats.poisson(10.5)
p = 1 - tickets.cdf(17)
print(f"P(18 or more) = {p:.3f}, about once every {1 / p:.0f} days")
```

Output:

```text
P(18 or more) = 0.022, about once every 46 days
```

The **Poisson** distribution counts events that happen independently at a constant average rate, such as tickets per day. `1 - cdf(17)` is the probability of 18 or more. Such a day happens about 2% of the time, roughly once in two months: unusual enough to look into, not so rare that it must signal a problem.

## Exercise 19.4

*Compute a 95% confidence interval for the coffee shop's mean order revenue with `stats.t.interval`, and a bootstrap interval for its median. Why do they differ so much?*

```python
orders = pd.read_parquet("data/shop_orders.parquet")
rev = (orders["quantity"] * orders["unit_price"]).dropna().astype(float)
low, high = stats.t.interval(0.95, len(rev) - 1, rev.mean(),
                             stats.sem(rev))
print(f"mean {rev.mean():.2f}, 95% CI {low:.2f} to {high:.2f}")
print(f"median {rev.median():.2f}, 95% CI",
      np.round(bootstrap_ci(rev), 2))
```

Output:

```text
mean 53.53, 95% CI 47.51 to 59.54
median 35.00, 95% CI [35.   41.25]
```

The mean and the median estimate different things. Order revenue is strongly right-skewed: most orders are $15 to $60, and the café's two wholesale orders are worth about $1,900 and $2,500. The median's interval runs from $35.00 to $41.25 because order values are a small set of bag prices times quantities, so the median can only take a few values. Those two orders pull the mean up and widen its interval; the median, which ignores them, is lower and much more precise. For "what does a typical order bring in?", the median is the right answer; for "total revenue per order, on average", the mean is.

## Exercise 19.5

*Repeat the coverage simulation with samples of 10 instead of 40. Do 95% of the intervals still contain the true mean?*

```python
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
```

Output:

```text
n = 10: 91.8% of intervals cover the mean
n = 40: 94.0% of intervals cover the mean
```

With samples of 10, the coverage drops to about 92%, against 94% with samples of 40. The t-interval assumes that the sample mean is normally distributed; for a skewed population, that is only approximately true, and the approximation gets worse as samples get smaller. Small samples from skewed data are where the bootstrap, or simply more data, earns its keep.

## Exercise 19.6

*Using the bootstrap, compute a 95% confidence interval for the difference between Harbor's and Central's median rent per square foot.*

```python
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
```

Output:

```text
difference 0.572, 95% CI 0.516 to 0.616
```

Each repetition resamples both districts independently, with their own sizes, and records the difference of the two medians. Harbor costs about 57 cents more per square foot, and the interval is far from zero, so the difference is not sampling noise.

## Exercise 19.7

*Write a function that returns a table of the mean, its 95% t-interval, the median and its bootstrap interval for every numeric column, and apply it to the apartment listings.*

```python
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
```

Output:

```text
                   mean  mean_lo  mean_hi   median   med_lo   med_hi
rent            1509.40  1477.97  1540.83  1365.00  1335.00  1410.00
sqft             924.75   909.67   939.83   892.00   874.98   914.00
per_sqft           1.65     1.63     1.67     1.52     1.50     1.54
days_on_market    24.75    23.84    25.66    19.00    19.00    20.00
```

`select_dtypes("number")` picks the numeric columns. With 1,800 listings, every interval is narrow; the gap between mean and median shows which columns are skewed, rent and days on the market most of all. A table like this is a compact first answer to "how precise are these numbers?".
