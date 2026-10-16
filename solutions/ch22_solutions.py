"""Solutions to the Chapter 22 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch22_solutions.py

The explanations are in ch22_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import time

import duckdb
import numpy as np
import pandas as pd
import polars as pl

pl.Config.set_tbl_formatting("ASCII_MARKDOWN")
pl.Config.set_tbl_hide_column_data_types(True)
daily = pd.read_csv("data/bike_daily.csv", parse_dates=["date"])
stations = np.arange(1, 121)
popularity = 1 / stations ** 0.8


def make_trips(year=2025, seed=22, scale=9):
    days = daily[daily["date"].dt.year == year]
    rng = np.random.default_rng(seed)
    n = days["rides"].sum() * scale
    day = rng.choice(days["date"].to_numpy(), n,
                     p=days["rides"] / days["rides"].sum())
    casual = rng.random(n) < 0.3
    hour = np.where(casual, rng.normal(15, 3, n), rng.choice(
        [8, 17], n) + rng.normal(0, 1.5, n)).clip(0, 23.99)
    return pd.DataFrame({
        "start_time": day + (hour * 3600).astype("timedelta64[s]"),
        "duration_min": np.where(casual, rng.gamma(2.2, 9, n),
                                 rng.gamma(2, 5.5, n)).round(1),
        "start_station": rng.choice(stations, n,
                                    p=popularity / popularity.sum()),
        "rider": np.where(casual, "casual", "member"),
        "bike": np.where(rng.random(n) < 0.3, "electric", "classic"),
    })


trips = make_trips()
small = trips.astype({"rider": "category", "bike": "category",
                      "start_station": "int16",
                      "duration_min": "float32"})
small.to_parquet("trips_small.parquet", index=False)

# %% Exercise 22.1
by_hour = (pl.scan_parquet("trips_small.parquet")
           .group_by(pl.col("start_time").dt.hour().alias("hour"))
           .agg((pl.col("bike") == "electric").mean().round(3)
                .alias("ebike"), pl.len().alias("rides"))
           .sort("hour")
           .collect())
print(by_hour.head(4))
print(by_hour["ebike"].min(), by_hour["ebike"].max())

# %% Exercise 22.2
print(duckdb.sql("""
    SELECT start_station,
           ROUND(MEDIAN(duration_min)::DOUBLE, 1) AS median_min,
           COUNT(*) AS rides
    FROM 'trips_small.parquet'
    WHERE rider = 'casual'
    GROUP BY start_station
    ORDER BY median_min DESC
    LIMIT 5
""").df())

# %% Exercise 22.3
base = trips.memory_usage(deep=True).sum() / 1e6
for col in ["rider", "bike"]:
    one = trips.astype({col: "category"})
    saved = base - one.memory_usage(deep=True).sum() / 1e6
    print(f"{col}: saves {saved:.0f} MB")

# %% Exercise 22.4
month = small["start_time"].dt.month
start = time.perf_counter()
slow = small.groupby(month)["rider"].agg(lambda r: (r == "casual")
                                         .mean())
t_slow = time.perf_counter() - start
start = time.perf_counter()
fast = (small["rider"] == "casual").groupby(month).mean()
t_fast = time.perf_counter() - start
print(f"lambda {t_slow:.2f} s, vectorized {t_fast:.2f} s, same: "
      f"{np.allclose(slow, fast)}")

# %% Exercise 22.5
july = (pl.scan_parquet("trips_small.parquet")
        .filter(pl.col("start_time").dt.month() == 7)
        .group_by(pl.col("start_time").dt.date().alias("day"))
        .agg(pl.len().alias("rides"))
        .sort("rides", descending=True))
for line in july.explain().splitlines()[-3:]:
    print(line.strip())
print(july.collect().head(1))

# %% Exercise 22.6
print(duckdb.sql("""
    SELECT CASE WHEN w.precip_mm = 0 THEN 'dry'
                WHEN w.precip_mm > 5 THEN 'heavy rain'
                ELSE 'light rain' END AS weather,
           COUNT(*) AS rides, ROUND(AVG(t.duration_min), 2) AS avg_min
    FROM 'trips_small.parquet' AS t
    JOIN read_csv('data/bike_daily.csv') AS w
      ON CAST(t.start_time AS DATE) = w.date
    GROUP BY weather ORDER BY weather
""").df())

# %% Exercise 22.7
import shutil

shutil.rmtree("rides_3y", ignore_errors=True)
for year in [2023, 2024, 2025]:
    t = make_trips(year, seed=year, scale=3)
    t.assign(year=t["start_time"].dt.year,
             month=t["start_time"].dt.month).to_parquet(
        "rides_3y", partition_cols=["year", "month"], index=False)
path = "read_parquet('rides_3y/*/*/*.parquet', hive_partitioning=true)"
for where in ["month = 6", "month(start_time) = 6"]:
    start = time.perf_counter()
    res = duckdb.sql(f"SELECT year, COUNT(*) AS rides FROM {path} "
                     f"WHERE {where} GROUP BY year ORDER BY year").df()
    print(f"{where:<22} {time.perf_counter() - start:.2f} s",
          res["rides"].tolist())
