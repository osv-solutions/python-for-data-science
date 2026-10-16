"""Project 2 (Beginner): World Development Explorer

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p02_world.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and meet the API
import practice_web
import requests

BASE = practice_web.start()
url = f"{BASE}/v2/country/IND/indicator/SP.DYN.LE00.IN"
response = requests.get(url, timeout=10)
print(response.headers["Content-Type"])
print(response.text[:120])

# %% Step 1: Plan and meet the API
response = requests.get(url, params={"format": "json"}, timeout=10)
from pprint import pprint

meta, rows = response.json()
print("page", meta["page"], "of", meta["pages"], "-", meta["total"],
      "data points")
pprint(rows[0], width=68)

# %% Step 2: Download an indicator for every country
import json
from pathlib import Path

RAW = Path("raw")
RAW.mkdir(exist_ok=True)

# %% Step 2: Download an indicator for every country
def download(indicator, per_page=500):
    """Fetch every page of an indicator for all countries; save it."""
    url = f"{BASE}/v2/country/all/indicator/{indicator}"
    params = {"format": "json", "date": "1952:2007",
              "per_page": per_page}
    rows, page, pages = [], 1, 1
    while page <= pages:
        reply = requests.get(url, params=params | {"page": page},
                             timeout=30)
        meta, data = reply.json()
        rows, pages, page = rows + data, meta["pages"], page + 1
    (RAW / f"{indicator}.json").write_text(json.dumps(rows))
    return rows

# %% Step 2: Download an indicator for every country
INDICATORS = {"SP.POP.TOTL": "population",
              "SP.DYN.LE00.IN": "life_exp",
              "NY.GDP.PCAP.PP.KD": "gdp_per_cap"}
raw = {code: download(code) for code in INDICATORS}
for code, rows in raw.items():
    print(f"{code:<20}{len(rows):>6} rows")

# %% Step 3: From JSON to one table
import pandas as pd

def to_series(rows, name):
    """One indicator as a Series indexed by (iso3, year)."""
    frame = pd.DataFrame({
        "iso3": [r["countryiso3code"] for r in rows],
        "year": [int(r["date"]) for r in rows],
        name: [r["value"] for r in rows]})
    return frame.set_index(["iso3", "year"])[name]

# %% Step 3: From JSON to one table
world = pd.DataFrame({name: to_series(raw[code], name)
                      for code, name in INDICATORS.items()})
world = world.reset_index().sort_values(["iso3", "year"])
print(world.shape)
print(world.head(3))
print(world.isna().sum().sum(), "missing values")

# %% Step 3: From JSON to one table
meta, countries = requests.get(f"{BASE}/v2/country", timeout=10,
                               params={"format": "json",
                                       "per_page": 300}).json()
names = {c["id"]: c["name"] for c in countries}
regions = {c["id"]: c["region"]["value"] for c in countries}
world["country"] = world["iso3"].map(names)
world["continent"] = world["iso3"].map(regions)
print(meta["total"], "countries")
print(world["continent"].value_counts())

# %% Step 4: Life expectancy by continent
def weighted(group):
    return (group["life_exp"] * group["population"]).sum() \
        / group["population"].sum()

ends = world[world["year"].isin([1952, 2007])]
by_cont = ends.groupby(["continent", "year"]).apply(weighted)
table = by_cont.unstack().round(1)
table["gain"] = table[2007] - table[1952]
print(table.sort_values("gain", ascending=False))

# %% Step 5: The biggest gains
wide = (world[world["year"].isin([1952, 2007])]
        .pivot(index="country", columns="year", values="life_exp"))
wide["gain"] = wide[2007] - wide[1952]
print(wide.nlargest(5, "gain").round(1))
print(wide.nsmallest(3, "gain").round(1))

# %% Step 6: Income and life expectancy
import matplotlib.pyplot as plt

y2007 = world[world["year"] == 2007]
fig, ax = plt.subplots(figsize=(6.4, 3.8))
markers = dict(zip(sorted(y2007["continent"].unique()), "os^Dv"))
for continent, group in y2007.groupby("continent"):
    ax.scatter(group["gdp_per_cap"], group["life_exp"], s=18,
               marker=markers[continent], label=continent, alpha=0.8)
ax.set_xscale("log")
ax.set_xlabel("GDP per person, 2007 (log scale)")
ax.set_ylabel("Life expectancy (years)")
ax.legend(fontsize=8)
plt.show()

# %% Step 6: Income and life expectancy
import numpy as np

log_income = np.log10(y2007["gdp_per_cap"])
r = np.corrcoef(log_income, y2007["life_exp"])[0, 1]
print(f"correlation of log income and life expectancy: {r:.2f}")

# %% Step 7: Save the explorer's results
with pd.ExcelWriter("world_development.xlsx") as writer:
    world.to_excel(writer, sheet_name="Data", index=False)
    table.to_excel(writer, sheet_name="Continents")
    wide.sort_values("gain", ascending=False).round(1).to_excel(
        writer, sheet_name="Gains")
print(list(pd.read_excel("world_development.xlsx", sheet_name=None)))
