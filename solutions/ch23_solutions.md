# Solutions: Chapter 23, Sharing Results

Worked solutions to the exercises at the end of Chapter 23 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch23_solutions.ipynb`](ch23_solutions.ipynb) or the script `ch23_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

The solutions use the coffee shop's orders, without cancelled ones and with a `revenue` column, and the chapter's logging setup.

## Exercise 23.1

*Add a markdown cell with a short conclusion and a code cell with a bar chart to the generated notebook, execute it and export it to HTML with the code hidden.*

```python
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
```

Output:

```text
True
```

The semicolon after `plot(...)` stops the notebook from also printing the axes object. The executed cell's output holds the chart as a PNG image, which the HTML file embeds, so the report is a single file. The conclusion is plain text in the notebook; for numbers that change, a code cell that prints an f-string keeps the text and the data in step.

## Exercise 23.2

*Add a third page to the PDF report with a table of revenue by state, drawn with `ax.table` on an axes with `ax.axis("off")`.*

```python
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
```

Output:

```text
16,660 bytes
```

`ax.table` draws a grid of text cells from a list of rows; `colLabels` adds the header, and `scale(1, 1.6)` makes the rows taller. `ax.axis("off")` hides the axes so that only the table shows. The same page can be appended to the chapter's report with one more `pdf.savefig` inside its `with` block.

## Exercise 23.3

*Add a date-range filter to the dashboard with `st.sidebar.slider`, and make the metrics and charts follow it.*

```python
first = orders["order_date"].min().date()
last = orders["order_date"].max().date()
start, end = st.sidebar.slider("Order dates", min_value=first,
                               max_value=last, value=(first, last))
view = view[view["order_date"].dt.date.between(start, end)]
```

A slider with a tuple as `value` lets the reader choose a range, and it accepts dates directly. Placed after the product and state filters and before the metrics, the extra line narrows `view`, so every element below follows it automatically: that's the advantage of Streamlit's top-to-bottom model.

## Exercise 23.4

*Write a test that starts the dashboard, uses Playwright to choose one product in the sidebar, and checks that the revenue metric changes.*

```python
def revenue_text(page):
    return page.locator('[data-testid="stMetricValue"]').first.inner_text()


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://127.0.0.1:8765")
    page.wait_for_selector("text=Slow deliveries")
    before = revenue_text(page)
    page.get_by_role("button", name="Clear all").first.click()
    page.get_by_role("combobox").first.click()
    page.get_by_role("option", name="House Blend").click()
    page.wait_for_timeout(2000)
    after = revenue_text(page)
    browser.close()
print(before, "->", after)
assert before != after
```

On the build machine, the test printed `$56,181 -> $12,725`: the House Blend's revenue alone.

Streamlit marks its elements with `data-testid` attributes, which make stable selectors; `stMetricValue` is the big number of a metric. The test clears the product selection with the multiselect's "Clear all" button, opens the first **combobox**, the list control of the products filter, picks one product, and checks that the revenue changed. Element names can change between Streamlit versions, so tests like this need an occasional update, which is still far cheaper than finding a broken dashboard in a meeting. The server is started and stopped as in the chapter.

## Exercise 23.5

*Change `refresh` so that it skips the work, and logs a message, if today's file already exists.*

```python
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
```

Output:

```text
INFO wrote reports/orders_2026-07-13.csv
INFO skipped: reports/orders_2026-07-13.csv already exists
```

The second call finds the file and returns at once, logging that it skipped. A scheduled job that may run twice, after a retry for example, should be safe to repeat in this way; such a job is called **idempotent**.

## Exercise 23.6

*Write the cron line and the GitHub Actions schedule for a refresh at 7:30 every weekday morning, and one for the first day of every month.*

```text
30 7 * * 1-5   cd /home/me/coffee && .venv/bin/python refresh.py
0 6 1 * *      cd /home/me/coffee && .venv/bin/python refresh.py

on:
  schedule:
    - cron: "30 7 * * 1-5"     # weekdays 07:30 UTC
    - cron: "0 6 1 * *"        # first of the month, 06:00 UTC
```

`1-5` in the day-of-week field means Monday to Friday, and `1` in the day-of-month field the first of the month. GitHub Actions uses the same five fields, but always in UTC: 7:30 UTC is 2:30 or 3:30 in the morning in New York, depending on daylight saving time (Chapter 12), so convert the time you want into UTC.

## Exercise 23.7

*Turn the coffee shop analysis of Chapters 11 to 14 into a reproducible project, and test it from a fresh folder.*

A sketch of the layout and the entry script:

```text
coffee-analysis/
  README.md            how to set up and run
  requirements.txt     pandas==3.0.6, pyarrow==26.0.0, matplotlib==3.11.2
  run_all.py           runs the two steps below in order
  data/raw/shop_orders_raw.csv
  src/clean.py         Chapter 11's pipeline: raw CSV -> data/processed/
  src/report.py        Chapter 14's summaries and a PDF in reports/
```

```python
"""run_all.py: rebuild everything from the raw data."""
import subprocess
import sys

for step in ["src/clean.py", "src/report.py"]:
    print("running", step)
    subprocess.run([sys.executable, step], check=True)
```

`check=True` stops at the first step that fails, instead of building a report from stale data. To test reproducibility: clone the project into a new folder, create a fresh virtual environment, install `requirements.txt`, run `python run_all.py`, and compare the processed data and the report figures with the originals. If anything differs, a step depends on something outside the project, such as a file on your desktop or a package version you didn't pin.
