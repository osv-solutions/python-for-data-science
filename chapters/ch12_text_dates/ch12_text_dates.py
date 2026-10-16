"""Chapter 12: Text, Dates and Categories

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch12_text_dates.py

or open the notebook and run the cells in order.
"""

# %% 12.1 The support desk data
import pandas as pd

tickets = pd.read_csv("data/support_tickets.csv")
print(tickets.shape)
print(tickets.loc[[0, 4, 9], ["channel", "opened", "customer"]])
print(tickets.loc[[3, 12], "subject"].tolist())

# %% 12.2 Working with text: the str accessor
email = tickets["customer"].str.strip().str.lower()
print(tickets["customer"].nunique(), "->", email.nunique())
parts = email.str.split("@", expand=True)
parts.columns = ["user", "domain"]
print(parts["domain"].value_counts())

# %% 12.2 Working with text: the str accessor
subject = tickets["subject"].str.strip()
print(subject.str.len().describe()[["mean", "max"]].round(1))
print(subject.str.contains("refund", case=False).sum(), "refunds")
print(subject.str.startswith("Where").sum(), "start with Where")
print(subject.str.upper().str.isupper().all())

# %% 12.3 Regular expressions
pattern = r"(?i)#?\bhc[-\s]?(?P<order>\d{5})"
found = subject.str.extract(pattern)
print(found.head(4))
print(found["order"].notna().sum(), "tickets mention an order")

# %% 12.3 Regular expressions
topics = {"damage": r"damaged|broken",
          "delivery": r"where is|not here",
          "refund": r"refund", "wrong item": r"wrong",
          "quality": r"stale|taste",
          "account": r"log in|address|subscription"}
topic = pd.Series("other", index=subject.index)
for name, pat in reversed(topics.items()):
    topic[subject.str.contains(pat, case=False)] = name
print(topic.value_counts())

# %% 12.3 Regular expressions
standard = subject.str.replace(pattern, r"HC-\g<order>", regex=True)
messy = subject.str.contains(r"^order hc|^Where is my order #")
for before, after in zip(subject[messy][:3], standard[messy][:3]):
    print(before, "->", after)

# %% 12.4 Parsing dates
first = tickets.groupby("channel")["opened"].first()
print(first)

# %% 12.4 Parsing dates
try:
    pd.to_datetime(tickets["opened"])
except ValueError as err:
    print("ValueError:", str(err).splitlines()[0][:62])

# %% 12.4 Parsing dates
mixed = pd.to_datetime(tickets["opened"], format="mixed", utc=True)
row = tickets.index[tickets["channel"] == "email"][0]
print(tickets.loc[row, "opened"], "->", mixed[row])

# %% 12.4 Parsing dates
def parse_times(text, channel):
    out = pd.Series(pd.NaT, index=text.index,
                    dtype="datetime64[us, UTC]")
    iso = channel.isin(["web", "phone"])
    out[iso] = pd.to_datetime(text[iso], format="ISO8601", utc=True)
    local = pd.to_datetime(text[~iso], format="%m/%d/%Y %I:%M %p")
    local = local.dt.tz_localize("America/New_York")
    out[~iso] = local.dt.tz_convert("UTC")
    return out

# %% 12.4 Parsing dates
for col in ["opened", "closed"]:
    tickets[col] = parse_times(tickets[col], tickets["channel"])
print(tickets["opened"].dtype)
print(tickets.loc[row, "opened"])
print(tickets["closed"].isna().sum(), "tickets still open")

# %% 12.5 Time zones
local = tickets["opened"].dt.tz_convert("America/New_York")
print(local.iloc[[0, 1]])
by_hour = local.dt.hour.value_counts().sort_index()
print("busiest hours:", by_hour.nlargest(3).index.tolist())

# %% 12.5 Time zones
start = pd.Timestamp("2026-03-07 12:00")
end = pd.Timestamp("2026-03-08 12:00")
print("naive:", end - start)
ny = "America/New_York"
print("aware:", end.tz_localize(ny) - start.tz_localize(ny))

# %% 12.6 Durations and periods
took = tickets["closed"] - tickets["opened"]
print(took.dtype)
print(took.describe()[["mean", "50%", "max"]])
hours = took.dt.total_seconds() / 3600
print(f"{(hours <= 24).mean():.0%} closed within a day")

# %% 12.6 Durations and periods
local_day = local.dt.tz_localize(None)
week = local_day.dt.to_period("W")
print(week.value_counts().sort_index().head(4))
print(local.dt.day_name().value_counts().head(3))

# %% 12.7 Categorical data
print(tickets["priority"].value_counts().rename(index=repr).head(5))

# %% 12.7 Categorical data
levels = pd.CategoricalDtype(["low", "normal", "high", "urgent"],
                             ordered=True)
priority = tickets["priority"].str.strip().str.lower().astype(levels)
print(priority.dtype)
print(priority.value_counts(sort=False))
print((priority >= "high").sum(), "high or urgent")

# %% 12.7 Categorical data
agent = tickets["agent"]
print(agent.memory_usage(deep=True), "bytes as str")
print(agent.astype("category").memory_usage(deep=True),
      "bytes as category")

# %% 12.7 Categorical data
bands = pd.cut(hours, bins=[0, 4, 24, 72, float("inf")],
               labels=["< 4 h", "4-24 h", "1-3 days", "> 3 days"]
               ).rename("closed in")
print(pd.crosstab(priority, bands))

# %% 12.8 Putting it together: the support desk report
def load_tickets(path):
    raw = pd.read_csv(path)
    subject = raw["subject"].str.strip()
    return raw.assign(
        opened=parse_times(raw["opened"], raw["channel"]),
        closed=parse_times(raw["closed"], raw["channel"]),
        customer=raw["customer"].str.strip().str.lower(),
        subject=subject,
        order_id="HC-" + subject.str.extract(pattern)["order"],
        priority=(raw["priority"].str.strip().str.lower()
                  .astype(levels)),
        channel=raw["channel"].astype("category"),
    )

# %% 12.8 Putting it together: the support desk report
desk = load_tickets("data/support_tickets.csv")
took = desk["closed"] - desk["opened"]
desk["hours"] = took.dt.total_seconds() / 3600
report = desk.groupby("priority", observed=True).agg(
    tickets=("ticket_id", "count"),
    median_hours=("hours", "median"),
    within_day=("hours", lambda h: (h <= 24).mean()),
)
print(report.round(2))
