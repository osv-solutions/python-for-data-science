"""Chapter 22: Faster and Bigger Data: Polars and DuckDB

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch22_polars_duckdb.py

or open the notebook and run the cells in order.
"""

# %% 22.1 Five million rides
import time

import numpy as np
import pandas as pd

daily = pd.read_csv("data/bike_daily.csv", parse_dates=["date"])
days = daily[daily["date"].dt.year == 2025]
stations = np.arange(1, 121)
popularity = 1 / stations ** 0.8
print(len(days), "days of 2025,", days["rides"].sum(), "rides")

# %% 22.1 Five million rides
def make_trips(seed=22):
    rng = np.random.default_rng(seed)
    n = days["rides"].sum() * 9             # a city nine times busier
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

# %% 22.1 Five million rides
start = time.perf_counter()
trips = make_trips()
trips.to_parquet("trips_2025.parquet", index=False)
print(f"{len(trips):,} rides in {time.perf_counter() - start:.1f} s")

# %% 22.2 How big is too big?
mb = trips.memory_usage(deep=True) / 1e6
print(mb.round(1).to_string())
print(f"total {mb.sum():.0f} MB")

# %% 22.2 How big is too big?
small = trips.astype({"rider": "category", "bike": "category",
                      "start_station": "int16",
                      "duration_min": "float32"})
mb_small = small.memory_usage(deep=True).sum() / 1e6
print(f"{mb.sum():.0f} MB -> {mb_small:.0f} MB")

# %% 22.2 How big is too big?
small.to_parquet("trips_small.parquet", index=False)
start = time.perf_counter()
part = pd.read_parquet("trips_small.parquet",
                       columns=["rider", "duration_min"])
print(f"2 columns read in {time.perf_counter() - start:.2f} s")
start = time.perf_counter()
print(part.groupby("rider", observed=True)["duration_min"].median())
print(f"groupby in {time.perf_counter() - start:.2f} s")

# %% 22.3 Polars
import polars as pl

pl.Config.set_tbl_formatting("ASCII_MARKDOWN")
pl.Config.set_tbl_hide_column_data_types(True)
rides = pl.read_parquet("trips_small.parquet")
print(rides.shape)
print(rides.head(3))

# %% 22.3 Polars
summary = (rides
           .filter(pl.col("duration_min") < 120)
           .with_columns(pl.col("start_time").dt.hour().alias("hour"))
           .group_by("rider")
           .agg(pl.len().alias("rides"),
                pl.col("duration_min").median().alias("median_min"),
                (pl.col("bike") == "electric").mean().alias("ebike"))
           .sort("rider"))
print(summary)

# %% 22.3 Polars
def timed(label, func):
    start = time.perf_counter()
    result = func()
    print(f"{label:<7} {time.perf_counter() - start:.2f} s")
    return result


pd_res = timed("pandas", lambda: small.groupby(
    [small["start_station"], small["start_time"].dt.hour],
    observed=True)["duration_min"].agg(["count", "mean", "median"]))
pl_res = timed("polars", lambda: rides.group_by(
    "start_station", pl.col("start_time").dt.hour()).agg(
    pl.len(), pl.col("duration_min").mean().alias("mean"),
    pl.col("duration_min").median().alias("median")))
print(len(pd_res), len(pl_res), "groups")

# %% 22.4 Lazy queries
query = (pl.scan_parquet("trips_small.parquet")
         .filter(pl.col("rider") == "casual")
         .group_by("start_station")
         .agg(pl.len().alias("rides"),
              pl.col("duration_min").mean().round(1).alias("avg_min"))
         .sort("rides", descending=True)
         .head(3))
for line in query.explain().splitlines()[-4:]:
    print(line.strip())
print(query.collect())

# %% 22.5 DuckDB: SQL on files
import duckdb

result = duckdb.sql("""
    SELECT rider, bike, COUNT(*) AS rides,
           ROUND(AVG(duration_min), 1) AS avg_min
    FROM 'trips_small.parquet'
    GROUP BY rider, bike
    ORDER BY rider, bike
""").df()
print(result)

# %% 22.5 DuckDB: SQL on files
busy = duckdb.sql("""
    SELECT start_station, COUNT(*) AS rides
    FROM small
    WHERE hour(start_time) BETWEEN 7 AND 9 AND rider = 'member'
    GROUP BY start_station ORDER BY rides DESC LIMIT 3
""").df()
print(busy)

# %% 22.5 DuckDB: SQL on files
import shutil
from pathlib import Path

shutil.rmtree("rides_by_month", ignore_errors=True)
small.assign(month=small["start_time"].dt.month).to_parquet(
    "rides_by_month", partition_cols=["month"], index=False)

print(sorted(p.name for p in Path("rides_by_month").iterdir())[:3])
july = duckdb.sql("""
    SELECT COUNT(*) AS rides FROM read_parquet(
        'rides_by_month/*/*.parquet', hive_partitioning = true)
    WHERE month = 7
""").fetchone()[0]
print(f"{july:,} rides in July")

# %% 22.7 Putting it together: one question, three tools
pd_month = timed("pandas", lambda: small.groupby(
    small["start_time"].dt.month).agg(
    casual=("rider", lambda r: (r == "casual").mean()),
    median_min=("duration_min", "median")))
pl_month = timed("polars", lambda: pl.scan_parquet(
    "trips_small.parquet").group_by(
    pl.col("start_time").dt.month().alias("month")).agg(
    (pl.col("rider") == "casual").mean().alias("casual"),
    pl.col("duration_min").median().alias("median_min")).sort(
    "month").collect())
db_month = timed("duckdb", lambda: duckdb.sql("""
    SELECT month(start_time) AS month,
           AVG((rider = 'casual')::INT) AS casual,
           MEDIAN(duration_min) AS median_min
    FROM 'trips_small.parquet' GROUP BY month ORDER BY month""").df())

# %% 22.7 Putting it together: one question, three tools
check = pd.DataFrame({"pandas": pd_month["casual"].to_numpy(),
                      "polars": pl_month["casual"].to_numpy(),
                      "duckdb": db_month["casual"].to_numpy()},
                     index=range(1, 13))
print(check.round(4).head(3))
print("all equal:", np.allclose(check["pandas"], check["polars"])
      and np.allclose(check["pandas"], check["duckdb"]))
