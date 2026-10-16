# Solutions: Chapter 22, Faster and Bigger Data: Polars and DuckDB

Worked solutions to the exercises at the end of Chapter 22 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch22_solutions.ipynb`](ch22_solutions.ipynb) or the script `ch22_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

The solutions start from the chapter's five and a half million rides, as `trips` and with smaller dtypes as `small`, saved as `trips_small.parquet`. `make_trips` gained `year` and `scale` arguments for exercise 7.

## Exercise 22.1

*With Polars, find the share of rides on electric bikes for each hour of the day, sorted by hour.*

```python
by_hour = (pl.scan_parquet("trips_small.parquet")
           .group_by(pl.col("start_time").dt.hour().alias("hour"))
           .agg((pl.col("bike") == "electric").mean().round(3)
                .alias("ebike"), pl.len().alias("rides"))
           .sort("hour")
           .collect())
print(by_hour.head(4))
print(by_hour["ebike"].min(), by_hour["ebike"].max())
```

Output:

```text
shape: (4, 3)
| hour | ebike | rides |
|------|-------|-------|
| 0    | 0.2   | 10    |
| 1    | 0.304 | 69    |
| 2    | 0.282 | 811   |
| 3    | 0.3   | 6812  |
0.2 0.304
```

A lazy query reads only the two columns it needs. The share is the mean of a Boolean expression. It is close to 30% at every hour, as the data was built, except in the quiet small hours, where a handful of rides makes the share jumpy (0.2 at midnight is 2 of 10 rides); in a real system, a pattern here, such as more electric bikes in the evening, would be worth a closer look.

## Exercise 22.2

*With DuckDB, find the five stations with the longest median casual ride, querying the Parquet file directly.*

```python
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
```

Output:

```text
   start_station  median_min  rides
0             98        17.4   4903
1             79        17.3   5844
2             87        17.3   5509
3             57        17.2   7663
4             93        17.2   5159
```

`MEDIAN` is one of DuckDB's aggregate functions, and `::DOUBLE` converts the `float32` durations to ordinary floats before rounding, so they print cleanly. The five medians are within a fraction of a minute of each other and come from quieter stations: rides were generated the same way at every station, so this ranking is pure chance, and smaller stations, with fewer rides, vary more (Chapter 19). Ranking by a statistic without looking at the counts behind it is a common trap; a minimum count, such as `HAVING COUNT(*) >= 10000`, or a confidence interval per station, makes such rankings fairer.

## Exercise 22.3

*Measure how much memory `trips` saves if only `rider` becomes a category, and if only `bike` does. Which column gains more, and why?*

```python
base = trips.memory_usage(deep=True).sum() / 1e6
for col in ["rider", "bike"]:
    one = trips.astype({col: "category"})
    saved = base - one.memory_usage(deep=True).sum() / 1e6
    print(f"{col}: saves {saved:.0f} MB")
```

Output:

```text
rider: saves 72 MB
bike: saves 79 MB
```

`bike` saves a little more, because its labels, `classic` and `electric`, are longer than `member` and `casual`, so each stored string costs more. As categories, both become one byte per row plus two labels, whatever the label length.

## Exercise 22.4

*Rewrite the monthly casual share in pandas without a `lambda`, and compare its time with the `lambda` version.*

```python
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
```

Output:

```text
lambda 0.20 s, vectorized 0.08 s, same: True
```

The vectorized version computes the Boolean column once for all rows, in compiled code, and then takes a grouped mean, which pandas does very fast. The `lambda` version calls Python once per group and compares strings group by group. With only 12 groups the gap is modest; with thousands of groups, such as one per station and day, it grows to many times.

## Exercise 22.5

*With a Polars lazy query, find the number of rides per day of July and the busiest day, and print the optimized plan.*

```python
july = (pl.scan_parquet("trips_small.parquet")
        .filter(pl.col("start_time").dt.month() == 7)
        .group_by(pl.col("start_time").dt.date().alias("day"))
        .agg(pl.len().alias("rides"))
        .sort("rides", descending=True))
for line in july.explain().splitlines()[-3:]:
    print(line.strip())
print(july.collect().head(1))
```

Output:

```text
PROJECT 1/5 COLUMNS
SELECTION: (col("start_time").dt.month() == 7)
ESTIMATED ROWS: 5555709
shape: (1, 2)
| day        | rides |
|------------|-------|
| 2025-07-25 | 24916 |
```

The plan reads only `start_time`, one of five columns, and applies the month filter during the scan. The busiest July day is July 25. In Chapter 21's daily totals, the busiest July day was July 15: the generated rides follow those totals only on average, so days with similar totals can swap places by chance.

## Exercise 22.6

*Use DuckDB to join the rides with the 2025 daily weather from `bike_daily.csv`, and compute the average ride length on dry days and on days with more than 5 mm of rain.*

```python
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
```

Output:

```text
      weather    rides  avg_min
0         dry  4201008    13.64
1  heavy rain   497042    13.64
2  light rain   857659    13.62
```

`read_csv` reads the CSV file inside the query, and the join matches each ride's date with the day's weather. Rainy days have far fewer rides, as Chapter 21 found, but the rides that do happen are about as long: the generated rides don't model the weather's effect on length. In real data, this query is how you would check whether bad weather shortens rides.

## Exercise 22.7

*Make a dataset of three years of rides, partitioned by year and month, and time a query for the number of rides in each June with DuckDB, with and without the partition filter.*

```python
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
```

Output:

```text
month = 6              0.01 s [154381, 174132, 181924]
month(start_time) = 6  0.30 s [154381, 174132, 181924]
```

`scale=3` keeps the three years to a manageable size. Both queries count the same June rides. Filtering on the partition column `month` lets DuckDB open only the three June folders; filtering on `month(start_time)` must read the timestamps of every file. The partition filter is about 30 times faster here, and on real datasets of hundreds of files, the difference is between seconds and minutes.
