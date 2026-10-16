# Solutions: Chapter 1, The Data Science Toolkit and Workflow

Worked solutions to the exercises at the end of Chapter 1 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch01_solutions.ipynb`](ch01_solutions.ipynb) or the script `ch01_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

## Exercise 1.1

*Set up the book's environment, run the version check, then check pandas from a notebook.*

After installing `requirements.txt` into an activated virtual environment, the version check from the chapter prints the version of each library:

```python
import sys
import numpy as np
import pandas as pd
import matplotlib

for name, version in [("Python", sys.version.split()[0]),
                      ("NumPy", np.__version__),
                      ("pandas", pd.__version__),
                      ("Matplotlib", matplotlib.__version__)]:
    print(f"{name:<11}{version}")
```

Output:

```text
Python     3.14.6
NumPy      2.5.4
pandas     3.0.6
Matplotlib 3.11.2
```

In JupyterLab, the two cells are `import pandas as pd` and `pd.__version__`. The second cell needs no `print`: a notebook shows the value of a cell's last line by itself. If the import fails, the notebook's kernel is not using the virtual environment; start JupyterLab from the activated environment with `python -m jupyter lab`.

## Exercise 1.2

*Change `x` in the first cell without rerunning it, rerun the second cell, and explain.*

The second cell still prints `10`. The kernel only knows the values that cells have *run*, and the first cell, though it now reads `x = 5` on the page, has not run since you changed it, so `x` is still 1 in the kernel's memory. After **Kernel > Restart Kernel and Run All Cells**, the cells run from top to bottom and the output becomes `50`. The same thing, written as plain code in the order the cells ran:

```python
x = 1              # cell 1, first version, run
print(x * 10)      # cell 2, run
# cell 1 edited to x = 5, but not run: the kernel still has x = 1
print(x * 10)      # cell 2, run again
x = 5              # Restart and Run All: cell 1 runs again ...
print(x * 10)      # ... and then cell 2
```

Output:

```text
10
10
50
```

## Exercise 1.3

*Print how many penguins were recorded in each year and on each island.*

```python
penguins = pd.read_csv("data/penguins.csv")
print(penguins["year"].value_counts().sort_index())
print(penguins["island"].value_counts())
```

Output:

```text
year
2007    110
2008    114
2009    120
Name: count, dtype: int64
island
Biscoe       168
Dream        124
Torgersen     52
Name: count, dtype: int64
```

`value_counts` counts each distinct value. For the years, `sort_index` puts them in time order rather than by count.

## Exercise 1.4

*Find the average flipper length of each species, from longest to shortest, rounded to one decimal place.*

```python
flippers = (penguins.groupby("species")["flipper_length_mm"].mean()
            .sort_values(ascending=False).round(1))
print(flippers)
```

Output:

```text
species
Gentoo       217.2
Chinstrap    195.8
Adelie       190.0
Name: flipper_length_mm, dtype: float64
```

The same `groupby`, `mean` pattern as the chapter's body-mass example, with `sort_values(ascending=False)` putting the longest first: Gentoo flippers are the longest, at 217.2 millimeters on average.

## Exercise 1.5

*Create the chapter's project folder layout for an analysis of your own, with a README that describes the question.*

`pathlib` creates the folders and the README in a few lines, which also makes the layout easy to repeat for every new project:

```python
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
```

Output:

```text
README.md
data
data/processed
data/raw
notebooks
outputs
src
```

`mkdir(parents=True, exist_ok=True)` creates each folder together with any missing parent, and does nothing if it already exists. `rglob("*")` lists everything inside the project, at every level.

## Exercise 1.6

*Extend the island report with the share of females on each island, as a percentage with one decimal place.*

```python
report = (penguins
          .assign(is_female=penguins["sex"] == "female")
          .groupby("island")
          .agg(birds=("species", "size"),
               species=("species", "nunique"),
               mean_mass_g=("body_mass_g", "mean"),
               female_pct=("is_female", "mean")))
report["female_pct"] = (report["female_pct"] * 100).round(1)
print(report.round(1))
```

Output:

```text
           birds  species  mean_mass_g  female_pct
island                                            
Biscoe       168        2       4716.0        47.6
Dream        124        2       3712.9        49.2
Torgersen     52        1       3706.4        46.2
```

`penguins["sex"] == "female"` is a Boolean column, so its mean per island is the share of females. Note that birds of unknown sex count as "not female" here, which slightly lowers the shares; to leave them out, first drop the rows with `dropna(subset=["sex"])`.
