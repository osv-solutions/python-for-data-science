# Solutions: Chapter 11, Cleaning Messy Data

Worked solutions to the exercises at the end of Chapter 11 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch11_solutions.ipynb`](ch11_solutions.ipynb) or the script `ch11_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import pandas as pd

names = {"PENNSYLVANIA": "PA", "PENN": "PA", "NEW YORK": "NY",
         "NEW JERSEY": "NJ", "OHIO": "OH", "MARYLAND": "MD",
         "VIRGINIA": "VA", "MASS": "MA"}
STATUSES = ["delivered", "shipped", "processing", "cancelled"]


def check_orders(df):
    checks = {
        "order_id unique": df["order_id"].is_unique,
        "status known": df["status"].isin(STATUSES).all(),
        "state is a code": df["state"].dropna().str.fullmatch(
            "[A-Z]{2}").all(),
        "price positive": (df["unit_price"].dropna() > 0).all(),
        "rating 1 to 5": df["rating"].dropna().between(1, 5).all(),
        "shipping >= 0": (df["shipping_days"].dropna() >= 0).all(),
    }
    return [name for name, ok in checks.items() if not ok]


def fix_types(df):
    price = df["unit_price"].str.replace(r"[$,]", "", regex=True)
    return df.assign(
        order_date=pd.to_datetime(df["order_date"], errors="coerce"),
        unit_price=pd.to_numeric(price),
        quantity=df["quantity"].astype("Int64"),
        shipping_days=df["shipping_days"].astype("Int64"),
        rating=df["rating"].astype("Int64"),
        grams=df["bag_size"].map({"250g": 250, "500g": 500, "1kg": 1000}),
    )


def fix_labels(df):
    state = (df["state"].str.strip().str.upper()
             .str.replace(".", "", regex=False).replace(names))
    return df.assign(status=df["status"].str.strip().str.lower(),
                     state=state)


def drop_repeats(df):
    return (df.drop_duplicates()
              .drop_duplicates(subset="order_id", keep="last"))


def fix_outliers(df):
    df = df.copy()
    typical = (df.groupby(["product", "bag_size"])["unit_price"]
               .transform("median"))
    wrong = df["unit_price"] > 3 * typical
    df.loc[wrong, "unit_price"] = typical[wrong]
    df.loc[df["shipping_days"] < 0, "shipping_days"] = pd.NA
    df.loc[~df["rating"].between(1, 5), "rating"] = pd.NA
    df.loc[df["quantity"] > 100, "quantity"] = pd.NA
    return df


raw = pd.read_csv("data/shop_orders_raw.csv",
                  na_values={"unit_price": ["-"], "rating": [0]})
clean = (raw.pipe(fix_types).pipe(fix_labels).pipe(drop_repeats)
         .pipe(fix_outliers))
```

</details>

The solutions start from the chapter's cleaning functions and the `clean` table, which are set up as in the chapter.

## Exercise 11.1

*Load `shop_orders_raw.csv` and print, for each column, the number of distinct values and the number of missing values, in one table.*

```python
raw0 = pd.read_csv("data/shop_orders_raw.csv")
profile = pd.DataFrame({"distinct": raw0.nunique(),
                        "missing": raw0.isna().sum(),
                        "dtype": raw0.dtypes.astype(str)})
print(profile)
```

Output:

```text
               distinct  missing    dtype
