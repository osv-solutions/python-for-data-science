"""Chapter 1: The Data Science Toolkit and Workflow

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch01_workflow.py

or open the notebook and run the cells in order.
"""

# %% 1.4 Setting up your environment
import sys
import numpy as np
import pandas as pd
import matplotlib

print("Python     ", sys.version.split()[0])
print("NumPy      ", np.__version__)
print("pandas     ", pd.__version__)
print("Matplotlib ", matplotlib.__version__)

# %% 1.7 A first analysis
import pandas as pd

penguins = pd.read_csv("data/penguins.csv")
print(penguins.shape)
print(penguins.head())

# %% 1.7 A first analysis
print(penguins["species"].value_counts())
print("missing body mass:", penguins["body_mass_g"].isna().sum())

# %% 1.7 A first analysis
mass = penguins.groupby("species")["body_mass_g"].mean()
print(mass.round(0).sort_values())

# %% 1.7 A first analysis
by_sex = (penguins.groupby(["species", "sex"])["body_mass_g"]
          .mean().unstack().round(0))
by_sex["difference"] = by_sex["male"] - by_sex["female"]
print(by_sex)

# %% 1.7 A first analysis
import matplotlib.pyplot as plt

ax = by_sex[["female", "male"]].plot.bar(rot=0, color=["#2a9bb0",
                                                       "#1d5c8c"])
ax.set_ylabel("Average body mass (g)")
ax.set_title("Palmer penguins: body mass by species and sex")
plt.show()

# %% 1.8 Putting it together: an island report
from pathlib import Path

penguins = pd.read_csv("data/penguins.csv")
report = penguins.groupby("island").agg(
    birds=("species", "size"),
    species=("species", "nunique"),
    mean_mass_g=("body_mass_g", "mean"),
    mean_bill_mm=("bill_length_mm", "mean"),
).round(1)
Path("outputs").mkdir(exist_ok=True)
report.to_csv("outputs/island_report.csv")
print(report)
