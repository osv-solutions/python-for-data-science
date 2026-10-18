"""Make a year of rides for Project 13 of "Python for Data Science".

Riverton Bikes is a fictional bike-share system with 360 stations. Like real
systems, it publishes one file of rides per month. This script writes them,
for 2025, to rides/2025-01.parquet ... rides/2025-12.parquet, and the station
list to stations.csv. The number of rides each day follows the daily totals
in data/bike_daily.csv (Chapter 21), times nine.

The rides have the flaws of real exports: a few end before they start, a few
last more than a day (bikes that were lost or stolen), and some come from
station 999, the repair shop, which isn't a public station.

Usage: python make_rides.py          (takes a few seconds)
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SCALE = 9


def make_stations(rng):
    kinds = ["downtown"] * 90 + ["residential"] * 180 + ["park"] * 90
    hoods = {"downtown": ["Downtown", "Market Square", "Station Quarter"],
             "residential": ["Northside", "Eastwood", "Hillcrest",
                             "Westgate", "Southbank", "Elm Park"],
             "park": ["Riverfront", "Lakeside", "Botanic Gardens"]}
    streets = ["Main", "Oak", "River", "Market", "Union", "Lake", "Grant",
               "Liberty", "Elm", "Bridge", "Mill", "Park", "Church",
               "Water", "Spring", "Center", "Maple", "High", "Chestnut",
               "Walnut"]
    corners = [(a, b) for a in streets for b in streets if a != b]
    order = rng.permutation(len(corners))
    rows = []
    for i, kind in enumerate(kinds, start=1):
        a, b = corners[order[i]]
        lat = 41.50 + {"downtown": 0, "residential": 0.025,
                       "park": -0.015}[kind] + rng.normal(0, 0.01)
        lon = -81.69 + rng.normal(0, 0.015 if kind == "downtown" else 0.03)
        rows.append({"station_id": i, "name": f"{a} St & {b} Ave",
                     "neighborhood": rng.choice(hoods[kind]),
                     "kind": kind, "capacity": int(rng.choice(
                         [15, 19, 23, 27, 31] if kind == "downtown"
                         else [11, 15, 19])),
                     "lat": round(lat, 5), "lon": round(lon, 5)})
    return pd.DataFrame(rows)


def pick(rng, ids, weights, n):
    return rng.choice(ids, n, p=weights / weights.sum())


def make_month(days, stations, rng):
    """All rides of the days in `days` (a slice of bike_daily.csv)."""
    n = int(days["rides"].sum() * SCALE)
    day = rng.choice(days["date"].to_numpy(), n,
                     p=days["rides"] / days["rides"].sum())
    weekend = pd.DatetimeIndex(day).dayofweek >= 5
    casual = rng.random(n) < np.where(weekend, 0.5, 0.25)
    commute = ~casual & ~weekend & (rng.random(n) < 0.8)
    hour = np.where(commute, rng.choice([8, 17.5], n, p=[0.45, 0.55])
                    + rng.normal(0, 1.2, n),
                    np.where(casual, rng.normal(14.5, 3, n),
                             rng.normal(12.5, 3.8, n)))
    hour = hour.clip(5, 23.99)
    morning = hour < 12
    pop = 1 / np.arange(1, len(stations) + 1) ** 0.6
    rng.shuffle(pop)
    ids = stations["station_id"].to_numpy()
    kind = stations["kind"].to_numpy()
    w = {k: pop * np.where(kind == k, 1.0, 0.12) for k in
         ["downtown", "residential", "park"]}
    w["any"] = pop
    # commuters ride from home to downtown in the morning, back at night
    start = np.where(commute & morning, pick(rng, ids, w["residential"], n),
                     np.where(commute, pick(rng, ids, w["downtown"], n),
                              np.where(casual, pick(rng, ids, w["park"], n),
                                       pick(rng, ids, w["any"], n))))
    end = np.where(commute & morning, pick(rng, ids, w["downtown"], n),
                   np.where(commute, pick(rng, ids, w["residential"], n),
                            pick(rng, ids, w["any"], n)))
    loop = casual & (rng.random(n) < 0.18)        # round trips
    last = len(stations)
    end = np.where(loop, start, np.where(end == start, end % last + 1, end))
    minutes = np.where(casual, rng.gamma(2.2, 10, n), rng.gamma(2.4, 5, n))
    start_time = (pd.to_datetime(day)
                  + pd.to_timedelta((hour * 3600).astype(int), "s"))
    end_time = start_time + pd.to_timedelta((minutes * 60).astype(int), "s")
    rides = pd.DataFrame({
        "start_time": start_time, "end_time": end_time,
        "start_station": start.astype("int16"),
        "end_station": end.astype("int16"),
        "rider": np.where(casual, "casual", "member"),
        "bike": np.where(rng.random(n) < 0.32, "electric", "classic")})
    # the flaws of a real export
    bad = rng.random(n)
    swap = bad < 0.0004                       # clock errors
    rides.loc[swap, "end_time"] = (rides.loc[swap, "start_time"]
                                   - pd.Timedelta(minutes=3))
    lost = (bad >= 0.0004) & (bad < 0.0006)   # never docked for a day
    rides.loc[lost, "end_time"] += pd.Timedelta(hours=30)
    shop = (bad >= 0.0006) & (bad < 0.0016)   # repair shop moves
    rides.loc[shop, "start_station"] = 999
    return rides.sort_values("start_time", ignore_index=True)


def main(folder=HERE):
    rng = np.random.default_rng(2025)
    stations = make_stations(rng)
    stations.to_csv(folder / "stations.csv", index=False)
    daily = pd.read_csv(folder / "data/bike_daily.csv",
                        parse_dates=["date"])
    daily = daily[daily["date"].dt.year == 2025]
    out = folder / "rides"
    out.mkdir(exist_ok=True)
    total, first = 0, 1
    for month, days in daily.groupby(daily["date"].dt.month):
        rides = make_month(days, stations, rng)
        rides.insert(0, "ride_id", np.arange(first, first + len(rides)))
        first += len(rides)
        rides.to_parquet(out / f"2025-{month:02d}.parquet", index=False)
        total += len(rides)
    return total


if __name__ == "__main__":
    print(f"{main():,} rides written to rides/")
