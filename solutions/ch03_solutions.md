# Solutions: Chapter 3, pandas Essentials

Worked solutions to the exercises at the end of Chapter 3 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch03_solutions.ipynb`](ch03_solutions.ipynb) or the script `ch03_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import pandas as pd

penguins = pd.read_csv("data/penguins.csv")
stores = pd.DataFrame({
    "city": ["Pittsburgh", "Erie", "Harrisburg", "Scranton",
             "Allentown", "Lancaster"],
    "region": ["West", "West", "Central", "East", "East", "Central"],
    "sq_ft": [12000, 7500, 9800, 6400, 11200, 8300],
    "sales_k": [3150, 1480, 2210, 1395, 2870, 1920],
    "opened": [2011, 2016, 2013, 2019, 2012, 2017],
})
```

</details>

## Exercise 3.1

*Create a Series of a week's daily steps, indexed by day name, and print the average, the best day and the days above 8,000 steps.*

```python
steps = pd.Series([6200, 9100, 7400, 10350, 5800, 12900, 8300],
                  index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
                         "Sun"])
print(round(steps.mean()))
print("best day:", steps.idxmax())
print(steps[steps > 8000])
```

Output:

```text
8579
best day: Sat
Tue     9100
Thu    10350
Sat    12900
Sun     8300
dtype: int64
```

`idxmax` returns the *label* of the largest value, so the answer is a day name rather than a position. The mask keeps four days, with their labels.

## Exercise 3.2

*Print the bill length and depth of the rows labeled 100 to 105 with `loc`, then the same rows with `iloc`.*

```python
cols = ["bill_length_mm", "bill_depth_mm"]
print(penguins.loc[100:105, cols])
print(penguins.iloc[100:106, [2, 3]].equals(penguins.loc[100:105,
                                                          cols]))
```

Output:

```text
     bill_length_mm  bill_depth_mm
100            35.0           17.9
101            41.0           20.0
102            37.7           16.0
103            37.8           20.0
104            37.9           18.6
105            39.7           18.9
True
```

With `loc`, the slice `100:105` includes label 105. With `iloc`, the end is excluded, so the same six rows need `100:106`, and the two columns are given by position, 2 and 3. Because the index is 0, 1, 2…, labels and positions coincide here, and `equals` confirms that both selections are identical.

## Exercise 3.3

*List the penguins from Dream island with a flipper length of at least 200 millimeters.*

```python
long_dream = penguins[(penguins["island"] == "Dream")
                      & (penguins["flipper_length_mm"] >= 200)]
print(len(long_dream))
print(long_dream["species"].value_counts())
```

Output:

```text
25
species
Chinstrap    20
Adelie        5
Name: count, dtype: int64
```

Two conditions combined with `&`, each in parentheses. There are 25 such birds. Gentoo penguins don't live on Dream, so all of them are Chinstraps (20) and Adelies (5).

## Exercise 3.4

*Add a `bill_ratio` column and show the five penguins with the highest ratio.*

```python
penguins["bill_ratio"] = (penguins["bill_length_mm"]
                          / penguins["bill_depth_mm"]).round(2)
print(penguins.nlargest(5, "bill_ratio")[["species", "bill_ratio"]])
```

Output:

```text
    species  bill_ratio
239  Gentoo        3.61
172  Gentoo        3.51
185  Gentoo        3.51
152  Gentoo        3.49
215  Gentoo        3.46
```

A long, thin bill gives a high ratio. All five are Gentoos, whose bills are long and shallow; the ratio separates them from the other two species better than either measurement alone.

## Exercise 3.5

*Add a `size` column: large from 10,000 square feet, medium from 8,000, small otherwise.*

```python
stores["size"] = "small"
stores.loc[stores["sq_ft"] >= 8000, "size"] = "medium"
stores.loc[stores["sq_ft"] >= 10000, "size"] = "large"
print(stores[["city", "sq_ft", "size"]])
print(stores["size"].value_counts())
```

Output:

```text
         city  sq_ft    size
0  Pittsburgh  12000   large
1        Erie   7500   small
2  Harrisburg   9800  medium
3    Scranton   6400   small
4   Allentown  11200   large
5   Lancaster   8300  medium
size
large     2
small     2
medium    2
Name: count, dtype: int64
```

The order of the assignments matters: each later, stricter condition overwrites the earlier label for the stores it matches. Two stores are large, two medium and two small.

## Exercise 3.6

*In one method chain, find the three heaviest female penguins, with their mass in pounds.*

```python
heavy_females = (
    penguins
    .dropna()
    .query("sex == 'female'")
    .assign(mass_lb=lambda d: (d["body_mass_g"] / 453.6).round(1))
    .nlargest(3, "mass_lb")
    .loc[:, ["species", "island", "mass_lb"]]
)
print(heavy_females)
```

Output:

```text
    species  island  mass_lb
225  Gentoo  Biscoe     11.5
274  Gentoo  Biscoe     11.5
186  Gentoo  Biscoe     11.4
```

`dropna()` with no arguments drops every row that has any missing value. The three heaviest females are all Gentoos from Biscoe, at around 11 pounds.

## Exercise 3.7

*Compute a price change with index alignment, then with `sub` and `fill_value=0`.*

```python
september = pd.Series({"coffee": 8.99, "tea": 4.50, "milk": 3.29})
october = pd.Series({"milk": 3.49, "coffee": 9.49, "bread": 2.99})
print(october - september)
print(october.sub(september, fill_value=0))
```

Output:

```text
bread     NaN
coffee    0.5
milk      0.2
tea       NaN
dtype: float64
bread     2.99
coffee    0.50
milk      0.20
tea      -4.50
dtype: float64
```

The products are in different orders, but pandas matches them by label: coffee went up 50 cents and milk 20 cents. Bread (only in October) and tea (only in September) give `NaN`, which is honest: there is no change to compute. `fill_value=0` treats the missing price as 0, so bread shows a "change" of 2.99 and tea of -4.50. That makes sense for quantities, such as units sold, where "not listed" really means zero, but not for prices, where a missing price is unknown, not free.
