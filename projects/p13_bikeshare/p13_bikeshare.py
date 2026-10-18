"""Project 13 (Advanced): Bike-Share Ridership at Scale

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p13_bikeshare.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and make the data
import time
from pathlib import Path

import make_rides

start = time.perf_counter()
total = make_rides.main()
files = sorted(Path("rides").glob("*.parquet"))
size = sum(f.stat().st_size for f in files) / 1e6
print(f"{total:,} rides in {len(files)} files, {size:.0f} MB, "
      f"made in {time.perf_counter() - start:.0f} s")

# %% Step 2: Look before loading
import polars as pl

pl.Config.set_tbl_formatting("ASCII_MARKDOWN")
pl.Config.set_tbl_hide_column_data_types(True)
rides = pl.scan_parquet("rides/*.parquet")
for name, dtype in rides.collect_schema().items():
    print(f"{name:<14} {dtype}")
print(f"{rides.select(pl.len()).collect().item():,} rides")

# %% Step 2: Look before loading
stations = pl.read_csv("stations.csv")
print(stations.select("station_id", "name", "kind", "capacity")
      .head(3))
print(stations.group_by("kind").len().sort("kind"))

# %% Step 3: Check the data, lazily
minutes = (pl.col("end_time") - pl.col("start_time")
           ).dt.total_seconds() / 60
known = stations["station_id"].to_list()
checks = rides.select(
    negative=(minutes < 0).sum(),
    over_a_day=(minutes > 24 * 60).sum(),
    unknown_start=(~pl.col("start_station").is_in(known)).sum(),
    unknown_end=(~pl.col("end_station").is_in(known)).sum(),
    duplicate_ids=pl.len() - pl.col("ride_id").n_unique(),
).collect()
print(checks)

# %% Step 3: Check the data, lazily
print(rides.filter(~pl.col("start_station").is_in(known))
      .group_by("start_station").len().collect())

# %% Step 3: Check the data, lazily
valid = (rides
         .with_columns(minutes=minutes)
         .filter(pl.col("minutes").is_between(1, 24 * 60),
                 pl.col("start_station").is_in(known)))
print(f"{valid.select(pl.len()).collect().item():,} valid rides")

# %% Step 4: Who rides when?
start = pl.col("start_time")
hourly = (valid
          .with_columns(hour=start.dt.hour(),
                        weekend=start.dt.weekday() >= 6)
          .group_by("weekend", "rider", "hour")
          .agg(rides=pl.len())
          .collect())
days = {False: 261, True: 104}         # weekdays and weekend days
day_count = pl.col("weekend").replace_strict(days)
hourly = hourly.with_columns(
    per_day=(pl.col("rides") / day_count).round(1))
print(hourly.sort("weekend", "rider", "hour").head(3))

# %% Step 4: Who rides when?
import matplotlib.pyplot as plt

hourly_pd = hourly.to_pandas()
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), sharey=True)
for ax, weekend in zip(axes, [False, True]):
    part = hourly_pd[hourly_pd["weekend"] == weekend]
    for rider, color in [("member", "#1d5c8c"),
                         ("casual", "#c0582b")]:
        line = part[part["rider"] == rider].sort_values("hour")
        ax.plot(line["hour"], line["per_day"], color=color,
                label=rider)
    ax.set_title("Weekend" if weekend else "Weekday", fontsize=9)
    ax.set_xticks([6, 12, 18], ["6:00", "12:00", "18:00"])
axes[0].set_ylabel("Rides per hour")
axes[0].legend(frameon=False)
plt.show()

# %% Step 5: Stations with SQL
import duckdb

CLEAN = """
    SELECT *, epoch(end_time - start_time) / 60 AS minutes
    FROM 'rides/*.parquet'
    WHERE start_station <> 999
      AND epoch(end_time - start_time) BETWEEN 60 AND 86400
