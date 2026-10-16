"""Chapter 10: Scraping Responsibly

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch10_responsible.py

or open the notebook and run the cells in order.
"""

# %% 10.2 robots.txt in practice
import practice_web
import requests

BASE = practice_web.start()
print(requests.get(f"{BASE}/robots.txt", timeout=10).text)

# %% 10.2 robots.txt in practice
from urllib.robotparser import RobotFileParser

robots = RobotFileParser(f"{BASE}/robots.txt")
robots.read()
agent = "ds-book-crawler"
for path in ["/shop/catalogue/page-1.html", "/shop/admin/stats",
             "/shop/cart"]:
    print(path, robots.can_fetch(agent, f"{BASE}{path}"))
print("GreedyBot:", robots.can_fetch("GreedyBot", f"{BASE}/shop/"))
print("delay:", robots.crawl_delay(agent), "sitemaps:",
      robots.site_maps())

# %% 10.3 Terms of use
from bs4 import BeautifulSoup

terms = requests.get(f"{BASE}/shop/terms.html", timeout=10).text
import textwrap

text = BeautifulSoup(terms, "lxml").select_one("main p").get_text()
print(textwrap.fill(" ".join(text.split()), width=70))

# %% 10.8 Putting it together: a fetcher that follows the rules
import time
from urllib.parse import urlsplit

class ResponsibleFetcher:
    """GET pages only as a site's robots.txt allows, and log them."""

    def __init__(self, site, agent, contact):
        self.robots = RobotFileParser(f"{site}/robots.txt")
        self.robots.read()
        self.agent = agent
        self.delay = max(self.robots.crawl_delay(agent) or 0, 1.0)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = f"{agent} ({contact})"
        self.log, self.last = [], 0.0

# %% 10.8 Putting it together: a fetcher that follows the rules
def get(self, url):
    """GET a URL if robots.txt allows it, after the crawl delay."""
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

ResponsibleFetcher.get = get

# %% 10.8 Putting it together: a fetcher that follows the rules
fetcher = ResponsibleFetcher(BASE, "ds-book-crawler",
                             "you@example.com")
for n in range(1, 4):
    fetcher.get(f"{BASE}/shop/catalogue/page-{n}.html")
try:
    fetcher.get(f"{BASE}/shop/admin/stats")
except PermissionError as err:
    print(err)

# %% 10.8 Putting it together: a fetcher that follows the rules
times = [t for t, path, status in fetcher.log]
gaps = [b - a for a, b in zip(times, times[1:])]
print(len(fetcher.log), "requests, statuses:",
      sorted({status for _, _, status in fetcher.log}))
print("shortest gap between requests:", round(min(gaps), 2), "s")
