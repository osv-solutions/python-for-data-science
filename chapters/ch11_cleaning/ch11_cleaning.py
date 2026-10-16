"""Chapter 11: Cleaning Messy Data

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch11_cleaning.py

or open the notebook and run the cells in order.
"""

# %% 11.1 A first look at messy data
import pandas as pd

raw = pd.read_csv("data/shop_orders_raw.csv")
print(raw.shape)
print(raw.head(3).T)

# %% 11.1 A first look at messy data
raw.info()

# %% 11.2 Missing values
missing = raw.isna().sum()
share = (missing / len(raw) * 100).round(1)
print(pd.DataFrame({"count": missing, "pct": share})[missing > 0])

# %% 11.2 Missing values
no_ship = raw["shipping_days"].isna()
print(raw.loc[no_ship, "status"].value_counts())

# %% 11.2 Missing values
demo = raw[["order_id", "quantity"]].copy()
demo["quantity_filled"] = demo["quantity"].isna()
demo["quantity"] = demo["quantity"].fillna(demo["quantity"].median())
print(demo[demo["quantity_filled"]])

# %% 11.2 Missing values
print(raw["unit_price"].isin(["-"]).sum(), "prices are '-'")
print(raw["rating"].value_counts(dropna=False).sort_index())

# %% 11.2 Missing values
raw = pd.read_csv("data/shop_orders_raw.csv",
                  na_values={"unit_price": ["-"], "rating": [0]})
print(raw[["unit_price", "rating"]].isna().sum())

# %% 11.3 Fixing types
text = raw["unit_price"].str.replace(r"[$,]", "", regex=True)
price = pd.to_numeric(text, errors="coerce")
print(price.dtype, price.isna().sum())
print(price.describe().round(2))

# %% 11.3 Fixing types
dates = pd.to_datetime(raw["order_date"], errors="coerce")
broken = dates.isna() & raw["order_date"].notna()
print(raw.loc[broken, ["order_id", "order_date"]])

# %% 11.3 Fixing types
qty = raw["quantity"].astype("Int64")
print(qty.dtype, qty.isna().sum(), qty.head(3).tolist())

# %% 11.3 Fixing types
grams = raw["bag_size"].map({"250g": 250, "500g": 500, "1kg": 1000})
print(grams.value_counts())

# %% 11.4 Standardizing labels
print(raw["status"].value_counts().rename(index=repr))

# %% 11.4 Standardizing labels
status = raw["status"].str.strip().str.lower()
print(status.value_counts())

# %% 11.4 Standardizing labels
state = (raw["state"].str.strip().str.upper()
         .str.replace(".", "", regex=False))
codes = sorted(state.dropna().unique())
print(codes[:8])
print(codes[8:])

# %% 11.4 Standardizing labels
names = {"PENNSYLVANIA": "PA", "PENN": "PA", "NEW YORK": "NY",
         "NEW JERSEY": "NJ", "OHIO": "OH", "MARYLAND": "MD",
         "VIRGINIA": "VA", "MASS": "MA"}
state = state.replace(names)
print(state.value_counts(dropna=False))

# %% 11.5 Duplicates
print(raw.duplicated().sum(), "exact duplicates")
dedup = raw.drop_duplicates()
print(len(raw), "->", len(dedup))

# %% 11.5 Duplicates
twice = dedup["order_id"].duplicated(keep=False)
cols = ["order_id", "status", "shipping_days"]
print(dedup.loc[twice, cols].head(6))

# %% 11.5 Duplicates
dedup = dedup.drop_duplicates(subset="order_id", keep="last")
print(len(dedup), dedup["order_id"].is_unique)

# %% 11.6 Outliers
orders = dedup.assign(
    unit_price=pd.to_numeric(dedup["unit_price"]
                             .str.replace(r"[$,]", "", regex=True)),
    quantity=dedup["quantity"].astype("Int64"),
)
cols = ["quantity", "unit_price", "shipping_days", "rating"]
print(orders[cols].describe().round(1))

# %% 11.6 Outliers
bad_ship = orders["shipping_days"] < 0
rating = orders["rating"]
bad_rating = rating.notna() & ~rating.between(1, 5)
print(bad_ship.sum(), "negative shipping times")
print(orders.loc[bad_rating, ["order_id", "rating"]])

# %% 11.6 Outliers
typical = (orders.groupby(["product", "bag_size"])["unit_price"]
           .transform("median"))
odd = orders["unit_price"] > 3 * typical
print(orders.loc[odd, ["order_id", "product", "bag_size",
                       "unit_price"]])
print(typical[odd].tolist())

# %% 11.6 Outliers
q1, q3 = orders["quantity"].quantile([0.25, 0.75])
fence = q3 + 1.5 * (q3 - q1)
big = orders["quantity"] > fence
print("upper fence:", fence)
print(orders.loc[big, "quantity"].value_counts().sort_index())

# %% 11.6 Outliers
huge = orders["quantity"] > 20
print(orders.loc[huge, ["order_id", "customer_id", "bag_size",
                        "quantity", "status"]])

# %% 11.7 Validating with checks
STATUSES = ["delivered", "shipped", "processing", "cancelled"]


def check_orders(df):
    """Return the names of the checks that fail."""
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

# %% 11.7 Validating with checks
print(check_orders(orders))

# %% 11.8 Putting it together: a cleaning function
def fix_types(df):
    price = df["unit_price"].str.replace(r"[$,]", "", regex=True)
    return df.assign(
        order_date=pd.to_datetime(df["order_date"], errors="coerce"),
        unit_price=pd.to_numeric(price),
        quantity=df["quantity"].astype("Int64"),
        shipping_days=df["shipping_days"].astype("Int64"),
        rating=df["rating"].astype("Int64"),
        grams=df["bag_size"].map({"250g": 250, "500g": 500,
                                  "1kg": 1000}),
    )

# %% 11.8 Putting it together: a cleaning function
def fix_labels(df):
    state = (df["state"].str.strip().str.upper()
             .str.replace(".", "", regex=False).replace(names))
    return df.assign(status=df["status"].str.strip().str.lower(),
                     state=state)


def drop_repeats(df):
    return (df.drop_duplicates()
              .drop_duplicates(subset="order_id", keep="last"))

# %% 11.8 Putting it together: a cleaning function
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

# %% 11.8 Putting it together: a cleaning function
clean = (pd.read_csv("data/shop_orders_raw.csv",
                     na_values={"unit_price": ["-"], "rating": [0]})
         .pipe(fix_types).pipe(fix_labels).pipe(drop_repeats)
         .pipe(fix_outliers))
print(len(clean), "orders; failed checks:", check_orders(clean))
clean.to_parquet("shop_orders_clean.parquet", index=False)

# %% 11.8 Putting it together: a cleaning function
rated = clean[clean["rating"].notna()]
by_days = rated.groupby("shipping_days")["rating"].agg(["mean",
                                                       "count"])
print(by_days.round(2))
