# Solutions: Chapter 13, Combining Data

Worked solutions to the exercises at the end of Chapter 13 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch13_solutions.ipynb`](ch13_solutions.ipynb) or the script `ch13_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import sqlite3
from pathlib import Path

import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
customers = pd.read_csv("data/shop_customers.csv",
                        parse_dates=["joined"])
tickets = pd.read_csv("data/support_tickets.csv")
pattern = r"(?i)#?\bhc[-\s]?(\d{5})"
tickets["order_id"] = "HC-" + tickets["subject"].str.extract(pattern)[0]
for month, part in orders.groupby(orders["order_date"]
                                  .dt.to_period("M")):
    part.to_csv(f"orders_{month}.csv", index=False)
```

</details>

The solutions use the chapter's `orders`, `customers` and `tickets` tables, with the tickets' `order_id` column, and the monthly order files.

## Exercise 13.1

*List the 26 customers who never placed an order, with their tier and join date, newest first.*

```python
both = customers.merge(orders[["customer_id"]].drop_duplicates(),
                       on="customer_id", how="left", indicator=True)
never = both[both["_merge"] == "left_only"]
print(len(never))
print(never.sort_values("joined", ascending=False)
      [["customer_id", "tier", "joined"]].head())
```

Output:

```text
26
    customer_id      tier     joined
323       C0327  standard 2026-05-18
321       C0325  standard 2026-03-23
162       C0164      gold 2026-03-05
265       C0268  standard 2026-02-14
32        C0033      gold 2025-11-22
```

A left join from the customers, with `indicator=True`, marks the customers without a match as `left_only`. Merging with the *distinct* customer IDs of the orders, rather than all orders, keeps one row per customer. An equivalent shortcut is `customers[~customers["customer_id"].isin(orders["customer_id"])]`; the merge version generalizes to keys of several columns.

## Exercise 13.2

*Count the orders per tier, with the 14 orders of unknown customers shown as "unknown".*

```python
full = orders.merge(customers, on="customer_id", how="left",
                    validate="many_to_one")
full["tier"] = full["tier"].fillna("unknown")
print(full["tier"].value_counts())
```

Output:

```text
tier
standard    648
silver      259
gold        179
unknown      14
Name: count, dtype: int64
```

The left join keeps all 1,100 orders, and `fillna` labels the missing tier. Filling *after* the merge is the point: the gap means "not in the customer list", which only the merge can tell you.

## Exercise 13.3

*For each customer, compute the number of orders and the date of their first order, and attach them to the customer table, keeping every customer.*

```python
stats = orders.groupby("customer_id").agg(
    orders=("order_id", "count"), first_order=("order_date", "min"))
profile = customers.merge(stats, left_on="customer_id",
                          right_index=True, how="left",
                          validate="one_to_one")
profile["orders"] = profile["orders"].fillna(0).astype(int)
print(len(profile) == len(customers))
print(profile.sort_values("orders", ascending=False).head(3))
```

Output:

```text
True
    customer_id       name     joined      tier  orders first_order
99        C0100  Gus Walsh 2025-10-13      gold      10  2026-01-02
295       C0298  Jo Mensah 2024-05-23  standard       8  2026-01-27
27        C0028   Hana Kim 2024-05-19      gold       8  2026-01-01
```

The summary has one row per customer, indexed by `customer_id`, so the join is one-to-one, and `right_index=True` uses that index as the right key. Customers without orders get a missing count, which `fillna(0)` makes a true zero; their `first_order` stays missing, which is correct.

## Exercise 13.4

*Find the support tickets whose customers mention an order that was cancelled. How many are there, and which topics do they have?*

```python
linked = tickets.merge(orders[["order_id", "status"]], on="order_id",
                       how="inner", validate="many_to_one")
cancelled = linked[linked["status"] == "cancelled"]
print(len(cancelled), "tickets about cancelled orders")
template = (cancelled["subject"].str.strip().str.lower()
            .str.replace(r"#?hc[-\s]?\d{5}", "…", regex=True))