order_id           1100        0      str
order_date          182        7      str
customer_id         304        0      str
state                21       11      str
product               6        0      str
bag_size              3        0      str
quantity              7        5  float64
unit_price           25        4      str
shipping_days         7       66  float64
status                8        0      str
rating                7      520  float64
```

`nunique` counts the distinct non-missing values of every column, and `isna().sum()` the gaps; both return a Series indexed by column name, so they line up in one DataFrame. The profile already hints at most of the chapter's problems: 1,100 distinct order IDs in 1,118 rows means duplicates, 8 statuses and 21 states are more than the real ones, and three numeric columns are floats.

## Exercise 11.2

*Count the orders per cleaned status, and the share of delivered orders that have a rating.*

```python
print(clean["status"].value_counts())
delivered = clean[clean["status"] == "delivered"]
print(f"{delivered['rating'].notna().mean():.1%} rated")
```

Output:

```text
status
delivered     1041
cancelled       31
processing      16
shipped         12
Name: count, dtype: int64
56.4% rated
```

After cleaning, 1,041 orders are delivered. `notna().mean()` is the share of `True` values, the orders with a rating: a little over half of the delivered orders have been rated.

## Exercise 11.3

*The seven orders with no date can't be placed in time. Drop them from `clean`, and compare the number of orders per month before and after.*

```python
dated = clean.dropna(subset=["order_date"])
print(len(clean), "->", len(dated))
per_month = dated["order_date"].dt.to_period("M").value_counts()
print(per_month.sort_index())
```

Output:

```text
1100 -> 1091
order_date
2026-01    176
2026-02    175
2026-03    183
2026-04    200
2026-05    186
2026-06    171
Freq: M, Name: count, dtype: int64
```

`dropna(subset=["order_date"])` drops 9 rows, not 7: the two impossible dates, February 30 and April 31, became missing in `fix_types` too. The monthly counts are the same before and after dropping, because orders without a date never belonged to a month; dropping them only matters for totals over the whole table.

## Exercise 11.4

*Fill the missing states in `clean` with the state the same customer used on another order, where there is one. How many states remain missing?*

```python
known = clean.groupby("customer_id")["state"].transform("first")
filled = clean["state"].fillna(known)
print(clean["state"].isna().sum(), "->", filled.isna().sum())
```

Output:

```text
11 -> 0
```

`groupby(...).transform("first")` returns, on every row, the first non-missing state of that row's customer. `fillna` uses it only where the state is missing. All 11 gaps can be filled, because every customer with a missing state also placed another order with the state written down. In a real project you would also add a flag column, as in the chapter.

## Exercise 11.5

*Add two checks to `check_orders`: dates between January 1 and June 30, 2026, and quantities from 1 to 100. Show that `clean` passes them and the raw table doesn't.*

```python
def check_more(df):
    problems = check_orders(df)
    dates = pd.to_datetime(df["order_date"], errors="coerce").dropna()
    if not dates.between("2026-01-01", "2026-06-30").all():
        problems.append("date in range")
    qty = pd.to_numeric(df["quantity"], errors="coerce").dropna()
    if not qty.between(1, 100).all():
        problems.append("quantity 1 to 100")
    return problems


print("clean:", check_more(clean))
typed = raw.pipe(fix_types).pipe(drop_repeats)
print("raw:", check_more(typed))
```

Output:

```text
clean: []
raw: ['status known', 'state is a code', 'rating 1 to 5', 'shipping >= 0', 'quantity 1 to 100']
```

The new function reuses `check_orders` and adds the two rules. Converting with `errors="coerce"` inside the checks lets them run on any version of the table. The clean table passes everything; the typed raw table fails five rules, among them the 999-bag order, which breaks the new quantity rule.

## Exercise 11.6

*Apply the IQR rule to `unit_price` for each bag size separately. Which prices are flagged, and are any of them errors?*

```python
def iqr_flags(s):
    q1, q3 = s.quantile([0.25, 0.75])
    return (s < q1 - 1.5 * (q3 - q1)) | (s > q3 + 1.5 * (q3 - q1))


typed = raw.pipe(fix_types).pipe(fix_labels).pipe(drop_repeats)
flags = typed.groupby("bag_size")["unit_price"].transform(iqr_flags)
print(typed.loc[flags, ["order_id", "product", "bag_size",
                        "unit_price"]])
```

Output:

```text
   order_id      product bag_size  unit_price
7  HC-10008  House Blend     250g      1250.0
9  HC-10010  House Blend     250g      1250.0
```

`transform` with a function that returns a Boolean Series of the same length gives each row its flag, computed within its bag size. Only the two $1,250 House Blend prices are flagged, and both are errors. Within one bag size, the six coffees' list prices are close together, so no real price is far enough out to be flagged; across all sizes, the 1-kilogram prices would look high next to the small bags.

## Exercise 11.7

*Write `cleaning_report(raw, clean)` that prints, for each column, how many values changed, how many became missing and how many missing values were filled.*

```python
def cleaning_report(before, after, key="order_id"):
    before = before.drop_duplicates(subset=key, keep="last")
    before = before.set_index(key)
    after = after.set_index(key)
    rows = {}
    for col in after.columns.intersection(before.columns):
        a = before[col].astype(str).where(before[col].notna())
        b = after[col].astype(str).where(after[col].notna())
        rows[col] = {"changed": (a.notna() & b.notna() & (a != b)).sum(),
                     "now missing": (a.notna() & b.isna()).sum(),
                     "filled": (a.isna() & b.notna()).sum()}
    print(pd.DataFrame(rows).T)


cleaning_report(pd.read_csv("data/shop_orders_raw.csv"), clean)
```

Output:

```text
               changed  now missing  filled
order_date           0            2       0
customer_id          0            0       0
state              530            0       0
product              0            0       0
bag_size             0            0       0
quantity          1094            1       0
unit_price        1087            9       0
shipping_days     1038            3       0
status              42            0       0
rating             587            7       0
```

To compare row by row, both tables are indexed by the key, keeping the last version of each order as the cleaning did. Comparing as text, with missing values kept missing by `where`, treats `2.0` and `2` as different, so `quantity` and the other converted columns count as "changed" in every row; that is part of what cleaning did. The useful lines are the others. `state` changed in 530 rows, `status` in 42, and `unit_price` became missing in 9 rows, the dashes. A report like this, saved with each run, is the record of the cleaning that Chapter 11 recommends.
