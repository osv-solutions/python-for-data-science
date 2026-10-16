"""Solutions to the Chapter 11 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch11_solutions.py

The explanations are in ch11_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
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

# %% Exercise 11.1
raw0 = pd.read_csv("data/shop_orders_raw.csv")
profile = pd.DataFrame({"distinct": raw0.nunique(),
                        "missing": raw0.isna().sum(),
                        "dtype": raw0.dtypes.astype(str)})
print(profile)

# %% Exercise 11.2
print(clean["status"].value_counts())
delivered = clean[clean["status"] == "delivered"]
print(f"{delivered['rating'].notna().mean():.1%} rated")

# %% Exercise 11.3
dated = clean.dropna(subset=["order_date"])
print(len(clean), "->", len(dated))
per_month = dated["order_date"].dt.to_period("M").value_counts()
print(per_month.sort_index())

# %% Exercise 11.4
known = clean.groupby("customer_id")["state"].transform("first")
filled = clean["state"].fillna(known)
print(clean["state"].isna().sum(), "->", filled.isna().sum())

# %% Exercise 11.5
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

# %% Exercise 11.6
def iqr_flags(s):
    q1, q3 = s.quantile([0.25, 0.75])
    return (s < q1 - 1.5 * (q3 - q1)) | (s > q3 + 1.5 * (q3 - q1))


typed = raw.pipe(fix_types).pipe(fix_labels).pipe(drop_repeats)
flags = typed.groupby("bag_size")["unit_price"].transform(iqr_flags)
print(typed.loc[flags, ["order_id", "product", "bag_size",
                        "unit_price"]])

# %% Exercise 11.7
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
