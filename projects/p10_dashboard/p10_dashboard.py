"""Project 10 (Advanced): End-to-End Data Dashboard

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p10_dashboard.py

or open the notebook and run the cells in order.
"""

# %% Step 2: Collect
from datetime import date
from pathlib import Path

import pandas as pd
import practice_web
import pipeline

practice_web.start()
session = pipeline.make_session()
stations = pipeline.fetch_stations(session)
day = pipeline.fetch_day(session, date(2026, 9, 30))
print(stations.shape, day.shape)
print(day.iloc[0])

# %% Step 3: Check, and refuse bad days
good = date(2026, 9, 30)
print(pipeline.check(day, stations, good))
broken = pd.concat([day, day.head(3)])
broken.loc[broken.index[-1], "start_station"] = "S999"
print(pipeline.check(broken, stations, good))
print(pipeline.check(day.head(0), stations, good))

# %% Step 4: Store, idempotently
import sqlite3

for name in ["bikes.sqlite", "pipeline.log"]:
    Path(name).unlink(missing_ok=True)       # start from scratch
con = sqlite3.connect("bikes.sqlite")
con.executescript(pipeline.SCHEMA)
for _ in range(2):
    pipeline.store(con, good, day)
print(con.execute("SELECT COUNT(*) FROM trips").fetchone())
print(con.execute("SELECT day, trips FROM loads").fetchall())
con.close()

# %% Step 5: Refresh, backfill and log
import logging

logging.basicConfig(filename="pipeline.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    force=True)
until = date(2026, 9, 30)
print(pipeline.refresh(until), "days loaded")
print(pipeline.refresh(until), "days loaded")

# %% Step 5: Refresh, backfill and log
with sqlite3.connect("bikes.sqlite") as con:
    for gone in ["2026-09-14", "2026-09-15"]:
        con.execute("DELETE FROM trips WHERE day = ?", (gone,))
        con.execute("DELETE FROM loads WHERE day = ?", (gone,))
print(pipeline.refresh(until), "days loaded")
for line in Path("pipeline.log").read_text().splitlines()[-3:]:
    print(line[24:])

# %% Step 6: The dashboard
import socket
import subprocess
import sys
import time

server = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "dashboard.py",
     "--server.headless", "true", "--server.port", "8766",
     "--browser.gatherUsageStats", "false"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    try:
        socket.create_connection(("127.0.0.1", 8766), 1).close()
        break
    except OSError:
        time.sleep(0.5)

# %% Step 6: The dashboard
from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200,
                                          "height": 1160})
        page.goto("http://127.0.0.1:8766")
        page.wait_for_selector("text=Data through", timeout=30000)
        page.wait_for_timeout(2500)
        page.screenshot(path="dashboard.png")
        caption = page.get_by_text("Data through").inner_text()
        browser.close()
finally:
    server.terminate()
print(caption.split(";")[0])

# %% Step 6: The dashboard
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6.6, 6.4))
ax.imshow(plt.imread("dashboard.png"))
ax.axis("off")
plt.show()

# %% Step 7: Schedule and monitor
def health(db="bikes.sqlite", today=date(2026, 10, 1)):
    with sqlite3.connect(db) as con:
        loads = pd.read_sql("SELECT * FROM loads", con,
                            parse_dates=["day"])
    latest = loads["day"].max().date()
    typical = loads["trips"].median()
    return {"fresh": (today - latest).days <= 1,
            "complete": len(loads) >= 28,
            "volumes normal": bool(loads["trips"].between(
                typical / 2, typical * 2).all())}

print(health())
