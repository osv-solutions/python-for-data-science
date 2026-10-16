"""Chapter 18: Exploratory Data Analysis

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch18_eda.py

or open the notebook and run the cells in order.
"""

# %% 18.2 Step 1: The question and the data
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="colorblind")
flats = pd.read_csv("data/apartments.csv", parse_dates=["listed"])
print(flats.shape)
print(flats.iloc[0])

# %% 18.3 Step 2: Structure
def profile(df):
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "distinct": df.nunique(),
        "example": df.iloc[0].astype(str).str[:10],
    })


print(profile(flats))

# %% 18.4 Step 3: Quality
cols = ["bedrooms", "sqft", "rent", "year_built", "distance_km",
        "days_on_market"]
summary = flats[cols].describe().round(1).T
print(summary[["mean", "min", "25%", "50%", "75%", "max"]])

# %% 18.4 Step 3: Quality
odd = flats[(flats["sqft"] > 4000) | (flats["rent"] > 6000)]
print(odd[["listing_id", "district", "bedrooms", "bathrooms", "sqft",
           "rent"]])

# %% 18.4 Step 3: Quality
flats.loc[flats["sqft"] > 4000, "sqft"] = (
    flats.loc[flats["sqft"] > 4000, "sqft"] // 10)
flats["per_sqft"] = flats["rent"] / flats["sqft"]
print(flats["sqft"].max(), flats["per_sqft"].describe().round(2)
      [["min", "50%", "max"]].tolist())

# %% 18.5 Step 4: One variable at a time
fig, axes = plt.subplots(1, 2, figsize=(7, 2.8))
sns.histplot(flats["rent"], bins=40, ax=axes[0])
sns.histplot(flats["rent"], bins=40, log_scale=True, ax=axes[1])
axes[0].set_title("Rent ($)")
axes[1].set_title("Rent ($, log scale)")
plt.show()

# %% 18.5 Step 4: One variable at a time
for col in ["district", "bedrooms", "laundry"]:
    print(flats[col].value_counts().to_frame().T.to_string())
print(flats[["parking", "pets_allowed"]].mean().round(2).to_dict())

# %% 18.6 Step 5: Two variables
fig, ax = plt.subplots(figsize=(6, 3.2))
sns.scatterplot(data=flats, x="sqft", y="rent", hue="bedrooms",
                palette="crest", s=12, alpha=0.7, ax=ax)
ax.set_yscale("log")
ax.set_title("Bigger apartments cost more, but with wide spread")
plt.show()

# %% 18.6 Step 5: Two variables
nums = ["rent", "sqft", "per_sqft", "year_built", "distance_km",
        "days_on_market"]
corr = flats[nums].corr()
fig, ax = plt.subplots(figsize=(5.4, 4))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu", center=0,
            vmin=-1, vmax=1, cbar=False, ax=ax)
plt.show()

# %% 18.7 Step 6: Groups and confounders
order = (flats.groupby("district")["per_sqft"].median()
         .sort_values(ascending=False).index)
fig, ax = plt.subplots(figsize=(6, 3))
sns.boxplot(data=flats, x="district", y="per_sqft", order=order,
            color="#2a9bb0", fliersize=2, ax=ax)
ax.set_ylabel("Rent per sq ft ($)")
ax.set_xlabel("")
plt.show()

# %% 18.7 Step 6: Groups and confounders
flats["era"] = pd.cut(flats["year_built"], [1899, 1950, 1980, 2000,
                                            2025],
                      labels=["before 1950", "1951-1980", "1981-2000",
                              "after 2000"])
print(flats.groupby("era", observed=True)["per_sqft"].median()
      .round(2))

# %% 18.7 Step 6: Groups and confounders
share = pd.crosstab(flats["district"], flats["era"],
                    normalize="index")
print((share * 100).round(0))

# %% 18.7 Step 6: Groups and confounders
within = flats.pivot_table(index="district", columns="era",
                           values="per_sqft", aggfunc="median",
                           observed=True)
print(within.loc[order].round(2))

# %% 18.7 Step 6: Groups and confounders
typical = flats.groupby("district")["per_sqft"].transform("median")
flats["vs_market"] = flats["per_sqft"] / typical - 1
flats["pricing"] = pd.cut(flats["vs_market"],
                          [-1, -0.1, 0.1, 10],
                          labels=["below", "near", "above"])
print(flats.groupby("pricing", observed=True)["days_on_market"]
      .agg(["median", "count"]))

# %% 18.8 Step 7: Summary and story
data = flats.dropna(subset=["era", "per_sqft"])
fig, ax = plt.subplots(figsize=(6.4, 3.4))
sns.pointplot(data=data, x="district", y="per_sqft", hue="era",
              order=order, estimator="median", errorbar=None,
              dodge=0.5, linestyle="none", markers="o", ax=ax)
ax.set_title("In every district, older apartments rent for less")
ax.set_ylabel("Median rent per sq ft ($)")
ax.set_xlabel("")
ax.legend(title="Built", fontsize=8, ncols=2)
plt.show()
