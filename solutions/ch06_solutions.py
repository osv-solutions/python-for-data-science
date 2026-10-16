"""Solutions to the Chapter 6 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch06_solutions.py

The explanations are in ch06_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import os
import time
from pathlib import Path
import pandas as pd
import practice_web
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

BASE = practice_web.start()
Path(".env").write_text("BIKE_API_KEY=demo-key-2026\n", encoding="utf-8")
load_dotenv()
session = requests.Session()
session.headers.update({"X-API-Key": os.environ["BIKE_API_KEY"]})
retry = Retry(total=4, backoff_factor=0.5,
              status_forcelist=[429, 500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retry))

# %% Exercise 6.1
url = f"{BASE}/api/v1/stations"
first = requests.get(url, params={"per_page": 8}, timeout=10).json()
records = list(first["data"])
for page in range(2, first["meta"]["pages"] + 1):
    body = requests.get(url, params={"per_page": 8, "page": page},
                        timeout=10).json()
    records += body["data"]
stations = pd.json_normalize(records)
stations.columns = [c.split(".")[-1] for c in stations.columns]
print(first["meta"]["pages"], "pages,", len(stations), "stations,",
      stations["station_id"].is_unique)

# %% Exercise 6.2
closed = stations[~stations["is_renting"]]
print(closed[["station_id", "name"]].to_string(index=False))
empty = stations["docks_available"].sum() / stations["capacity"].sum()
print(f"empty docks: {empty:.1%}")

# %% Exercise 6.3
def get_json(session, url, **params):
    """GET a URL with a timeout, check the status, return its JSON."""
    response = session.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def get_trips(day):
    """Return all trips of one day as a DataFrame."""
    url = f"{BASE}/api/v1/trips"
    first = get_json(session, url, date=day)
    rows = list(first["data"])
    for n in range(2, first["meta"]["pages"] + 1):
        rows += get_json(session, url, date=day, page=n)["data"]
    return pd.DataFrame(rows).assign(
        started_at=lambda d: pd.to_datetime(d["started_at"]))

print(len(get_trips("2026-06-01")))

# %% Exercise 6.4
days = pd.date_range("2026-06-01", "2026-06-07")
week = pd.concat([get_trips(d.date().isoformat()).assign(date=d)
                  for d in days], ignore_index=True)
per_day = week.groupby("date").size()
weekend = per_day.index.dayofweek >= 5
print(per_day.to_string())
print("weekday mean:", per_day[~weekend].mean().round(1),
      " weekend mean:", per_day[weekend].mean().round(1))

# %% Exercise 6.5
share = (week.assign(electric=week["bike"].eq("electric"))
         .groupby("rider")["electric"].mean())
print(share.round(3))

# %% Exercise 6.6
import json

RAW = Path("raw")
RAW.mkdir(exist_ok=True)
for d in days:
    day = d.date().isoformat()
    url = f"{BASE}/api/v1/trips"
    first = get_json(session, url, date=day)
    rows = list(first["data"])
    for n in range(2, first["meta"]["pages"] + 1):
        rows += get_json(session, url, date=day, page=n)["data"]
    (RAW / f"trips_{day}.json").write_text(json.dumps(rows))
print(sorted(p.name for p in RAW.glob("*.json"))[:2])

# %% Exercise 6.6
def week_from_files(folder):
    frames = []
    for path in sorted(Path(folder).glob("trips_*.json")):
        day = path.stem.removeprefix("trips_")
        rows = json.loads(path.read_text())
        frames.append(pd.DataFrame(rows).assign(date=day))
    return pd.concat(frames, ignore_index=True)

rebuilt = week_from_files("raw")
print(len(rebuilt) == len(week), rebuilt["date"].nunique())

# %% Exercise 6.7
from collections import deque

def throttled_calls(n, limit=3, window=2.0):
    recent = deque(maxlen=limit)
    codes = []
    for _ in range(n):
        if len(recent) == limit:
            wait = recent[0] + window - time.monotonic()
            if wait > 0:
                time.sleep(wait + 0.05)
        recent.append(time.monotonic())
        r = requests.get(f"{BASE}/api/v1/limited", timeout=10)
        codes.append(r.status_code)
    return codes

# %% Exercise 6.7
time.sleep(2)
start = time.monotonic()
print(throttled_calls(10), f"{time.monotonic() - start:.0f} s")
