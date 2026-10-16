"""Chapter 23: Sharing Results

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch23_sharing.py

or open the notebook and run the cells in order.
"""

# %% 23.2 Notebooks as reports
import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

nb = new_notebook(cells=[
    new_markdown_cell("# Orders this half-year\nCancelled orders "
                      "are excluded."),
    new_code_cell("import pandas as pd\n"
                  "o = pd.read_parquet('data/shop_orders.parquet')\n"
                  "o = o[o['status'] != 'cancelled']\n"
                  "o.groupby('product')['quantity'].sum()"),
])
nbformat.write(nb, "report.ipynb")

# %% 23.2 Notebooks as reports
ExecutePreprocessor(timeout=120, kernel_name="python3").preprocess(
    nb, {"metadata": {"path": "."}})
html, _ = HTMLExporter(exclude_input=True).from_notebook_node(nb)
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"{len(html):,} characters of HTML")
table = nb.cells[1].outputs[0]["data"]["text/plain"]
print("\n".join(table.splitlines()[:3]))

# %% 23.3 PDF reports with Matplotlib
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].assign(
    revenue=lambda d: d["quantity"] * d["unit_price"],
    month=lambda d: d["order_date"].dt.to_period("M"))
monthly = orders.groupby("month")["revenue"].sum()
by_product = orders.groupby("product")["revenue"].sum().sort_values()
stars = orders.groupby("shipping_days")["rating"].mean()

# %% 23.3 PDF reports with Matplotlib
def text_page(pdf, title, lines):
    fig = plt.figure(figsize=(8.27, 11.69))       # A4 portrait
    fig.text(0.1, 0.9, title, fontsize=20, weight="bold")
    for i, line in enumerate(lines):
        fig.text(0.1, 0.84 - i * 0.035, line, fontsize=11)
    pdf.savefig(fig)
    plt.close(fig)

# %% 23.3 PDF reports with Matplotlib
best = by_product.idxmax()
with PdfPages("sales_report.pdf") as pdf:
    text_page(pdf, "Hilltop Coffee Roasters: H1 2026", [
        f"Revenue: ${orders['revenue'].sum():,.0f} from "
        f"{len(orders):,} orders.",
        f"Best seller: {best} (${by_product.max():,.0f}).",
        "Deliveries of six days or more get ratings about a "
        "star lower."])
    fig, axes = plt.subplots(2, 1, figsize=(8.27, 11.69))
    monthly.plot(kind="bar", ax=axes[0], color="#1d5c8c", rot=0)
    axes[0].set_title("Revenue per month ($)")
    stars.plot(kind="bar", ax=axes[1], color="#c0582b", rot=0)
    axes[1].set_title("Average rating by days to deliver")
    pdf.savefig(fig)
    plt.close(fig)
    pdf.infodict()["Title"] = "Sales report H1 2026"
print(f"{Path('sales_report.pdf').stat().st_size:,} bytes")

# %% 23.4 Dashboards with Streamlit
import socket
import subprocess
import sys
import time

server = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "dashboard.py",
     "--server.headless", "true", "--server.port", "8765",
     "--browser.gatherUsageStats", "false"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):                       # wait up to 30 seconds
    try:
        socket.create_connection(("127.0.0.1", 8765), 1).close()
        break
    except OSError:
        time.sleep(0.5)

# %% 23.4 Dashboards with Streamlit
from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100,
                                          "height": 760})
        page.goto("http://127.0.0.1:8765")
        page.wait_for_selector("text=Slow deliveries", timeout=30000)
        page.wait_for_timeout(2000)
        page.screenshot(path="dashboard.png")
        print("title:", page.title())
        browser.close()
finally:
    server.terminate()

# %% 23.4 Dashboards with Streamlit
fig, ax = plt.subplots(figsize=(7, 4.9))
ax.imshow(plt.imread("dashboard.png"))
ax.axis("off")
plt.show()

# %% 23.5 Reproducible projects
from importlib.metadata import version

for name in ["numpy", "pandas", "matplotlib", "streamlit"]:
    print(f"{name}=={version(name)}")

# %% 23.6 Scheduling a refresh
import logging
from datetime import date

logging.basicConfig(filename="refresh.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


def refresh(today=None):
    today = today or date.today()
    out = Path("reports") / f"orders_{today:%Y-%m-%d}.csv"
    out.parent.mkdir(exist_ok=True)
    orders = pd.read_parquet("data/shop_orders.parquet")
    summary = orders.groupby("product")["quantity"].sum()
    summary.to_csv(out)
    logging.info("wrote %s with %d products", out, len(summary))
    return out

# %% 23.6 Scheduling a refresh
path = refresh(date(2026, 7, 6))
print(path, path.exists())
print(Path("refresh.log").read_text().splitlines()[-1][24:])

# %% 23.7 Putting it together: a weekly report in one call
def weekly_report(today):
    stamp = f"{today:%Y-%m-%d}"
    folder = Path("reports")
    with PdfPages(folder / f"sales_{stamp}.pdf") as pdf:
        text_page(pdf, f"Sales report, {stamp}", [
            f"Revenue: ${orders['revenue'].sum():,.0f}.",
            f"Best seller: {by_product.idxmax()}."])
    table = by_product.round(0).to_frame("revenue $").to_html()
    html = (f"<h1>Sales, {stamp}</h1><p>Best seller: "
            f"{by_product.idxmax()}</p>{table}")
    (folder / f"sales_{stamp}.html").write_text(html,
                                                encoding="utf-8")
    logging.info("weekly report %s written", stamp)
    return sorted(p.name for p in folder.glob(f"*{stamp}*"))


print(weekly_report(date(2026, 7, 6)))
