"""Riverton bike-share pipeline (Project 15): collect, check, store.

Run it with:  python pipeline.py
It loads each day of the last four weeks not yet in bikes.sqlite,
from the practice server's bike-share API, which must be running
(python practice_web.py in another terminal)."""
import logging
import os
import sqlite3
from datetime import date, timedelta

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

API = "http://127.0.0.1:8020/api/v1"
KEY = os.environ.get("BIKE_API_KEY", "demo-key-2026")
DB = "bikes.sqlite"
log = logging.getLogger("pipeline")


def make_session():
    session = requests.Session()
    retry = Retry(total=4, backoff_factor=0.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"X-API-Key": KEY,
                            "User-Agent": "riverton-dashboard/1.0"})
    return session


def fetch_stations(session):
    rows, url = [], f"{API}/stations?per_page=50"
    while url:
        page = session.get(url, timeout=10)
        page.raise_for_status()
        rows += page.json()["data"]
        url = page.json()["links"]["next"]
    stations = pd.json_normalize(rows)
    stations.columns = [c.split(".")[-1] for c in stations.columns]
    keep = ["station_id", "name", "neighborhood", "lat", "lon",
            "capacity"]
    return stations[keep]


def fetch_day(session, day):
    rows, number, pages = [], 1, 1
    while number <= pages:
        reply = session.get(f"{API}/trips", timeout=10, params={
            "date": day.isoformat(), "page": number, "per_page": 200})
        reply.raise_for_status()
        body = reply.json()
        rows += body["data"]
        pages = body["meta"]["pages"]
        number += 1
    trips = pd.DataFrame(rows)
    trips["started_at"] = pd.to_datetime(trips["started_at"])
    return trips


def check(trips, stations, day):
    if trips.empty:
        return ["no trips"]
    known = stations["station_id"]
    ends = pd.concat([trips["start_station"], trips["end_station"]])
    minutes = trips["duration_min"]
    failed = {
        "duplicate trip ids": trips["trip_id"].duplicated().any(),
        "wrong day": (trips["started_at"].dt.date != day).any(),
        "bad duration": not minutes.between(1, 24 * 60).all(),
        "unknown station": not ends.isin(known).all(),
    }
    return [name for name, bad in failed.items() if bad]


SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
    station_id TEXT PRIMARY KEY, name TEXT, neighborhood TEXT,
    lat REAL, lon REAL, capacity INTEGER);
CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY, day TEXT, started_at TEXT,
    duration_min REAL, start_station TEXT, end_station TEXT,
    rider TEXT, bike TEXT);
CREATE TABLE IF NOT EXISTS loads (
    day TEXT PRIMARY KEY, trips INTEGER, loaded_at TEXT);
"""


def store(con, day, trips):
    rows = trips.assign(day=day.isoformat(),
                        started_at=trips["started_at"].astype(str))
    with con:                                  # one transaction
        con.execute("DELETE FROM trips WHERE day = ?",
                    (day.isoformat(),))
        rows.to_sql("trips", con, if_exists="append", index=False)
        now = pd.Timestamp.now().isoformat(timespec="seconds")
        con.execute("INSERT OR REPLACE INTO loads VALUES (?, ?, ?)",
                    (day.isoformat(), len(rows), now))


def refresh(until=None, days=28, db=DB):
    until = until or date.today() - timedelta(days=1)
    wanted = [until - timedelta(days=i) for i in range(days)]
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    done = {d for (d,) in con.execute("SELECT day FROM loads")}
    session = make_session()
    stations = fetch_stations(session)
    with con:
        con.execute("DELETE FROM stations")
        stations.to_sql("stations", con, if_exists="append",
                        index=False)
    loaded = 0
    for day in sorted(d for d in wanted if d.isoformat() not in done):
        try:
            trips = fetch_day(session, day)
        except requests.RequestException as error:
            log.error("%s: download failed: %s", day, error)
            continue
        problems = check(trips, stations, day)
        if problems:
            log.error("%s: not loaded: %s", day, ", ".join(problems))
            continue
        store(con, day, trips)
        log.info("%s: loaded %d trips", day, len(trips))
        loaded += 1
    con.close()
    log.info("refresh done: %d new days", loaded)
    return loaded


if __name__ == "__main__":
    logging.basicConfig(
        filename="pipeline.log", level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    refresh()