"""
duckdb.sql(f"CREATE VIEW valid AS {CLEAN}")
duckdb.sql("CREATE VIEW stations AS SELECT * FROM 'stations.csv'")
print(duckdb.sql("SELECT COUNT(*) AS rides FROM valid").fetchone())

# %% Step 5: Stations with SQL
print(duckdb.sql("""
    SELECT s.name, s.kind, COUNT(*) AS departures
    FROM valid AS v JOIN stations AS s
      ON v.start_station = s.station_id
    GROUP BY s.name, s.kind
    ORDER BY departures DESC
    LIMIT 5
""").df())

# %% Step 6: The rebalancing problem
flows = duckdb.sql("""
    WITH moves AS (
        SELECT start_station AS station, start_time AS t, -1 AS change
        FROM valid
        UNION ALL
        SELECT end_station, end_time, 1 FROM valid
    )
    SELECT s.kind, hour(t) AS hour, SUM(change) / 261 AS net_per_day
    FROM moves JOIN stations AS s ON moves.station = s.station_id
    WHERE dayofweek(t) BETWEEN 1 AND 5
    GROUP BY s.kind, hour
    ORDER BY s.kind, hour
""").df()
print(flows.pivot(index="kind", columns="hour",
                  values="net_per_day").loc[:, 7:10].round(0))

# %% Step 6: The rebalancing problem
grid = flows.pivot(index="kind", columns="hour", values="net_per_day")
fig, ax = plt.subplots(figsize=(6.6, 1.9))
limit = grid.abs().max().max()
im = ax.imshow(grid, cmap="RdBu", vmin=-limit, vmax=limit,
               aspect="auto")
ax.grid(False)
ax.set_yticks(range(3), grid.index)
ax.set_xticks(range(0, len(grid.columns), 3), grid.columns[::3])
ax.set_xlabel("Hour of the day (weekdays)")
fig.colorbar(im, ax=ax, label="Bikes gained per day")
plt.show()

# %% Step 6: The rebalancing problem
drain = duckdb.sql("""
    WITH moves AS (
        SELECT start_station AS station, start_time AS t, -1 AS change
        FROM valid UNION ALL
        SELECT end_station, end_time, 1 FROM valid)
    SELECT s.name, s.capacity, SUM(change) / 261 AS net_per_morning
    FROM moves JOIN stations AS s ON moves.station = s.station_id
    WHERE dayofweek(t) BETWEEN 1 AND 5 AND hour(t) BETWEEN 6 AND 9
      AND s.kind = 'residential'
    GROUP BY s.name, s.capacity ORDER BY net_per_morning LIMIT 3
""").df()
print(drain.round(1))

# %% Step 7: How long are rides?
lengths = (valid.group_by("rider", "bike")
           .agg(rides=pl.len(),
                median=pl.col("minutes").median(),
                p90=pl.col("minutes").quantile(0.9))
           .sort("rider", "bike")
           .collect())
print(lengths.with_columns(pl.col("median", "p90").round(1)))

# %% Step 8: Three tools, one question
import pandas as pd

def with_pandas():
    df = pd.read_parquet("rides", columns=["start_time", "end_time",
                                           "start_station", "rider"])
    mins = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60
    ok = mins.between(1, 24 * 60) & (df["start_station"] != 999)
    df = df[ok]
    return df.groupby([df["start_time"].dt.month, "rider"]).size()

def with_polars():
    return (valid.group_by(pl.col("start_time").dt.month(), "rider")
            .len().collect())

def with_duckdb():
    return duckdb.sql("""SELECT month(start_time), rider, COUNT(*)
                         FROM valid GROUP BY ALL""").df()

# %% Step 8: Three tools, one question
for f in [with_pandas, with_polars, with_duckdb]:
    start = time.perf_counter()
    result = f()
    print(f"{f.__name__:<12} {time.perf_counter() - start:5.2f} s "
          f"{len(result)} groups")

# %% Step 9: Save the results
out = Path("summary")
out.mkdir(exist_ok=True)
hourly.write_parquet(out / "hourly_profile.parquet")
lengths.write_parquet(out / "ride_lengths.parquet")
flows.to_parquet(out / "net_flow_by_kind.parquet", index=False)
drain.to_parquet(out / "draining_stations.parquet", index=False)
print(*sorted(p.name for p in out.iterdir()), sep="\n")
