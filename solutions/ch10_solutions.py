"""Solutions to the Chapter 10 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch10_solutions.py

The explanations are in ch10_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import practice_web
import requests
from bs4 import BeautifulSoup

BASE = practice_web.start()
robots = RobotFileParser(f"{BASE}/robots.txt")
robots.read()

class ResponsibleFetcher:
    def __init__(self, site, agent, contact):
        self.robots = RobotFileParser(f"{site}/robots.txt")
        self.robots.read()
        self.agent = agent
        self.delay = max(self.robots.crawl_delay(agent) or 0, 1.0)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = f"{agent} ({contact})"
        self.log, self.last = [], 0.0

    def get(self, url):
        if not self.robots.can_fetch(self.agent, url):
            raise PermissionError(f"robots.txt forbids {url}")
        wait = self.last + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last = time.monotonic()
        response = self.session.get(url, timeout=10)
        self.log.append((self.last, urlsplit(url).path,
                         response.status_code))
        return response

# %% Exercise 10.1
for agent in ["GreedyBot", "ds-book-crawler"]:
    for path in ["/robots.txt", "/shop/terms.html"]:
        print(f"{agent:<16}{path:<18}"
              f"{robots.can_fetch(agent, BASE + path)}")

# %% Exercise 10.2
sitemap = requests.get(f"{BASE}/sitemap.xml", timeout=10).text
locs = [loc.get_text() for loc in
        BeautifulSoup(sitemap, "xml").select("loc")]
books = [u for u in locs if "/shop/book/" in u]
print(len(locs), "URLs,", len(books), "book pages")

# %% Exercise 10.3
def polite_delay(robots, agent, minimum=1.0):
    """The site's crawl delay, but never less than minimum."""
    return max(robots.crawl_delay(agent) or 0, minimum)

slow = RobotFileParser()
slow.parse(["User-agent: *", "Crawl-delay: 5", "Disallow: /private/"])
print(polite_delay(slow, "anybot"), polite_delay(robots, "anybot"))
print(polite_delay(RobotFileParser(), "anybot"))

# %% Exercise 10.4
from collections import Counter

def summary(self):
    times = [t for t, _, _ in self.log]
    gaps = [b - a for a, b in zip(times, times[1:])]
    return {"requests": len(self.log),
            "statuses": dict(Counter(s for _, _, s in self.log)),
            "average gap": round(sum(gaps) / len(gaps), 2) if gaps
            else None,
            "total time": round(times[-1] - times[0], 2) if times
            else 0}

# %% Exercise 10.4
ResponsibleFetcher.summary = summary
fetcher = ResponsibleFetcher(BASE, "ds-book-crawler",
                             "you@example.com")
for n in (1, 2, 3, 99):
    fetcher.get(f"{BASE}/shop/catalogue/page-{n}.html")
for key, value in fetcher.summary().items():
    print(f"{key:<12}{value}")

# %% Exercise 10.5
import json
from pathlib import Path

record = {
    "source": "Corner Books (practice site)",
    "url": f"{BASE}/shop/",
    "pages_collected": "catalog pages and book pages",
    "rules": {"robots.txt": "catalog and book pages allowed; "
                            "admin and cart disallowed",
              "crawl_delay_seconds": 1,
              "terms": "learning use; identify yourself; 1 s pause"},
    "personal_data": "none collected",
    "contact": "you@example.com",
    "collected": "2026-10-15"}

# %% Exercise 10.5
text = json.dumps(record, indent=2)
Path("source_corner_books.json").write_text(text)
saved = json.loads(Path("source_corner_books.json").read_text())
print(len(saved), "fields; delay:",
      saved["rules"]["crawl_delay_seconds"], "s")

# %% Exercise 10.7
def careful_get(self, url, max_strikes=3):
    """GET like get(), slowing down when the server pushes back."""
    response = self.get(url)
    if response.status_code in (429, 503):
        self.strikes = getattr(self, "strikes", 0) + 1
        self.delay *= 2
        if self.strikes >= max_strikes:
            raise RuntimeError(f"stopping: {self.strikes} refusals")
    else:
        self.strikes = 0
    return response

ResponsibleFetcher.careful_get = careful_get

# %% Exercise 10.7
fetcher = ResponsibleFetcher(BASE, "ds-book-crawler",
                             "you@example.com")
fetcher.delay = 0.3
time.sleep(2)
try:
    for n in range(8):
        r = fetcher.careful_get(f"{BASE}/api/v1/limited")
        print(n, r.status_code, round(fetcher.delay, 2))
except RuntimeError as err:
    print(err)
