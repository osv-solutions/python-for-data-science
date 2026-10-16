# Solutions: Chapter 12, Text, Dates and Categories

Worked solutions to the exercises at the end of Chapter 12 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch12_solutions.ipynb`](ch12_solutions.ipynb) or the script `ch12_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

The solutions start from the chapter's `load_tickets` function and the clean `desk` table, with its `hours` column.

## Exercise 12.1

*Count the tickets per email domain, and find the domain whose customers mention an order number most often, as a share of their tickets.*

```python
desk["domain"] = desk["customer"].str.split("@").str[1]
per_domain = desk.groupby("domain").agg(
    tickets=("ticket_id", "count"),
    with_order=("order_id", lambda s: s.notna().mean()))
print(per_domain.sort_values("with_order", ascending=False).round(2))
```

Output:

```text
                      tickets  with_order
domain                                   
gmail.com                  89        0.80
outlook.com               118        0.75
hilltop-partners.com      166        0.70
yahoo.com                 153        0.68
example.org               114        0.68
```

`str.split("@")` gives a list per address, and `.str[1]` takes the second element of each list, the domain. The share of tickets with an order number is the mean of `notna()`. Gmail users mention an order most often, in 80% of their tickets; the other domains are between 68% and 75%, so customers of every kind write mostly about their orders.

## Exercise 12.2

*Print the ten tickets that took longest to close, with their priority and duration in hours, rounded to one decimal.*

```python
slowest = desk.nlargest(10, "hours")
print(slowest[["ticket_id", "priority", "hours"]].round(1))
```

Output:

```text
    ticket_id priority  hours
232    T-0233      low  168.0
403    T-0404      low  163.8
440    T-0441      low  161.2
612    T-0613      low  127.6
155    T-0156      low  118.5
505    T-0506      low  114.8
121    T-0122      low  108.6
605    T-0606      low  106.8
168    T-0169      low  106.3
583    T-0584      low  101.4
```

`nlargest(10, "hours")` sorts by duration and keeps the top ten in one step; open tickets, with a missing duration, are left out automatically. All ten are low priority, between about four and seven days, which is what a desk that handles the urgent work first should show.

## Exercise 12.3

*Write a regex that extracts the two bag sizes from subjects such as `Wrong bag size (500g instead of 1kg)` into columns `got` and `wanted`, and count the most common mix-up.*

```python
sizes = desk["subject"].str.extract(
    r"(?i)\((?P<got>\d+k?g) instead of (?P<wanted>\d+k?g)\)")
sizes = sizes.dropna().apply(lambda col: col.str.lower())
print(len(sizes), "wrong-size tickets")
print(sizes.value_counts().head(3))
```

Output:

```text
62 wrong-size tickets
got   wanted
500g  1kg       13
1kg   500g      13
250g  500g      12
Name: count, dtype: int64
```

`\(` and `\)` match literal parentheses, which otherwise mark groups. `\d+k?g` matches one or more digits, an optional `k`, then `g`, so it covers both `500g` and `1kg`. Lower-casing afterwards merges the subjects typed in capitals. `value_counts` on a two-column DataFrame counts each combination. There are 62 such tickets, and the top three mix-ups are almost equally common, 12 or 13 each, which suggests a packing problem in general rather than one mislabeled shelf.

## Exercise 12.4

*Count the tickets opened outside business hours, before 9 a.m. or after 5 p.m. New York time or on a weekend, per channel.*

```python
local = desk["opened"].dt.tz_convert("America/New_York")
after_hours = ((local.dt.hour < 9) | (local.dt.hour >= 17)
               | (local.dt.dayofweek >= 5))
table = desk.assign(after_hours=after_hours).groupby(
    "channel", observed=True)["after_hours"].agg(["sum", "mean"])
print(table.round(2))
```

Output:

```text
         sum  mean
channel           
email    101  0.53
phone     67  0.51
web      175  0.55
```

The test runs on local time, because "9 to 5" is a New York clock time. `dt.dayofweek` numbers Monday as 0, so 5 and 6 are Saturday and Sunday. Between 51% and 55% of the tickets on every channel arrive outside business hours, so a desk staffed only from 9 to 5 on weekdays would start each morning with a backlog.

## Exercise 12.5

*For each agent, compute the number of tickets closed and their median hours to close, and list the agents from fastest to slowest.*

```python
closed = desk.dropna(subset=["closed"])
agents = closed.groupby("agent").agg(closed=("ticket_id", "count"),
                                     median_hours=("hours", "median"))
print(agents.sort_values("median_hours").round(1))
```

Output:

```text
       closed  median_hours
agent                      
Tom       158          15.7
Luis      158          16.1
Maya      162          18.2
Priya     151          18.2
```

Dropping the open tickets first makes `count` the number of closed tickets. Tom and Luis close their tickets in a median of about 16 hours, Maya and Priya in about 18. Before calling one agent faster, compare their mix of priorities: an agent who handles more urgent tickets will look faster for that reason alone.

## Exercise 12.6

*Make the agent names an ordered categorical in the order Maya, Luis, Priya, Tom, and show that sorting by agent follows it.*

```python
order = pd.CategoricalDtype(["Maya", "Luis", "Priya", "Tom"],
                            ordered=True)
desk["agent"] = desk["agent"].astype(order)
print(desk.sort_values("agent")["agent"].drop_duplicates().tolist())
print(desk["agent"].value_counts(sort=False))
```

Output:

```text
['Maya', 'Luis', 'Priya', 'Tom']
agent
Maya     165
Luis     161
Priya    152
Tom      162
Name: count, dtype: int64
```

Sorting follows the order of the categories, not the alphabet, so Maya comes first and Luis second. `value_counts(sort=False)` lists the agents in the same order.

## Exercise 12.7

*Using `pd.date_range` with `freq="D"`, count the tickets opened on each day of March and April, including days with none, and find the longest run of days with more than 12 tickets.*

```python
day = desk["opened"].dt.tz_convert("America/New_York").dt.date
days = pd.date_range("2026-03-01", "2026-04-30", freq="D").date
per_day = day.value_counts().reindex(days, fill_value=0)
busy = per_day > 12
run_id = (busy != busy.shift()).cumsum()
runs = busy.groupby(run_id).agg(["first", "size"])
print(runs[runs["first"]]["size"].max(), "days in a row")
```

Output:

```text
3 days in a row
```

Counting by local date and reindexing with all 61 days puts 0 on days without tickets. To find runs, `busy != busy.shift()` is true wherever the value changes, so its cumulative sum gives each run of equal values its own number. Grouping by that number gives each run's first value and length, and the longest run of busy days is the largest length among runs whose value is `True`: three days in a row with more than 12 tickets.