print(template.value_counts())
```

Output:

```text
9 tickets about cancelled orders
subject
change address on … please                          3
refund request - …                                  2
order … arrived damaged                             2
bag of sumatra mandheling tastes stale (order …)    1
bag of espresso roast tastes stale (order …)        1
Name: count, dtype: int64
```

An inner join is right here, because only tickets with a known order can be about a cancelled one. Lower-casing the subjects and replacing the order numbers with `…` turns them into templates, so `value_counts` groups them by topic. Nine tickets concern cancelled orders: address changes, refunds, damage and stale coffee. An agent who sees the order's status next to the ticket can answer most of them at once, starting with "that order was cancelled".

## Exercise 13.5

*Read the monthly order files back with `concat`, but rename `quantity` to `qty` in one of them first. Show what goes wrong, and write a check that compares the columns of all files before stacking.*

```python
files = sorted(Path(".").glob("orders_2026-*.csv"))
parts = [pd.read_csv(f) for f in files]
parts[2] = parts[2].rename(columns={"quantity": "qty"})
broken = pd.concat(parts, ignore_index=True)
print(broken[["quantity", "qty"]].isna().sum())


def check_columns(frames, names):
    expected = list(frames[0].columns)
    for frame, name in zip(frames, names):
        if list(frame.columns) != expected:
            diff = set(frame.columns) ^ set(expected)
            raise ValueError(f"{name}: columns differ: {sorted(diff)}")


try:
    check_columns(parts, [f.name for f in files])
except ValueError as err:
    print(err)
```

Output:

```text
quantity    187
qty         910
dtype: int64
orders_2026-03.csv: columns differ: ['qty', 'quantity']
```

After the rename, `concat` produces both a `quantity` and a `qty` column, each missing wherever the other is filled, and nothing warns you. The check compares every file's columns with the first file's; `^` between two sets gives the names that are in one but not both, which names the problem exactly.

## Exercise 13.6

*Using Chinook, find the revenue per customer country and genre, and the top genre in each country.*

```python
con = sqlite3.connect("data/chinook.sqlite")
q = lambda sql: pd.read_sql_query(sql, con)
sales = (q("SELECT InvoiceId, TrackId, UnitPrice, Quantity "
           "FROM InvoiceLine")
         .merge(q("SELECT InvoiceId, CustomerId FROM Invoice"),
                on="InvoiceId", validate="many_to_one")
         .merge(q("SELECT CustomerId, Country FROM Customer"),
                on="CustomerId", validate="many_to_one")
         .merge(q("SELECT TrackId, GenreId FROM Track"),
                on="TrackId", validate="many_to_one")
         .merge(q("SELECT GenreId, Name AS genre FROM Genre"),
                on="GenreId", validate="many_to_one"))
sales["revenue"] = sales["UnitPrice"] * sales["Quantity"]
by = sales.groupby(["Country", "genre"])["revenue"].sum()
top = by.sort_values(ascending=False).groupby(level="Country").head(1)
print(top.sort_values(ascending=False).head(5))
```

Output:

```text
Country  genre
USA      Rock     155.43
Canada   Rock     105.93
Brazil   Rock      80.19
France   Rock      64.35
Germany  Rock      61.38
Name: revenue, dtype: float64
```

Each invoice line gets its invoice's customer, the customer's country, and the track's genre, with every join validated as many-to-one. After summing by country and genre, sorting by revenue and taking the first row of each country's group gives its top genre. Rock leads in the largest markets, the USA, Canada and Brazil among them.

## Exercise 13.7

*Write `safe_merge(left, right, **kwargs)` that merges with `indicator=True`, prints how many rows were matched, left only and right only, raises an error if the left table's row count changed in a left join, and returns the result without the `_merge` column.*

```python
def safe_merge(left, right, **kwargs):
    out = left.merge(right, indicator=True, **kwargs)
    counts = out["_merge"].value_counts()
    print(", ".join(f"{k}: {v}" for k, v in counts.items()))
    if kwargs.get("how") == "left" and len(out) != len(left):
        raise ValueError(f"left join changed rows: {len(left)} -> "
                         f"{len(out)}")
    return out.drop(columns="_merge")


ok = safe_merge(orders, customers, on="customer_id", how="left")
dup = pd.concat([customers, customers.iloc[[5]]])
try:
    safe_merge(orders, dup, on="customer_id", how="left")
except ValueError as err:
    print("ValueError:", err)
```

Output:

```text
both: 1086, left_only: 14, right_only: 0
both: 1088, left_only: 14, right_only: 0
ValueError: left join changed rows: 1100 -> 1102
```

The function passes its keyword arguments straight to `merge`, adds the indicator, and reports the counts in one line. A left join must keep the left table's row count; if a duplicated key on the right adds rows, the function stops, as it does with the duplicated customer.
