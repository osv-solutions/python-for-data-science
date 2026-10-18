"""Project 14 (Advanced): Job Market Skills Tracker

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p14_jobs.py

or open the notebook and run the cells in order.
"""

# %% Step 1: The rules and the plan
import re
import time
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import numpy as np
import pandas as pd
import practice_web
import requests
from bs4 import BeautifulSoup

BASE = practice_web.start()
print(requests.get(f"{BASE}/robots.txt", timeout=10).text)

# %% Step 1: The rules and the plan
class ResponsibleFetcher:
    """GET pages only as robots.txt allows, after the crawl delay."""

    def __init__(self, site, agent, contact):
        self.robots = RobotFileParser(f"{site}/robots.txt")
        self.robots.read()
        self.agent, self.last, self.count = agent, 0.0, 0
        self.delay = max(self.robots.crawl_delay(agent) or 0, 1.0)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = f"{agent} ({contact})"

    def get(self, url):
        if not self.robots.can_fetch(self.agent, url):
            raise PermissionError(f"robots.txt forbids {url}")
        time.sleep(max(0, self.last + self.delay - time.monotonic()))
        self.last, self.count = time.monotonic(), self.count + 1
        return self.session.get(url, timeout=10)

# %% Step 2: Look before you crawl
fetcher = ResponsibleFetcher(BASE, "ds-book-jobs", "you@example.com")
soup = BeautifulSoup(fetcher.get(f"{BASE}/jobs/").text, "lxml")
print(soup.select_one("p.count").get_text())
card = soup.select_one("article.job")
print(*[p.get_text() for p in card.select("h2, p, span")], sep="\n")
print(soup.select_one("nav.pager").get_text(" ", strip=True))

# %% Step 2: Look before you crawl
feed = soup.select_one('link[rel="alternate"]')
print(feed["type"], feed["href"])
feed_url = urljoin(BASE, feed["href"])

# %% Step 2: Look before you crawl
xml = fetcher.get(feed_url).text
first = xml[:xml.find("</item>") + 7].replace("><", ">\n<")
for line in first.splitlines()[:14]:
    print(line[:70])

# %% Step 3: Parse the feed
def parse_items(xml):
    soup = BeautifulSoup(xml, "xml")
    rows = []
    for item in soup.find_all("item"):
        rows.append({"id": item.guid.text, "title": item.title.text,
                     "company": item.find("job:company").text,
                     "location": item.find("job:location").text,
                     "salary_text": item.find("job:salary").text,
                     "published": item.pubDate.text,
                     "description": item.description.text})
    nxt = soup.find("atom:link", rel="next")
    return rows, (nxt["href"] if nxt else None)

# %% Step 3: Parse the feed
def read_feed(day):
    url, rows = f"{BASE}/jobs/feed.xml?date={day}", []
    while url:
        page_rows, url = parse_items(fetcher.get(url).text)
        rows.extend(page_rows)
    return pd.DataFrame(rows).assign(snapshot=pd.Timestamp(day))

today = read_feed("2026-09-28")
print(len(today), "postings")
print(today.iloc[0, :6])

# %% Step 4: Weekly snapshots in DuckDB
mondays = pd.date_range("2026-07-06", "2026-09-28", freq="7D")
snapshots = pd.concat([read_feed(day.date()) for day in mondays],
                      ignore_index=True)
print(len(mondays), "snapshots,", fetcher.count, "requests in all")
print(snapshots.groupby("snapshot").size().describe().round(0))

# %% Step 4: Weekly snapshots in DuckDB
import duckdb

con = duckdb.connect("jobs.duckdb")
con.execute("CREATE OR REPLACE TABLE snapshots AS "
            "SELECT * FROM snapshots")
print(con.sql("""SELECT snapshot::DATE AS day, COUNT(*) AS postings
                 FROM snapshots GROUP BY day ORDER BY day LIMIT 3"""))

# %% Step 5: One row per posting, and reposts
jobs = con.sql("""
    SELECT id, any_value(title) AS title,
           any_value(company) AS company,
           any_value(location) AS location,
           any_value(salary_text) AS salary_text,
           any_value(description) AS description,
           strptime(any_value(published), '%a, %d %b %Y %H:%M:%S %z')
               ::DATE AS posted,
           min(snapshot)::DATE AS first_seen,
           max(snapshot)::DATE AS last_seen, count(*) AS weeks
    FROM snapshots GROUP BY id""").df()
print(len(jobs), "distinct postings")
print(jobs["weeks"].value_counts().sort_index())

