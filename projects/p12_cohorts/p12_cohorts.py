"""Project 12 (Advanced): Subscription Retention and Cohorts

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p12_cohorts.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and audit
import pandas as pd

AS_OF = pd.Timestamp("2026-09-30")
subs = pd.read_csv("data/subscriptions.csv",
                   parse_dates=["signup_date", "cancel_date"])
print(subs.shape)
print(subs["plan"].value_counts())

# %% Step 1: Plan and audit
subs["plan"] = subs["plan"].str.lower()
print(subs.duplicated().sum(), "repeated rows")
impossible = subs["cancel_date"] < subs["signup_date"]
print(impossible.sum(), "cancelled before signing up")
print(subs[impossible].head(3))

# %% Step 1: Plan and audit
subs = subs[~impossible].drop_duplicates().reset_index(drop=True)
print(len(subs), "subscriptions")
print(subs.groupby("plan")["price"].agg(["min", "max", "count"]))

# %% Step 2: Months of membership
def months_between(start, end):
    months = ((end.dt.year - start.dt.year) * 12
              + end.dt.month - start.dt.month)
    short = (end.dt.day < start.dt.day) & ~end.dt.is_month_end
    return months - short

# %% Step 2: Months of membership
active = subs["cancel_date"].isna()
end = subs["cancel_date"].fillna(AS_OF)
subs["months"] = months_between(subs["signup_date"], end) + active
subs["age"] = months_between(subs["signup_date"],
                             pd.Series(AS_OF, index=subs.index))
subs["cohort"] = subs["signup_date"].dt.to_period("M")
print(subs[["signup_date", "cancel_date", "months", "age"]].head(4))

# %% Step 3: The cohort table
monthly = subs[subs["plan"] == "monthly"]
curve = {k: (monthly["months"] > k).astype(float)
               .where(monthly["age"] >= k) for k in range(13)}
retention = pd.DataFrame(curve).groupby(monthly["cohort"]).mean()
print((retention.iloc[[0, 1, 2, -3, -2, -1], :7] * 100).round(0))

# %% Step 3: The cohort table
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(6.4, 5.4))
sns.heatmap(retention.loc[:, 1:] * 100, cmap="Blues", vmin=30,
            vmax=90, cbar_kws={"label": "% still subscribed"}, ax=ax)
ax.set_xlabel("Months since sign-up")
ax.set_ylabel("Sign-up month")
ax.grid(False)
plt.show()

# %% Step 4: Did the June 2025 update help?
after = retention.index >= pd.Period("2025-06", "M")
curves = pd.DataFrame({
    "before": retention[~after].mean(),
    "after": retention[after].mean()}) * 100
print(curves.loc[[1, 3, 6, 9, 12]].round(1))

# %% Step 4: Did the June 2025 update help?
fig, ax = plt.subplots(figsize=(6.4, 3))
curves.plot(ax=ax, marker="o", markersize=3)
ax.set_xlabel("Months since sign-up")
ax.set_ylabel("% still subscribed")
ax.set_ylim(0, 100)
plt.show()

# %% Step 5: Channels and plans
seen6 = monthly[monthly["age"] >= 6]
by_channel = seen6.groupby("channel").agg(
    customers=("user_id", "count"),
    stayed_6=("months", lambda s: (s > 6).mean() * 100))
by_channel["share"] = by_channel["customers"] / len(seen6) * 100
print(by_channel.sort_values("stayed_6").round(1))

# %% Step 5: Channels and plans
annual = subs[(subs["plan"] == "annual") & (subs["age"] >= 12)]
renewed = annual["months"] > 12
print(f"{len(annual)} annual customers, {renewed.mean():.0%} renewed")
print(annual.assign(renewed=renewed)
      .groupby("channel")["renewed"].mean().round(2))

# %% Step 6: Revenue per customer
year1 = subs[subs["age"] >= 12].copy()
payments = year1["months"].clip(upper=12)
year1["revenue"] = year1["price"].where(year1["plan"] == "annual",
                                        year1["price"] * payments)
revenue = year1.groupby("channel")["revenue"].mean()
print(revenue.round(2).sort_values())

# %% Step 6: Revenue per customer
import numpy as np

rng = np.random.default_rng(12)

def bootstrap_mean(values, n=2_000):
    means = [rng.choice(values, len(values)).mean() for _ in range(n)]
    return np.percentile(means, [2.5, 97.5])

for channel, group in year1.groupby("channel"):
    low, high = bootstrap_mean(group["revenue"].to_numpy())
    print(f"{channel:9} {group['revenue'].mean():6.2f}"
          f"  ({low:.2f} to {high:.2f})")

# %% Step 7: Is each channel worth its cost?
spend = pd.read_csv("data/marketing_spend.csv")
spend["month"] = pd.PeriodIndex(spend["month"], freq="M")
months = year1["cohort"].unique()
cost = spend[spend["month"].isin(months)].groupby("channel")["spend"]
customers = year1["channel"].value_counts()
report = pd.DataFrame({"customers": customers, "revenue_y1": revenue,
                       "cac": cost.sum() / customers})
report["ratio"] = report["revenue_y1"] / report["cac"]
print(report.sort_values("ratio").round(2))

# %% Step 8: Save the report
with pd.ExcelWriter("retention_report.xlsx") as writer:
    (retention * 100).round(1).rename(index=str).to_excel(
        writer, sheet_name="Monthly cohorts")
    curves.round(1).to_excel(writer, sheet_name="Before and after")
    by_channel.round(1).to_excel(writer, sheet_name="Channels")
    report.round(2).to_excel(writer, sheet_name="Revenue and CAC")
print(f"{len(retention)} cohorts, {len(subs)} subscriptions")
