"""Solutions to the Chapter 18 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch18_solutions.py

The explanations are in ch18_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="colorblind")
flats = pd.read_csv("data/apartments.csv", parse_dates=["listed"])
flats.loc[flats["sqft"] > 4000, "sqft"] = (
    flats.loc[flats["sqft"] > 4000, "sqft"] // 10)
flats["per_sqft"] = flats["rent"] / flats["sqft"]


def profile(df):
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "distinct": df.nunique(),
        "example": df.iloc[0].astype(str).str[:10],
    })

# %% Exercise 18.1
raw = pd.read_csv("data/shop_orders_raw.csv")
print(profile(raw))
print(len(raw), "rows")

# %% Exercise 18.2
days = flats["days_on_market"]
fig, ax = plt.subplots(figsize=(6, 2.8))
sns.histplot(days, bins=40, ax=ax)
ax.axvline(days.median(), color="#c0582b", ls="--")
ax.axvline(days.mean(), color="#1d5c8c", ls=":")
ax.set_title(f"median {days.median():.0f} days, mean "
             f"{days.mean():.1f} days")
plt.show()

# %% Exercise 18.3
city = flats.groupby("laundry")["per_sqft"].median()
print((city / city["none"] - 1).mul(100).round(1))
by_district = flats.pivot_table(index="district", columns="laundry",
                                values="per_sqft", aggfunc="median")
premium = (by_district["in unit"] / by_district["none"] - 1) * 100
print(premium.round(1).sort_values())

# %% Exercise 18.4
fig, ax = plt.subplots(figsize=(6, 3.4))
sns.scatterplot(data=flats, x="distance_km", y="per_sqft",
                hue="district", s=10, alpha=0.6, ax=ax)
ax.set_xlabel("Distance to downtown (km)")
ax.set_ylabel("Rent per sq ft ($)")
plt.show()
within = flats.groupby("district")[["distance_km", "per_sqft"]].corr()
print(within.xs("per_sqft", level=1)["distance_km"].round(2))

# %% Exercise 18.5
month = flats["listed"].dt.month
per_month = flats.groupby(month).agg(
    listings=("listing_id", "count"),
    median_days=("days_on_market", "median"))
print(per_month)

# %% Exercise 18.6
nums = ["rent", "sqft", "per_sqft", "year_built", "distance_km",
        "days_on_market"]
pearson = flats[nums].corr()
spearman = flats[nums].corr(method="spearman")
gap = (spearman - pearson).abs().stack()
gap = gap[gap.index.get_level_values(0) < gap.index.get_level_values(1)]
print(gap.sort_values(ascending=False).head(3).round(2))
print(f"rent vs sqft: Pearson {pearson.loc['rent', 'sqft']:.2f}, "
      f"Spearman {spearman.loc['rent', 'sqft']:.2f}")

# %% Exercise 18.7
raw = pd.read_csv("data/service_requests.csv", dtype=str)
raw.columns = raw.columns.str.lower().str.replace(" ", "_")
print(profile(raw)[["missing", "distinct"]])
fmt = "%m/%d/%Y %I:%M:%S %p"
created = pd.to_datetime(raw["created_date"], format=fmt)
closed = pd.to_datetime(raw["closed_date"], format=fmt)
days = (closed - created).dt.total_seconds() / 86400
print((days < 0).sum(), "negative durations,",
      (closed.dt.year == 1900).sum(), "closed in 1900")

# %% Exercise 18.7
kind = (raw["complaint_type"].str.lower().str.replace("–", "-")
        .str.replace(r"\s*([-/])\s*", r" \1 ", regex=True).str.strip())
ok = (days >= 0) & (closed.dt.year > 2000)
data = raw.assign(days=days, kind=kind)[ok].drop_duplicates(
    "unique_key")
order = data.groupby("agency")["days"].median().sort_values().index
fig, ax = plt.subplots(figsize=(6, 3))
sns.boxplot(data=data, x="agency", y="days", order=order,
            color="#2a9bb0", fliersize=1, ax=ax)
ax.set_yscale("log")
ax.set_title("Police close requests in hours, Parks in weeks")
plt.show()
