"""Project 6 (Intermediate): Weather Trends

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p06_weather.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and meet the API
from pprint import pprint

import practice_web
import requests

BASE = practice_web.start()
params = {"latitude": 40.44, "longitude": -80.0,
          "start_date": "2025-07-01", "end_date": "2025-07-07",
          "daily": "temperature_2m_max,precipitation_sum",
          "timezone": "America/New_York"}
response = requests.get(f"{BASE}/v1/archive", params=params,
                        timeout=30)
week = response.json()
pprint(list(week), compact=True, width=70)
print(week["daily_units"])
print(week["daily"]["temperature_2m_max"])

# %% Step 1: Plan and meet the API
bad = dict(params, daily="temperature_max")
response = requests.get(f"{BASE}/v1/archive", params=bad, timeout=30)
print(response.status_code)
print(response.json())

# %% Step 2: Download ten years, one request per city and year
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CITIES = {"Pittsburgh": (40.44, -80.0, "America/New_York"),
          "Phoenix": (33.45, -112.07, "America/Phoenix"),
          "Seattle": (47.61, -122.33, "America/Los_Angeles")}
DAILY = "temperature_2m_max,temperature_2m_min,precipitation_sum"
RAW = Path("raw")
RAW.mkdir(exist_ok=True)

# %% Step 2: Download ten years, one request per city and year
def download(city, year):
    path = RAW / f"{city.lower()}_{year}.json"
    if path.exists():
        return json.loads(path.read_text())
    lat, lon, zone = CITIES[city]
    params = {"latitude": lat, "longitude": lon, "daily": DAILY,
              "start_date": f"{year}-01-01",
              "end_date": f"{year}-12-31", "timezone": zone}
    response = requests.get(f"{BASE}/v1/archive", params=params,
                            timeout=60)
    response.raise_for_status()
    path.write_text(response.text)
    return response.json()

# %% Step 2: Download ten years, one request per city and year
YEARS = range(2016, 2026)
frames = []
for city in CITIES:
    for year in YEARS:
        daily = pd.DataFrame(download(city, year)["daily"])
        frames.append(daily.assign(city=city))
weather = pd.concat(frames, ignore_index=True)
print(weather.shape)
print(sorted(p.name for p in RAW.iterdir())[:3])

# %% Step 3: Tidy and check
weather = weather.rename(columns={
    "time": "date", "temperature_2m_max": "tmax",
    "temperature_2m_min": "tmin", "precipitation_sum": "precip"})
weather["date"] = pd.to_datetime(weather["date"])
weather = weather[["city", "date", "tmax", "tmin", "precip"]]
weather["city"] = weather["city"].astype("category")
print(weather.head(3))

# %% Step 3: Tidy and check
days = weather.groupby("city", observed=True)["date"]
dup = weather.duplicated(["city", "date"]).any()
checks = {
    "3,653 days per city": (days.count() == 3653).all(),
    "no duplicate days": not dup,
    "no gaps": (days.diff().dropna() == pd.Timedelta(days=1)).all(),
    "no missing values": weather.notna().all().all(),
    "tmin <= tmax": (weather["tmin"] <= weather["tmax"]).all(),
    "precip >= 0": (weather["precip"] >= 0).all(),
    "plausible range": weather["tmax"].between(-40, 55).all(),
}
for name, ok in checks.items():
    print("ok  " if ok else "FAIL", name)

# %% Step 4: The climate at a glance
weather["month"] = weather["date"].dt.month
weather["year"] = weather["date"].dt.year
normals = weather.groupby(["city", "month"], observed=True).agg(
    high=("tmax", "mean"), low=("tmin", "mean"),
    precip=("precip", "sum"))
normals["precip"] /= len(YEARS)          # a total per month, per year
table = normals.unstack("city").round(0)
print(table["high"].T.astype(int))

# %% Step 4: The climate at a glance
fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.6), sharey=True)
for ax, city in zip(axes, CITIES):
    n = normals.loc[city]
    ax.fill_between(n.index, n["low"], n["high"], color="#c0582b",
                    alpha=0.3)
    rain = ax.twinx()
    rain.bar(n.index, n["precip"], color="#1d5c8c", alpha=0.35)
    rain.set_ylim(0, 400)
    ax.set_zorder(rain.get_zorder() + 1)    # the band over the bars
    ax.patch.set_visible(False)
    rain.set_yticks([] if city != "Seattle" else [0, 100, 200])
    ax.set_title(city, fontsize=9)
    ax.set_xticks([1, 4, 7, 10], ["Jan", "Apr", "Jul", "Oct"])
axes[0].set_ylabel("Temperature (°C)")
rain.set_ylabel("Rain per month (mm)", fontsize=7)
fig.tight_layout()
plt.show()

# %% Step 5: Smoothing and anomalies
pitt = weather[weather["city"] == "Pittsburgh"].set_index("date")
smooth = pitt["tmax"].rolling(30, center=True).mean()
fig, ax = plt.subplots(figsize=(6.6, 2.4))
ax.plot(pitt.index, pitt["tmax"], color="#c0582b", lw=0.4, alpha=0.5)
ax.plot(smooth.index, smooth, color="#7a2e12", lw=1.4)
ax.set_ylabel("Daily high (°C)")
ax.set_title("Pittsburgh, 2016 to 2025", fontsize=9, loc="left")
plt.show()

# %% Step 5: Smoothing and anomalies
doy = weather["date"].dt.dayofyear.clip(upper=365)
weather["normal"] = weather.groupby(
    ["city", doy], observed=True)["tmax"].transform("mean")
weather["normal"] = weather.groupby("city", observed=True)[
    "normal"].transform(lambda s: s.rolling(31, center=True,
                                            min_periods=1).mean())
weather["anomaly"] = weather["tmax"] - weather["normal"]
print(weather.groupby("city", observed=True)["anomaly"].agg(
    ["mean", "std"]).round(2))

# %% Step 6: Is it getting warmer?
annual = weather.pivot_table(index="year", columns="city",
                             values="anomaly", aggfunc="mean",
                             observed=True)
print(annual.round(2).T)

# %% Step 6: Is it getting warmer?
from scipy import stats

def trend(series):
    fit = stats.linregress(series.index, series.values)
    half = stats.t.ppf(0.975, len(series) - 2) * fit.stderr
    return pd.Series({"per_decade": fit.slope * 10,
                      "low": (fit.slope - half) * 10,
                      "high": (fit.slope + half) * 10})

print(annual.apply(trend).round(2).T)

# %% Step 6: Is it getting warmer?
early = pd.concat(
    [pd.DataFrame(download(c, y)["daily"]).assign(city=c)
     for c in CITIES for y in range(2000, 2016)])
early["year"] = pd.to_datetime(early["time"]).dt.year
early["tmean"] = (early["temperature_2m_max"]
                  + early["temperature_2m_min"]) / 2
weather["tmean"] = (weather["tmax"] + weather["tmin"]) / 2
both = pd.concat([early[["city", "year", "tmean"]],
                  weather[["city", "year", "tmean"]]])
long_run = both.pivot_table(index="year", columns="city",
                            values="tmean", aggfunc="mean",
                            observed=True)
print(long_run.apply(trend).round(2).T)

# %% Step 6: Is it getting warmer?
fig, ax = plt.subplots(figsize=(6.6, 2.6))
colors = {"Pittsburgh": "#1d5c8c", "Phoenix": "#c0582b",
          "Seattle": "#2a7f8f"}
for city, color in colors.items():
    s = long_run[city] - long_run[city].mean()
    fit = stats.linregress(s.index, s.values)
    ax.plot(s.index, s, "o-", color=color, ms=3, lw=0.8, label=city)
    ax.plot(s.index, fit.intercept + fit.slope * s.index, color=color,
            lw=1.6, ls="--")
ax.axhline(0, color="#888888", lw=0.6)
ax.set_ylabel("Annual mean vs average (°C)")
ax.legend(fontsize=7, ncols=3)
plt.show()

# %% Step 7: Extremes
hottest = weather.loc[weather.groupby("city", observed=True)[
    "tmax"].idxmax(), ["city", "date", "tmax", "normal"]]
print(hottest.round(1).to_string(index=False))

# %% Step 7: Extremes
weather["hot"] = weather["tmax"] >= 32
weather["frost"] = weather["tmin"] < 0
counts = weather.groupby(["city", "year"], observed=True)[
    ["hot", "frost"]].sum().unstack("city")
print(counts["hot"].T)
print(counts["frost"].T)

# %% Step 7: Extremes
def longest_dry_spell(df):
    dry = df["precip"] < 1
    run_id = (dry != dry.shift()).cumsum()
    runs = df[dry].groupby(run_id[dry])["date"].agg(["min", "count"])
    return runs.loc[runs["count"].idxmax()]

spells = weather.groupby("city", observed=True).apply(
    longest_dry_spell)
print(spells)

# %% Step 8: Save the results
weather.drop(columns=["month", "hot", "frost"]).to_parquet(
    "weather_2016_2025.parquet", index=False)
with pd.ExcelWriter("weather_summary.xlsx") as writer:
    table["high"].to_excel(writer, sheet_name="Normal highs")
    table["precip"].to_excel(writer, sheet_name="Normal rain")
    annual.apply(trend).T.round(2).to_excel(writer,
                                            sheet_name="Trend 10y")
    long_run.apply(trend).T.round(2).to_excel(writer,
                                              sheet_name="Trend 26y")
    counts.to_excel(writer, sheet_name="Hot and frost days")
print(*pd.ExcelFile("weather_summary.xlsx").sheet_names, sep=" | ")
