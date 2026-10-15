"""Chapter 3: pandas Essentials

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch03_pandas.py

or open the notebook and run the cells in order.
"""

# %% 3.1 Series: a labeled column
import pandas as pd

visitors = pd.Series([31.5, 28.2, 40.1, 45.8],
                     index=["Jan", "Feb", "Mar", "Apr"],
                     name="visitors")
print(visitors)
print(visitors["Mar"], visitors.iloc[0])

# %% 3.1 Series: a labeled column
print((visitors * 1000).astype(int))
print(visitors[visitors > 30])
print(visitors.mean().round(2), visitors.idxmax())

# %% 3.1 Series: a labeled column
last_year = pd.Series([29.0, 30.4, 35.2, 47.1],
                      index=["Jan", "Feb", "Mar", "Apr"])
change = visitors - last_year
print(change.round(1))
march_only = pd.Series([2.0], index=["Mar"])
print(visitors + march_only)

# %% 3.2 DataFrames: a table of Series
stores = pd.DataFrame({
    "city": ["Pittsburgh", "Erie", "Harrisburg", "Scranton",
             "Allentown", "Lancaster"],
    "region": ["West", "West", "Central", "East", "East", "Central"],
    "sq_ft": [12000, 7500, 9800, 6400, 11200, 8300],
    "sales_k": [3150, 1480, 2210, 1395, 2870, 1920],
    "opened": [2011, 2016, 2013, 2019, 2012, 2017],
})
print(stores)

# %% 3.2 DataFrames: a table of Series
print(stores.shape)
print(stores.columns.tolist())
print(stores.dtypes)

# %% 3.3 Looking at a new dataset
penguins = pd.read_csv("data/penguins.csv")
print(penguins.sample(4, random_state=1))

# %% 3.3 Looking at a new dataset
penguins.info()

# %% 3.3 Looking at a new dataset
print(penguins.describe().round(1))

# %% 3.3 Looking at a new dataset
print(penguins["island"].value_counts())
print(penguins["sex"].value_counts(dropna=False))

# %% 3.4 Selecting columns and rows
print(stores["city"].head(3))
print(stores[["city", "sales_k"]].head(3))

# %% 3.4 Selecting columns and rows
print(stores.loc[2, "city"])
print(stores.loc[1:3, ["city", "sales_k"]])
print(stores.iloc[1:3, [0, 3]])

# %% 3.4 Selecting columns and rows
by_city = stores.set_index("city")
print(by_city.loc["Erie"])
print(by_city.loc["Harrisburg":"Scranton", "sales_k"])

# %% 3.5 Filtering rows
big = stores[stores["sq_ft"] >= 9000]
print(big[["city", "sq_ft"]])
west_new = stores[(stores["region"] == "West")
                  & (stores["opened"] > 2015)]
print(west_new["city"].tolist())

# %% 3.5 Filtering rows
print(stores[stores["region"].isin(["East", "Central"])].shape)
print(stores[stores["opened"].between(2012, 2016)]["city"].tolist())
print(stores.query("sales_k > 2000 and region != 'West'")["city"]
      .tolist())

# %% 3.6 Sorting
print(stores.sort_values("sales_k", ascending=False)
      [["city", "sales_k"]].head(3))
print(stores.sort_values(["region", "sq_ft"],
                         ascending=[True, False])
      [["region", "city", "sq_ft"]])

# %% 3.6 Sorting
print(stores.nlargest(2, "sales_k")[["city", "sales_k"]])
print(stores.nsmallest(1, "opened")["city"].item())

# %% 3.7 Adding and changing columns
stores["sales_per_sqft"] = (stores["sales_k"] * 1000
                            / stores["sq_ft"]).round(1)
stores["age"] = 2026 - stores["opened"]
print(stores[["city", "sales_per_sqft", "age"]])

# %% 3.7 Adding and changing columns
stores["tier"] = "standard"
stores.loc[stores["sales_per_sqft"] >= 240, "tier"] = "flagship"
print(stores[["city", "tier"]].value_counts("tier"))

# %% 3.7 Adding and changing columns
tidy = (stores.drop(columns=["opened"])
        .rename(columns={"sales_k": "sales_thousands"}))
print(", ".join(tidy.columns))

# %% 3.8 Method chaining
heavy_gentoo = (
    penguins
    .dropna(subset=["body_mass_g", "sex"])
    .query("species == 'Gentoo'")
    .assign(mass_kg=lambda d: d["body_mass_g"] / 1000)
    .sort_values("mass_kg", ascending=False)
    .loc[:, ["island", "sex", "mass_kg"]]
    .head(5)
)
print(heavy_gentoo)

# %% 3.9 Putting it together: ranking the stores
import numpy as np

median = stores["sales_per_sqft"].median()
ranking = (
    stores
    .assign(vs_median=lambda d: (d["sales_per_sqft"] / median - 1)
            .mul(100).round(1),
            status=lambda d: np.where(d["sales_per_sqft"] >= median,
                                      "above", "below"))
    .sort_values("sales_per_sqft", ascending=False)
    .reset_index(drop=True)
    .loc[:, ["city", "region", "sales_per_sqft", "vs_median",
             "status"]]
)
ranking.index = ranking.index + 1
print(f"median: ${median} per sq ft")
print(ranking)
