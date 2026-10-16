"""Solutions to the Chapter 23 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch23_solutions.py

The explanations are in ch23_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import logging
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].assign(
    revenue=lambda d: d["quantity"] * d["unit_price"])
logging.basicConfig(filename="refresh.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# %% Exercise 23.1
import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

nb = new_notebook(cells=[
    new_markdown_cell("# Bags sold per product"),
    new_code_cell("import pandas as pd\n"
                  "o = pd.read_parquet('data/shop_orders.parquet')\n"
                  "q = o.groupby('product')['quantity'].sum()\n"
                  "q.sort_values().plot(kind='barh');"),
    new_markdown_cell("**Conclusion:** the House Blend sells the most "
                      "bags; the Decaf the fewest."),
])
ExecutePreprocessor(timeout=120, kernel_name="python3").preprocess(
    nb, {"metadata": {"path": "."}})
html, _ = HTMLExporter(exclude_input=True).from_notebook_node(nb)
Path("bags.html").write_text(html, encoding="utf-8")
print("image/png" in nb.cells[1].outputs[0]["data"])

# %% Exercise 23.2
from matplotlib.backends.backend_pdf import PdfPages

by_state = orders.groupby("state")["revenue"].sum().sort_values(
    ascending=False)
with PdfPages("state_report.pdf") as pdf:
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis("off")
    ax.set_title("Revenue by state", fontsize=16, loc="left")
    table = ax.table(cellText=[[s, f"${v:,.0f}"] for s, v in
                               by_state.items()],
                     colLabels=["State", "Revenue"], loc="upper left",
                     colWidths=[0.3, 0.3])
    table.scale(1, 1.6)
    pdf.savefig(fig)
    plt.close(fig)
print(f"{Path('state_report.pdf').stat().st_size:,} bytes")

# %% Exercise 23.5
def refresh(today=None):
    today = today or date.today()
    out = Path("reports") / f"orders_{today:%Y-%m-%d}.csv"
    if out.exists():
        logging.info("skipped: %s already exists", out)
        return out
    out.parent.mkdir(exist_ok=True)
    summary = orders.groupby("product")["quantity"].sum()
    summary.to_csv(out)
    logging.info("wrote %s", out)
    return out


for _ in range(2):
    refresh(date(2026, 7, 13))
for line in Path("refresh.log").read_text().splitlines()[-2:]:
    print(line[24:])
