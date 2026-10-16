# Solutions: Chapter 4, Loading Data from Files

Worked solutions to the exercises at the end of Chapter 4 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch04_solutions.ipynb`](ch04_solutions.ipynb) or the script `ch04_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(4)
n = 50 * 365 * 24
meters = pd.DataFrame({
    "meter": rng.integers(1, 51, size=n),
    "hour": rng.integers(0, 24, size=n),
    "kwh": rng.gamma(2.0, 0.6, size=n).round(3),
})
meters.to_csv("meters.csv", index=False)
```

</details>

## Exercise 4.1

*Load the transactions with dates parsed and print the first and last transaction of each month.*

```python
tx = pd.read_csv("data/transactions.csv", parse_dates=["date"])
month = tx["date"].dt.month
cols = ["date", "description", "amount"]
print(tx.groupby(month).head(1)[cols].to_string(index=False))
print(tx.groupby(month).tail(1)[cols].to_string(index=False))
```

Output:

```text
      date       description  amount
2026-01-01 ACME CORP PAYROLL  2450.0
2026-02-01 ACME CORP PAYROLL  2450.0
2026-03-01 ACME CORP PAYROLL  2450.0
2026-04-01 ACME CORP PAYROLL  2450.0
2026-05-01 ACME CORP PAYROLL  2450.0
2026-06-01 ACME CORP PAYROLL  2450.0
      date   description  amount
2026-01-31    TACO STAND   -8.80
2026-02-28 CITY PHARMACY  -44.01
2026-03-29  PIZZA PALACE  -32.11
2026-04-30    TACO STAND   -9.93
2026-05-31    NOODLE BAR  -33.26
2026-06-30  CITY TRANSIT   -2.75
```

The file is sorted by date, so `groupby(...).head(1)` keeps the first row of each month and `tail(1)` the last. Every month starts on the 1st with the paycheck, because the bank lists it first.

## Exercise 4.2

*Save the transactions over $100 to a CSV file, read it back and check the rows and the total.*

```python
big = tx[tx["amount"].abs() > 100]
big.to_csv("big.csv", index=False)
back = pd.read_csv("big.csv", parse_dates=["date"])
print(len(big), len(back))
print(round(big["amount"].sum(), 2), round(back["amount"].sum(), 2))
print(back.equals(big.reset_index(drop=True)))
```

Output:

```text
45 45
17620.41 17620.41
True
```

"More than $100" covers money in and out, so the filter uses the absolute value. The file round-trips exactly: same rows, same total, and `equals` confirms the tables are identical once `big`'s original row labels are reset to 0, 1, 2…, as the file has them.

## Exercise 4.3

*Read a tab-separated file with a two-line note and `"-"` for missing values.*

```python
text = ("Sensor export\nGenerated 2026-07-01\n"
        "station\ttemp_c\thumidity\n"
        "north\t21.5\t40\nsouth\t-\t38\neast\t23.1\t-\n")
with open("sensors.tsv", "w", encoding="utf-8") as f:
    f.write(text)
sensors = pd.read_csv("sensors.tsv", sep="\t", skiprows=2,
                      na_values=["-"])
print(sensors)
print(sensors.dtypes)
```

Output:

```text
  station  temp_c  humidity
0   north    21.5      40.0
1   south     NaN      38.0
2    east    23.1       NaN
station         str
temp_c      float64
humidity    float64
dtype: object
```

`sep="\t"` names the tab, `skiprows=2` skips the note, and `na_values=["-"]` turns the dashes into `NaN`, which keeps both measurement columns numeric. Without it, each column would contain a string and be read as text. Note that `-` alone is not confused with the minus sign of a negative number.

## Exercise 4.4

*Find the product with the most units sold in each category, and write one sheet per category.*

```python
orders = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                       header=2)
units = orders.groupby(["category", "product"])["units"].sum()
for category, product in units.groupby("category").idxmax():
    print(f"{category:<12}{product}")
with pd.ExcelWriter("by_category.xlsx") as writer:
    for category, part in orders.groupby("category"):
        part.to_excel(writer, sheet_name=category, index=False)
print(list(pd.read_excel("by_category.xlsx", sheet_name=None)))
```

Output:

```text
Accessories Laptop stand
Electronics Webcam
Furniture   Desk lamp
['Accessories', 'Electronics', 'Furniture']
```

`units` has a two-level index, (category, product). Grouping it again by the first level and taking `idxmax` returns the (category, product) label with the most units in each category: the laptop stand, the webcam and the desk lamp. Looping over `groupby` gives each category's name and its rows, which become one sheet each.

## Exercise 4.5

*Build one row per order from `orders.json`: ID, customer name, number of items and total.*

```python
import json

with open("data/orders.json", encoding="utf-8") as f:
    raw = json.load(f)
items = pd.json_normalize(raw, record_path="items",
                          meta=["order_id", ["customer", "name"]])
items["line_total"] = items["qty"] * items["price"]
per_order = items.groupby(["order_id", "customer.name"]).agg(
    items=("sku", "size"), total=("line_total", "sum"))
print(per_order.reset_index())
```

Output:

```text
  order_id customer.name  items  total
0    W-501      Asha Rao      2  32.50
1    W-502     Ben Ortiz      1  12.50
2    W-503       Chen Li      3  43.25
3    W-504      Dana Kim      1  39.00
```

First one row per item, as in the chapter, then `groupby` collapses the items back into one row per order, counting them and adding up their line totals. "Number of items" here means order lines; to count units instead, sum `qty`.

## Exercise 4.6

*Save the store orders as CSV and as Parquet, compare the sizes, and read two columns from the Parquet file.*

```python
orders.to_csv("orders.csv", index=False)
orders.to_parquet("orders.parquet", index=False)
for name in ["orders.csv", "orders.parquet"]:
    print(f"{name:<16}{Path(name).stat().st_size:>7,} bytes")
two = pd.read_parquet("orders.parquet", columns=["region", "units"])
print(two.shape, two.dtypes.astype(str).tolist())
```

Output:

```text
orders.csv       15,722 bytes
orders.parquet    7,717 bytes
(300, 2) ['str', 'int64']
```

The Parquet file is about half the size of the CSV file. With only 300 rows, Parquet's fixed overhead, the description of each column's type stored in the file, keeps the difference smaller than it is on big tables. `columns=` reads just the two columns asked for.

## Exercise 4.7

*Using `chunksize`, find each meter's total use and largest hourly reading, and check the result against a full load.*

```python
total = pd.Series(dtype=float)
largest = pd.Series(dtype=float)
for chunk in pd.read_csv("meters.csv", chunksize=100_000):
    by_meter = chunk.groupby("meter")["kwh"]
    total = total.add(by_meter.sum(), fill_value=0)
    largest = largest.combine(by_meter.max(), max, fill_value=0)
full = pd.read_csv("meters.csv").groupby("meter")["kwh"]
print((total.round(3) == full.sum().round(3)).all(),
      (largest == full.max()).all())
print(total.round(1).nlargest(3))
```

Output:

```text
True True
meter
43    10797.7
4     10755.1
26    10716.2
dtype: float64
```

Totals add across chunks. A maximum doesn't add, but the maximum of the chunks' maximums is the overall maximum, and `combine(other, max, fill_value=0)` applies Python's `max` to each pair of matching values. Both checks print `True`. The totals are compared after rounding, because adding the same numbers in a different order can change the last decimal places.
