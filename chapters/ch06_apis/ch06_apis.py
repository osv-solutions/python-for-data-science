"""Chapter 6: Data from REST APIs

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch06_apis.py

or open the notebook and run the cells in order.
"""

# %% 6.2 A practice API
import practice_web

BASE = practice_web.start()
print(BASE)

# %% 6.3 Your first requests
import requests

response = requests.get(f"{BASE}/api/v1/stations", timeout=10)
print(response.status_code, response.reason)
print(response.headers["Content-Type"])
print(response.text[:62])

# %% 6.3 Your first requests
from pprint import pprint

response = requests.get(f"{BASE}/api/v1/stations",
                        params={"page": 1, "per_page": 3}, timeout=10)
print(response.url)
body = response.json()
print(list(body))
print(body["meta"])
pprint(body["data"][0], width=60)

# %% 6.3 Your first requests
missing = requests.get(f"{BASE}/api/v1/bicycles", timeout=10)
print(missing.status_code, missing.json())
try:
    missing.raise_for_status()
except requests.HTTPError as err:
    print("raised", type(err).__name__, "for", err.response.url)

# %% 6.4 From JSON to a DataFrame
import pandas as pd

stations = pd.json_normalize(body["data"])
print("\n".join(stations.columns))

# %% 6.4 From JSON to a DataFrame
stations.columns = [c.split(".")[-1] for c in stations.columns]
cols = ["station_id", "neighborhood", "capacity", "bikes_available"]
print(stations[cols])

# %% 6.5 Following pagination
def fetch_all(url, params=None, session=requests):
    """Follow the `links.next` URLs and return every record."""
    records = []
    while url:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        body = response.json()
        records.extend(body["data"])
        url = body["links"]["next"]
        params = None            # the next link already contains them
    return records

# %% 6.5 Following pagination
records = fetch_all(f"{BASE}/api/v1/stations", {"per_page": 15})
stations = pd.json_normalize(records)
stations.columns = [c.split(".")[-1] for c in stations.columns]
print(len(stations), stations["station_id"].is_unique)
print(stations.groupby("neighborhood")["capacity"].sum()
      .sort_values(ascending=False).head(3))

# %% 6.6 Sessions and API keys
response = requests.get(f"{BASE}/api/v1/trips",
                        params={"date": "2026-06-01"}, timeout=10)
print(response.status_code, response.json())

# %% 6.6 Sessions and API keys
from pathlib import Path

Path(".env").write_text("BIKE_API_KEY=demo-key-2026\n",
                        encoding="utf-8")

# %% 6.6 Sessions and API keys
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["BIKE_API_KEY"]
print(api_key[:4] + "…")

# %% 6.6 Sessions and API keys
session = requests.Session()
session.headers.update({"X-API-Key": api_key,
                        "User-Agent": "ds-book-examples/1.0"})
response = session.get(f"{BASE}/api/v1/trips",
                       params={"date": "2026-06-01", "page": 1},
                       timeout=10)
meta = response.json()["meta"]
print(response.status_code, meta["total"], "trips,", meta["pages"],
      "pages")

# %% 6.6 Sessions and API keys
pages = [session.get(f"{BASE}/api/v1/trips", timeout=10,
                     params={"date": "2026-06-01", "page": n}).json()
         for n in range(1, meta["pages"] + 1)]
trips = pd.DataFrame([t for p in pages for t in p["data"]])
print(len(trips) == meta["total"])
print(trips.head(3)[["trip_id", "started_at", "duration_min",
                     "rider", "bike"]])

# %% 6.7 When requests fail
try:
    requests.get(f"{BASE}/api/v1/slow", params={"seconds": 3},
                 timeout=1)
except requests.Timeout as err:
    print("gave up:", type(err).__name__)

# %% 6.7 When requests fail
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

retry = Retry(total=4, backoff_factor=0.5,
              status_forcelist=[429, 500, 502, 503, 504],
              allowed_methods=["GET"])
session.mount("http://", HTTPAdapter(max_retries=retry))
session.mount("https://", HTTPAdapter(max_retries=retry))
response = session.get(f"{BASE}/api/v1/flaky", timeout=10)
print(response.status_code, response.json())

# %% 6.7 When requests fail
statuses = [requests.get(f"{BASE}/api/v1/limited", timeout=10)
            for _ in range(5)]
print([r.status_code for r in statuses])
print(statuses[-1].headers["Retry-After"], statuses[-1].json())

# %% 6.7 When requests fail
import time

start = time.perf_counter()
codes = [session.get(f"{BASE}/api/v1/limited", timeout=10).status_code
         for _ in range(5)]
print(codes, f"{time.perf_counter() - start:.0f} seconds")

# %% 6.8 Caching responses
import requests_cache

cached = requests_cache.CachedSession("bike_cache",
                                      expire_after=3600)
cached.headers.update({"X-API-Key": api_key})
url = f"{BASE}/api/v1/trips"
for attempt in range(2):
    r = cached.get(url, params={"date": "2026-06-02"}, timeout=10)
    print(attempt, r.status_code, r.from_cache)

# %% 6.9 Putting it together: a day on the bikes
def get_trips(day):
    """Return all trips of one day as a DataFrame."""
    url = f"{BASE}/api/v1/trips"
    first = session.get(url, params={"date": day}, timeout=10).json()
    rows = list(first["data"])
    for n in range(2, first["meta"]["pages"] + 1):
        page = session.get(url, params={"date": day, "page": n},
                           timeout=10).json()
        rows.extend(page["data"])
    return pd.DataFrame(rows).assign(
        started_at=lambda d: pd.to_datetime(d["started_at"]))

# %% 6.9 Putting it together: a day on the bikes
trips = get_trips("2026-06-06")
names = stations.set_index("station_id")["name"]
trips["start_name"] = trips["start_station"].map(names)
hourly = trips["started_at"].dt.hour.value_counts().sort_index()
print(len(trips), "trips; busiest hour:", hourly.idxmax())
print(trips["start_name"].value_counts().head(3))
print(trips.groupby("rider")["duration_min"].median())
