# Solutions: Chapter 6, Data from REST APIs

Worked solutions to the exercises at the end of Chapter 6 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch06_solutions.ipynb`](ch06_solutions.ipynb) or the script `ch06_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

## Exercise 6.1

*Fetch the stations with `per_page=8` using page numbers, and check that you get the same 40 stations.*

```python
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
```

Output:

```text
5 pages, 40 stations, True
```

The first response tells us there are 5 pages of 8; the loop fetches pages 2 to 5. All 40 station IDs are unique, the same set that `fetch_all` collects by following the next links.

## Exercise 6.2

*Find the stations that are not renting, and the share of all docks that are empty.*

```python
closed = stations[~stations["is_renting"]]
print(closed[["station_id", "name"]].to_string(index=False))
empty = stations["docks_available"].sum() / stations["capacity"].sum()
print(f"empty docks: {empty:.1%}")
```

Output:

```text
station_id                      name
      S012 Smallman St & River Trail
empty docks: 57.5%
```

`~` negates the Boolean column, keeping the stations that are not renting. Empty docks are docks without a bike, so their share is the sum of `docks_available` over the total capacity. The format `:.1%` prints a fraction as a percentage with one decimal.

## Exercise 6.3

*Write `get_json(session, url, **params)` and rewrite `get_trips` with it.*

```python
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
```

Output:

```text
265
```

`**params` collects the keyword arguments, such as `date=day`, into a dictionary that becomes the query string. The helper puts the timeout and the status check in one place, so no request can forget them.

## Exercise 6.4

*Download the trips of June 1 to 7, 2026, and compare weekdays with weekends.*

```python
days = pd.date_range("2026-06-01", "2026-06-07")
week = pd.concat([get_trips(d.date().isoformat()).assign(date=d)
                  for d in days], ignore_index=True)
per_day = week.groupby("date").size()
weekend = per_day.index.dayofweek >= 5
print(per_day.to_string())
print("weekday mean:", per_day[~weekend].mean().round(1),
      " weekend mean:", per_day[weekend].mean().round(1))
```

Output:

```text
date
2026-06-01    265
2026-06-02    270
2026-06-03    313
2026-06-04    272
2026-06-05    316
2026-06-06    353
2026-06-07    391
weekday mean: 287.2  weekend mean: 372.0
```

`pd.date_range` makes the seven dates. `pd.concat` stacks the seven daily tables (Chapter 13), each with its date added. `dayofweek` is 5 for Saturday and 6 for Sunday, so the mask separates the weekend; in this city, weekends are busier.

## Exercise 6.5

*Find the share of trips on electric bikes for members and for casual riders.*

```python
share = (week.assign(electric=week["bike"].eq("electric"))
         .groupby("rider")["electric"].mean())
print(share.round(3))
```

Output:

```text
rider
casual    0.319
member    0.325
Name: electric, dtype: float64
```

The mean of a Boolean column is a share (Chapter 2). Here the shares are about the same for both groups.

## Exercise 6.6

*Save each day's raw JSON to `raw/trips_<date>.json`, then rebuild the week from the files alone.*

```python
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
```

Output:

```text
['trips_2026-06-01.json', 'trips_2026-06-02.json']
```

The raw rows are saved exactly as the API sent them. Rebuilding needs no network at all:

```python
def week_from_files(folder):
    frames = []
    for path in sorted(Path(folder).glob("trips_*.json")):
        day = path.stem.removeprefix("trips_")
        rows = json.loads(path.read_text())
        frames.append(pd.DataFrame(rows).assign(date=day))
    return pd.concat(frames, ignore_index=True)

rebuilt = week_from_files("raw")
print(len(rebuilt) == len(week), rebuilt["date"].nunique())
```

Output:

```text
True 7
```

The file names carry the dates, so `path.stem` (the name without `.json`) gives each table its `date` column back. The rebuilt table has the same number of trips as the downloaded one.

## Exercise 6.7

*Call the `limited` endpoint 10 times without retries and never receive a 429.*

The endpoint allows 3 requests in any 2 seconds. Keeping the times of the recent requests, the program waits before each new request until the oldest of the last three is more than 2 seconds old:

```python
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
```

The `time.sleep(2)` first lets the limit window from the earlier examples expire:

```python
time.sleep(2)
start = time.monotonic()
print(throttled_calls(10), f"{time.monotonic() - start:.0f} s")
```

Output:

```text
[200, 200, 200, 200, 200, 200, 200, 200, 200, 200] 6 s
```

A `deque` with `maxlen=3` keeps only the last three request times, dropping the oldest automatically. Before each request beyond the third, the program sleeps until the oldest of those three falls out of the 2-second window, plus a small margin. All ten calls succeed, in about six seconds: the fastest pace the rate limit allows.
