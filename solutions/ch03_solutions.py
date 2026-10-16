"""Solutions to the Chapter 3 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch03_solutions.py

The explanations are in ch03_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
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

# %% Exercise 3.1
steps = pd.Series([6200, 9100, 7400, 10350, 5800, 12900, 8300],
                  index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
                         "Sun"])
print(round(steps.mean()))
print("best day:", steps.idxmax())
print(steps[steps > 8000])

# %% Exercise 3.2
cols = ["bill_length_mm", "bill_depth_mm"]
print(penguins.loc[100:105, cols])
print(penguins.iloc[100:106, [2, 3]].equals(penguins.loc[100:105,
                                                          cols]))

# %% Exercise 3.3
long_dream = penguins[(penguins["island"] == "Dream")
                      & (penguins["flipper_length_mm"] >= 200)]
print(len(long_dream))
print(long_dream["species"].value_counts())

# %% Exercise 3.4
penguins["bill_ratio"] = (penguins["bill_length_mm"]
                          / penguins["bill_depth_mm"]).round(2)
print(penguins.nlargest(5, "bill_ratio")[["species", "bill_ratio"]])

# %% Exercise 3.5
stores["size"] = "small"
stores.loc[stores["sq_ft"] >= 8000, "size"] = "medium"
stores.loc[stores["sq_ft"] >= 10000, "size"] = "large"
print(stores[["city", "sq_ft", "size"]])
print(stores["size"].value_counts())

# %% Exercise 3.6
heavy_females = (
    penguins
    .dropna()
    .query("sex == 'female'")
    .assign(mass_lb=lambda d: (d["body_mass_g"] / 453.6).round(1))
    .nlargest(3, "mass_lb")
    .loc[:, ["species", "island", "mass_lb"]]
)
print(heavy_females)

# %% Exercise 3.7
september = pd.Series({"coffee": 8.99, "tea": 4.50, "milk": 3.29})
october = pd.Series({"milk": 3.49, "coffee": 9.49, "bread": 2.99})
print(october - september)
print(october.sub(september, fill_value=0))
