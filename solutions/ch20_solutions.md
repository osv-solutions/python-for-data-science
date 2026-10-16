# Solutions: Chapter 20, Hypothesis Testing and A/B Tests

Worked solutions to the exercises at the end of Chapter 20 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch20_solutions.ipynb`](ch20_solutions.ipynb) or the script `ch20_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ab = pd.read_csv("data/ab_checkout.csv")
new = ab.loc[ab["group"] == "new_checkout", "revenue"].to_numpy()
old = ab.loc[ab["group"] == "control", "revenue"].to_numpy()
```

</details>

The solutions use the chapter's A/B test data, with the revenue per visitor of each group as `new` and `old`.

## Exercise 20.1

*Run `stats.permutation_test` on the revenue per visitor of the two groups, and compare the p-value with the t-test's.*

```python
def diff_means(x, y):
    return np.mean(x) - np.mean(y)


res = stats.permutation_test((new, old), diff_means, n_resamples=5000,
                             random_state=1)
t = stats.ttest_ind(new, old, equal_var=False)
print(f"permutation p = {res.pvalue:.4f}, t-test p = {t.pvalue:.4f}")
```

Output:

```text
permutation p = 0.0136, t-test p = 0.0109
```

`permutation_test` takes the samples as a tuple and a function of them; by default it shuffles the observations between the samples, two-sided. The two p-values are close, both about 0.01: with 12,000 visitors per group, the t-test's normal approximation is reliable even for skewed revenue.

## Exercise 20.2

*With `stats.binomtest`, test whether a coin that came up heads 61 times in 100 tosses is fair.*

```python
result = stats.binomtest(61, n=100, p=0.5)
print(f"p = {result.pvalue:.3f}")
ci = result.proportion_ci(confidence_level=0.95)
print(f"95% CI {ci.low:.2f} to {ci.high:.2f}")
```

Output:

```text
p = 0.035
95% CI 0.51 to 0.71
```

The p-value is about 0.035: 61 heads would be rare for a fair coin, so at α = 0.05 we reject fairness. The confidence interval for the probability of heads runs from about 0.51 to 0.71; it just excludes 0.5. One hundred tosses are enough to suspect the coin, not to say how biased it is.

## Exercise 20.3

*Use a chi-square test to check whether the share of 1-kilogram bags differs between the coffee shop's states.*

```python
orders = pd.read_parquet("data/shop_orders.parquet").dropna(
    subset=["state"])
table = pd.crosstab(orders["state"], orders["bag_size"] == "1kg")
chi2, p, dof, _ = stats.chi2_contingency(table)
print((table[True] / table.sum(axis=1)).round(2).to_frame("1kg").T)
print(f"chi-square {chi2:.1f}, {dof} degrees of freedom, p = {p:.3f}")
```

Output:

```text
state    MA    MD    NJ    NY    OH    PA    VA
1kg    0.16  0.26  0.24  0.19  0.25  0.21  0.31
chi-square 8.8, 6 degrees of freedom, p = 0.188
```

The table counts 1-kilogram and other orders per state. The shares range from about 16% to 31%, but with 60 to 340 orders per state, such differences are well within chance: the p-value is far above 0.05. There is no evidence that customers in different states prefer different bag sizes.

## Exercise 20.4

*Compute the power of the shop's test for a true lift from 3.0% to 3.3% with 12,000 visitors per group. What does the result mean?*

```python
h = proportion_effectsize(0.033, 0.030)
power = NormalIndPower().power(effect_size=h, nobs1=12000, alpha=0.05)
print(f"power {power:.0%}")
```

Output:

```text
power 27%
```

The power is only about 27%: if the new page truly lifted conversion by 0.3 points, a test of this size would detect it only one time in four. A non-significant result from such a test would mean "too small a test to tell", not "no effect". That is why sample sizes are computed before a test, from the smallest effect worth finding.

## Exercise 20.5

*Compare the median rent per square foot of apartments with and without parking with a permutation test of the difference in medians.*

```python
flats = pd.read_csv("data/apartments.csv")
flats["per_sqft"] = flats["rent"] / flats["sqft"]
with_p = flats.loc[flats["parking"], "per_sqft"].dropna().to_numpy()
without = flats.loc[~flats["parking"], "per_sqft"].dropna().to_numpy()
res = stats.permutation_test(
    (with_p, without), lambda x, y: np.median(x) - np.median(y),
    n_resamples=5000, random_state=2)
print(f"difference {np.median(with_p) - np.median(without):.3f}, "
      f"p = {res.pvalue:.4f}")
```

Output:

```text
difference 0.041, p = 0.0260
```

A permutation test works for any statistic, here the difference in medians, for which there is no simple formula. Apartments with parking cost about 4 cents more per square foot in the median, and the difference is significant (p = 0.026). But the citywide comparison understates the value of parking, because of a confounder (Chapter 18): parking is rare in Central, the second most expensive district, so many expensive apartments are in the group without it. Within every district, the median difference is larger, about 8 to 14 cents. The test answers the question it was asked; whether that question is the right one is up to you.

## Exercise 20.6

*Repeat the peeking simulation with checks every 7 days instead of every day. How much does the false positive rate drop?*

```python
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
```

Output:

```text
daily: 22.5%, weekly: 8.4%, once: 5.0%
```

The function checks the accumulated data on the given days only; day 6 is the end of the first week, day 13 the end of the test. Two looks instead of fourteen bring the false positive rate down to about 8%, and a single analysis at the end gives the promised 5%. Every extra look adds risk.

## Exercise 20.7

*Simulate 1,000 A/B tests in which the new page truly converts at 3.6% against 3.0%, with 4,000 visitors per group, and count how often the test finds p < 0.05.*

```python
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
```

Output:

```text
simulated power 31%, statsmodels 32%
```

The simulated tests detect the real lift only about a third of the time, close to the power that statsmodels computes (the chi-square test's continuity correction makes it slightly more conservative). With 4,000 visitors per group, two of every three tests of a genuinely better page would come back "not significant", the clearest argument for computing the sample size before testing.