# %% Step 5: One row per posting, and reposts
key = ["title", "company", "location", "salary_text"]
jobs = jobs.sort_values("posted")
jobs["repost"] = jobs.duplicated(key) & (jobs["salary_text"] != "")
print(jobs["repost"].sum(), "reposts")
print(jobs[jobs.duplicated(key, keep=False)
           & (jobs["salary_text"] != "")].sort_values(key)
      [key[:2] + ["posted"]].head(4))
jobs = jobs[~jobs["repost"]].reset_index(drop=True)

# %% Step 6: Parse the salaries
styles = jobs["salary_text"].str.replace(r"\d", "9", regex=True)
print(styles.value_counts().head(8))

# %% Step 6: Parse the salaries
def annual_salary(text):
    amounts = [float(a.replace(",", "")) for a in
               re.findall(r"\$([\d,.]+)", text)]
    if not amounts:
        return None                 # "Competitive" or empty
    if "K" in text:
        amounts = [a * 1_000 for a in amounts]
    if "hour" in text:
        amounts = [a * 2_080 for a in amounts]   # 40 hours x 52
    return sum(amounts) / len(amounts)

# %% Step 6: Parse the salaries
for text in ["$118,000 - $144,000 a year", "$95K–$116K",
             "$38 - $47 an hour", "Up to $150,000 per year",
             "Competitive"]:
    print(f"{text:28} {annual_salary(text)}")
jobs["salary"] = jobs["salary_text"].map(annual_salary)
share = jobs["salary"].notna().mean()
print(f"{share:.0%} of postings give a salary")

# %% Step 7: Find the skills
SKILLS = {
    "Python": r"(?i)\bpython\b", "SQL": r"SQL\b",
    "Excel": r"\bExcel\b", "Tableau": r"\bTableau\b",
    "Power BI": r"\bPower ?BI\b",
    "statistics": r"\bstatistic", "A/B testing": r"\bA/B test",
    "dbt": r"\bdbt\b", "R": r"\bR\b",
    "scikit-learn": r"scikit|sklearn",
    "PyTorch": r"\bPyTorch\b", "AWS": r"\bAWS\b|Amazon Web",
    "Docker": r"\bDocker\b", "Kubernetes": r"Kubernetes|\bk8s\b",
    "Spark": r"Spark\b", "Airflow": r"\bAirflow\b",
    "Hadoop": r"\bHadoop\b", "Polars": r"\bPolars\b",
    "LLMs": r"\bLLMs?\b|large language|generative AI|GenAI"}

# %% Step 7: Find the skills
r_hits = jobs["description"].str.extract(r"(.{12}\bR\b.{4})")[0]
print(r_hits.dropna().value_counts().head(4))

# %% Step 7: Find the skills
SKILLS["R"] = r"\bR\b(?!&)"
for skill, pattern in SKILLS.items():
    jobs[skill] = jobs["description"].str.contains(pattern)
demand = jobs[list(SKILLS)].mean().sort_values(ascending=False) * 100
print(demand.round(1).head(10))

# %% Step 8: Trends and pay
jobs["month"] = pd.to_datetime(jobs["posted"]).dt.to_period("M")
recent = jobs[jobs["month"] >= pd.Period("2026-07", "M")]
watch = ["LLMs", "Polars", "dbt", "Tableau", "Hadoop"]
trend = recent.groupby("month")[watch].mean() * 100
print(trend.round(1).T)

# %% Step 8: Trends and pay
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6.4, 3))
trend.index = trend.index.strftime("%b")
trend.plot(ax=ax, marker="o", markersize=3)
ax.set_ylabel("% of postings")
ax.set_xlabel("")
ax.legend(ncols=5, fontsize=7)
plt.show()

# %% Step 8: Trends and pay
is_ds = jobs["title"] == "Data Scientist"
ds = jobs[is_ds & jobs["salary"].notna()]
with_llm = ds.loc[ds["LLMs"], "salary"].to_numpy()
without = ds.loc[~ds["LLMs"], "salary"].to_numpy()
rng = np.random.default_rng(14)
diffs = [np.median(rng.choice(with_llm, len(with_llm)))
         - np.median(rng.choice(without, len(without)))
         for _ in range(2_000)]
low, high = np.percentile(diffs, [2.5, 97.5])
print(len(with_llm), len(without), "postings")
print(f"difference in medians: "
      f"{np.median(with_llm) - np.median(without):,.0f}"
      f" (95% CI {low:,.0f} to {high:,.0f})")

# %% Step 8: Trends and pay
clean = jobs.drop(columns="month")
con.execute("CREATE OR REPLACE TABLE jobs AS SELECT * FROM clean")
clean.drop(columns="description").to_csv("jobs.csv", index=False)
print(con.sql("SHOW TABLES"))
con.close()
print(f"{fetcher.count} requests to the job board")
