"""Solutions to the Chapter 12 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch12_solutions.py

The explanations are in ch12_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import pandas as pd

pattern = r"(?i)#?\bhc[-\s]?(?P<order>\d{5})"
levels = pd.CategoricalDtype(["low", "normal", "high", "urgent"],
                             ordered=True)


def parse_times(text, channel):
    out = pd.Series(pd.NaT, index=text.index,
                    dtype="datetime64[us, UTC]")
    iso = channel.isin(["web", "phone"])
    out[iso] = pd.to_datetime(text[iso], format="ISO8601", utc=True)
    local = pd.to_datetime(text[~iso], format="%m/%d/%Y %I:%M %p")
    local = local.dt.tz_localize("America/New_York")
    out[~iso] = local.dt.tz_convert("UTC")
    return out


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


desk = load_tickets("data/support_tickets.csv")
took = desk["closed"] - desk["opened"]
desk["hours"] = took.dt.total_seconds() / 3600

# %% Exercise 12.1
desk["domain"] = desk["customer"].str.split("@").str[1]
per_domain = desk.groupby("domain").agg(
    tickets=("ticket_id", "count"),
    with_order=("order_id", lambda s: s.notna().mean()))
print(per_domain.sort_values("with_order", ascending=False).round(2))

# %% Exercise 12.2
slowest = desk.nlargest(10, "hours")
print(slowest[["ticket_id", "priority", "hours"]].round(1))

# %% Exercise 12.3
sizes = desk["subject"].str.extract(
    r"(?i)\((?P<got>\d+k?g) instead of (?P<wanted>\d+k?g)\)")
sizes = sizes.dropna().apply(lambda col: col.str.lower())
print(len(sizes), "wrong-size tickets")
print(sizes.value_counts().head(3))

# %% Exercise 12.4
local = desk["opened"].dt.tz_convert("America/New_York")
after_hours = ((local.dt.hour < 9) | (local.dt.hour >= 17)
               | (local.dt.dayofweek >= 5))
table = desk.assign(after_hours=after_hours).groupby(
    "channel", observed=True)["after_hours"].agg(["sum", "mean"])
print(table.round(2))

# %% Exercise 12.5
closed = desk.dropna(subset=["closed"])
agents = closed.groupby("agent").agg(closed=("ticket_id", "count"),
                                     median_hours=("hours", "median"))
print(agents.sort_values("median_hours").round(1))

# %% Exercise 12.6
order = pd.CategoricalDtype(["Maya", "Luis", "Priya", "Tom"],
                            ordered=True)
desk["agent"] = desk["agent"].astype(order)
print(desk.sort_values("agent")["agent"].drop_duplicates().tolist())
print(desk["agent"].value_counts(sort=False))

# %% Exercise 12.7
day = desk["opened"].dt.tz_convert("America/New_York").dt.date
days = pd.date_range("2026-03-01", "2026-04-30", freq="D").date
per_day = day.value_counts().reindex(days, fill_value=0)
busy = per_day > 12
run_id = (busy != busy.shift()).cumsum()
runs = busy.groupby(run_id).agg(["first", "size"])
print(runs[runs["first"]]["size"].max(), "days in a row")
