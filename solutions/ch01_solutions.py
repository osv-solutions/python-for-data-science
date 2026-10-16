"""Solutions to the Chapter 1 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch01_solutions.py

The explanations are in ch01_solutions.md."""

# %% Exercise 1.1
import sys
import numpy as np
import pandas as pd
import matplotlib

for name, version in [("Python", sys.version.split()[0]),
                      ("NumPy", np.__version__),
                      ("pandas", pd.__version__),
                      ("Matplotlib", matplotlib.__version__)]:
    print(f"{name:<11}{version}")

# %% Exercise 1.2
x = 1              # cell 1, first version, run
print(x * 10)      # cell 2, run
# cell 1 edited to x = 5, but not run: the kernel still has x = 1
print(x * 10)      # cell 2, run again
x = 5              # Restart and Run All: cell 1 runs again ...
print(x * 10)      # ... and then cell 2

# %% Exercise 1.3
penguins = pd.read_csv("data/penguins.csv")
print(penguins["year"].value_counts().sort_index())
print(penguins["island"].value_counts())

# %% Exercise 1.4
flippers = (penguins.groupby("species")["flipper_length_mm"].mean()
            .sort_values(ascending=False).round(1))
print(flippers)

# %% Exercise 1.5
from pathlib import Path

project = Path("coffee-prices")
for folder in ["data/raw", "data/processed", "notebooks", "src",
               "outputs"]:
    (project / folder).mkdir(parents=True, exist_ok=True)
(project / "README.md").write_text(
    "# Coffee prices\n\nQuestion: how much has the price of a cup of "
    "coffee in my city changed since 2020?\n", encoding="utf-8")
for path in sorted(project.rglob("*")):
    print(path.relative_to(project))

# %% Exercise 1.6
report = (penguins
          .assign(is_female=penguins["sex"] == "female")
          .groupby("island")
          .agg(birds=("species", "size"),
               species=("species", "nunique"),
               mean_mass_g=("body_mass_g", "mean"),
               female_pct=("is_female", "mean")))
report["female_pct"] = (report["female_pct"] * 100).round(1)
print(report.round(1))
