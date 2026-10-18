"""Project 2 (Beginner): Fitness Tracker Insights

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p02_fitness.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and look at the export
import json

import pandas as pd

with open("data/fitness_export.json", encoding="utf-8") as f:
    export = json.load(f)
print(list(export))
print(export["app"], export["version"])
print(export["user"])
print(len(export["days"]), "days")

# %% Step 1: Plan and look at the export
from pprint import pprint

pprint(export["days"][4], width=70, sort_dicts=False)

# %% Step 2: The days table
days = pd.json_normalize(export["days"])
days = days.drop(columns=["workouts", "sleep"])
for prefix in ["sleep.", "stages_min."]:
    days.columns = days.columns.str.replace(prefix, "", regex=False)
print(*days.columns)
print(days.shape)

# %% Step 2: The days table
days["date"] = pd.to_datetime(days["date"])
days["start"] = pd.to_datetime(days["start"])
days["end"] = pd.to_datetime(days["end"])
days["km"] = days["distance_m"] / 1000
days["sleep_h"] = (days["deep"] + days["rem"] + days["light"]) / 60
days["weekday"] = days["date"].dt.day_name()
days["weekend"] = days["date"].dt.dayofweek >= 5
print(days[["date", "steps", "km", "sleep_h", "weekday"]].head(3))

# %% Step 3: Gaps and days without the watch
year = pd.date_range("2025-01-01", "2025-12-31")
missing = year.difference(days["date"])
print(len(missing), "days missing")
print(*missing[missing.month == 8].strftime("%b %d"), sep=", ")

# %% Step 3: Gaps and days without the watch
print(days["resting_hr"].isna().sum(), "days without heart rate")
print(days.loc[days["resting_hr"].isna(), "steps"].describe()
      .round(0).loc[["count", "min", "max"]])
days["worn"] = days["resting_hr"].notna()
print(days["sleep_h"].isna().sum(), "nights without sleep data")

# %% Step 4: Steps through the year
worn = days[days["worn"]]
print(f"average {worn['steps'].mean():,.0f} steps a day, "
      f"median {worn['steps'].median():,.0f}")
print(f"10,000 or more on {(worn['steps'] >= 10_000).mean():.0%} "
      "of days")
monthly = worn.groupby(worn["date"].dt.month)["steps"].mean()
print((monthly / 1000).round(1).to_frame("thousands").T)

# %% Step 4: Steps through the year
import matplotlib.pyplot as plt

weekly = worn.groupby(worn["date"].dt.to_period("W"))["steps"].mean()
fig, ax = plt.subplots(figsize=(6.4, 2.6))
ax.bar(weekly.index.start_time, weekly, width=5, color="#2a7f8f")
ax.axhline(10_000, color="#c0582b", lw=1, ls="--")
ax.set_ylabel("Average steps per day")
ax.set_title("Steps per week, 2025", loc="left", fontsize=10)
plt.show()

# %% Step 5: Sleep, weekdays and weekends
sleep = days.groupby("weekend")[["sleep_h", "deep", "rem"]].mean()
sleep.index = ["weekday", "weekend"]
print(sleep.round(1))
bed = days["start"].dt.hour + days["start"].dt.minute / 60
print(bed.groupby(days["weekend"]).median().round(1).tolist())

# %% Step 5: Sleep, weekdays and weekends
fig, ax = plt.subplots(figsize=(6.4, 3))
colors = worn["weekend"].map({True: "#c0582b", False: "#1d5c8c"})
ax.scatter(worn["steps"], worn["sleep_h"], s=10, c=colors, alpha=0.6)
ax.set_xlabel("Steps that day")
ax.set_ylabel("Sleep that night (hours)")
ax.set_title("Weekdays (blue) and weekends (orange)", loc="left",
             fontsize=10)
plt.show()
print(worn["steps"].corr(worn["sleep_h"]).round(2))

# %% Step 6: Streaks and personal records
year_steps = days.set_index("date")["steps"].reindex(year)
active = year_steps.fillna(0) >= 8000
streak_id = (~active).cumsum()
lengths = active.groupby(streak_id).sum()
best = lengths.idxmax()
dates = year_steps.index[(streak_id == best) & active]
print(f"longest streak: {lengths.max()} days, "
      f"{dates[0]:%B %d} to {dates[-1]:%B %d}")

# %% Step 6: Streaks and personal records
workouts = pd.json_normalize(export["days"], record_path="workouts",
                             meta="date")
workouts["minutes"] = workouts["duration_s"] / 60
workouts["km"] = workouts["distance_m"] / 1000
print(workouts["type"].value_counts().to_frame().T)
print(workouts.groupby("type")["minutes"].sum().round(0).to_frame().T)

# %% Step 6: Streaks and personal records
runs = workouts[workouts["type"] == "run"].copy()
runs["pace"] = runs["minutes"] / runs["km"]
runs["month"] = pd.to_datetime(runs["date"]).dt.month
print(runs.groupby("month")["pace"].median().round(1).to_frame().T)
fastest = runs.nsmallest(1, "pace").iloc[0]
print(f"fastest run: {fastest['date']}, {fastest['km']:.1f} km, "
      f"{fastest['pace']:.2f} min/km")

# %% Step 7: Save the report
summary = pd.DataFrame({
    "steps": worn.groupby(worn["date"].dt.month)["steps"].mean(),
    "sleep_h": days.groupby(days["date"].dt.month)["sleep_h"].mean(),
    "workouts": workouts.groupby(
        pd.to_datetime(workouts["date"]).dt.month).size(),
}).round(1)
summary.index.name = "month"
with pd.ExcelWriter("fitness_2025.xlsx") as writer:
    summary.to_excel(writer, sheet_name="Months")
    sleep.round(2).to_excel(writer, sheet_name="Sleep")
    workouts.to_excel(writer, sheet_name="Workouts", index=False)
print(summary.head(3))
