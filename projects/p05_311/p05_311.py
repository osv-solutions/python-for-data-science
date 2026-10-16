"""Project 5 (Intermediate): City Service Requests Cleanup

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p05_311.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and audit
import pandas as pd

raw = pd.read_csv("data/service_requests.csv", dtype=str)
raw.columns = raw.columns.str.lower().str.replace(" ", "_")
print(raw.shape)
print(raw.iloc[0])

# %% Step 1: Plan and audit
profile = pd.DataFrame({"distinct": raw.nunique(),
                        "missing": raw.isna().sum()})
print(profile)
print(raw["complaint_type"].nunique(), "complaint type spellings")

# %% Step 2: Fix the types
fmt = "%m/%d/%Y %I:%M:%S %p"
df = raw.assign(
    created=pd.to_datetime(raw["created_date"], format=fmt),
    closed=pd.to_datetime(raw["closed_date"], format=fmt),
)
print(df["closed"].dt.year.value_counts().sort_index())

# %% Step 2: Fix the types
bad = (df["closed"].dt.year == 1900) | (df["closed"] < df["created"])
df["closed_fixed"] = bad
df.loc[bad, "closed"] = pd.NaT
print(bad.sum(), "impossible closing dates removed")

# %% Step 2: Fix the types
print(raw["incident_zip"].str.len().value_counts().sort_index())
zip5 = raw["incident_zip"].str.extract(r"^(\d{5})")[0]
df["zip"] = zip5.where(zip5 != "00000")
print(df["zip"].value_counts(dropna=False).head(4))

# %% Step 2: Fix the types
for col in ["latitude", "longitude"]:
    df[col] = pd.to_numeric(raw[col]).replace(0.0, float("nan"))
print(df[["latitude", "longitude"]].describe().round(3).loc[
    ["count", "min", "max"]])

# %% Step 3: Standardize the labels
types = raw["complaint_type"].value_counts()
print(types[types.index.str.contains("(?i)noise|pot")])

# %% Step 3: Standardize the labels
def normalize(text):
    return (text.str.strip().str.lower()
                .str.replace("–", "-", regex=False)
                .str.replace(r"\s*([-/])\s*", r" \1 ", regex=True))


fixes = {"pot hole": "pothole", "streetlight out": "street light out",
         "rodents": "rodent", "grafitti": "graffiti"}
kind = normalize(raw["complaint_type"]).replace(fixes)
print(kind.nunique(), "types")

# %% Step 3: Standardize the labels
official = ["Noise - Residential", "Heat/Hot Water", "Pothole",
            "Missed Collection", "Street Light Out",
            "Illegal Dumping", "Water Leak", "Rodent", "Graffiti",
            "Tree Damage"]
lookup = dict(zip(normalize(pd.Series(official)), official))
df["type"] = kind.map(lookup).astype("category")
print(df["type"].isna().sum(), "unmatched")

# %% Step 3: Standardize the labels
district = raw["district"].str.strip().str.title()
district = district.where(district != "Unspecified")
by_zip = (pd.DataFrame({"zip": df["zip"], "district": district})
          .dropna().groupby("zip")["district"]
          .agg(lambda d: d.mode()[0]))
df["district"] = district.fillna(df["zip"].map(by_zip))
print(district.isna().sum(), "->", df["district"].isna().sum(),
      "missing districts")

# %% Step 4: Duplicates and repeat reports
print(df.duplicated().sum(), "exact duplicates")
df = df.drop_duplicates(subset="unique_key").copy()
print(len(df), "requests,", df["unique_key"].is_unique)

# %% Step 4: Duplicates and repeat reports
df["spot"] = (df["latitude"].round(3).astype(str) + ","
              + df["longitude"].round(3).astype(str))
df = df.sort_values("created")
gap = df.groupby(["type", "spot"], observed=True)["created"].diff()
df["repeat"] = gap <= pd.Timedelta(hours=2)
print(df["repeat"].sum(), "repeat reports")
print(df[df["repeat"]]["type"].value_counts().head(4))

# %% Step 5: Validate
checks = {
    "keys unique": df["unique_key"].is_unique,
    "every type known": df["type"].notna().all(),
    "zip is five digits": df["zip"].dropna().str.fullmatch(
        r"\d{5}").all(),
    "closed after created": (df["closed"].dropna()
                             >= df.loc[df["closed"].notna(),
                                       "created"]).all(),
    "closed only if status Closed": (
        df.loc[df["closed"].notna(), "status"] == "Closed").all(),
    "created in 2025": (df["created"].dt.year == 2025).all(),
}
for name, ok in checks.items():
    print("ok  " if ok else "FAIL", name)

# %% Step 6: Join the lookup tables
agencies = pd.read_csv("data/agencies.csv")
districts = pd.read_csv("data/districts.csv")
n = len(df)
df = (df.merge(agencies, on="agency", how="left",
               validate="many_to_one")
        .merge(districts, on="district", how="left",
               validate="many_to_one"))
print(len(df) == n, df["target_days"].isna().sum(), "no target")
df["days"] = (df["closed"] - df["created"]).dt.total_seconds() / 86400
df["on_time"] = df["days"] <= df["target_days"]

# %% Step 7: What Riverton reports, where and when
problems = df[~df["repeat"]]
volume = pd.DataFrame({"calls": df["type"].value_counts(),
                       "problems": problems["type"].value_counts()})
print(volume.sort_values("problems", ascending=False))

# %% Step 7: What Riverton reports, where and when
import matplotlib.pyplot as plt

problems = problems.assign(month=problems["created"].dt.month)
four = ["Heat/Hot Water", "Noise - Residential", "Pothole", "Rodent"]
monthly = problems[problems["type"].isin(four)].pivot_table(
    index="month", columns="type", values="unique_key",
    aggfunc="count", observed=True)[four]
fig, ax = plt.subplots(figsize=(6.4, 3.4))
for name, style in zip(four, ["-o", "--s", "-.^", ":D"]):
    ax.plot(monthly.index, monthly[name], style, label=name,
            markersize=4)
ax.set_xticks(range(1, 13))
ax.set_xlabel("Month of 2025")
ax.set_ylabel("Problems reported")
ax.legend(fontsize=7, ncols=2)
plt.show()

# %% Step 7: What Riverton reports, where and when
rate = (problems.groupby("district").size()
        / districts.set_index("district")["population"] * 10_000)
print(rate.round(0).sort_values(ascending=False))

# %% Step 7: What Riverton reports, where and when
closed = problems.dropna(subset=["days"])
grid = closed.pivot_table(index="type", columns="district",
                          values="days", aggfunc="median",
                          observed=True)
print(grid.round(1))

# %% Step 7: What Riverton reports, where and when
report = problems.groupby("agency_name").agg(
    requests=("unique_key", "count"),
    target_days=("target_days", "first"),
    median_days=("days", "median"),
    on_time=("on_time", "mean"),
).sort_values("on_time")
print(report.round(2))

# %% Step 8: Save the results
keep = ["unique_key", "created", "closed", "closed_fixed", "type",
        "agency", "agency_name", "district", "zip", "latitude",
        "longitude", "status", "channel", "repeat", "days", "on_time"]
df[keep].to_parquet("requests_2025_clean.parquet", index=False)
with pd.ExcelWriter("riverton_311_2025.xlsx") as writer:
    volume.to_excel(writer, sheet_name="Volume")
    monthly.to_excel(writer, sheet_name="Monthly")
    rate.round(1).rename("per_10k").to_excel(writer,
                                             sheet_name="Districts")
    grid.round(1).to_excel(writer, sheet_name="Days to close")
    report.round(2).to_excel(writer, sheet_name="Agencies")
print(pd.read_parquet("requests_2025_clean.parquet").dtypes.head(6))
