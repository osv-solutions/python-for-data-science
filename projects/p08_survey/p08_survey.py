"""Project 8 (Intermediate): Customer Survey Analysis

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p08_survey.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and audit
import pandas as pd

raw = pd.read_csv("data/survey_raw.csv")
print(raw.shape)
print(raw.iloc[0])

# %% Step 1: Plan and audit
print(raw.isna().sum()[lambda s: s > 0])

# %% Step 2: Remove the responses that can't be trusted
raw["started"] = pd.to_datetime(raw["started"],
                                format="%m/%d/%Y %H:%M")
raw = raw.sort_values("started")
dup = raw["email"].duplicated(keep="first")
print(dup.sum(), "repeat submissions")

# %% Step 2: Remove the responses that can't be trusted
print(raw["duration_s"].median())
speeder = raw["duration_s"] < raw["duration_s"].median() / 3
print(speeder.sum(), "speeders")

# %% Step 2: Remove the responses that can't be trusted
failed = raw["q3_attention"] != 4
print(failed.sum(), "failed the attention check")
print(pd.crosstab(speeder, failed))

# %% Step 2: Remove the responses that can't be trusted
keep = ~dup & ~speeder & ~failed
survey = raw[keep].drop(columns="q3_attention").reset_index(drop=True)
funnel = pd.Series({"responses": len(raw), "repeats": dup.sum(),
                    "speeders": (speeder & ~dup).sum(),
                    "failed check": (failed & ~dup & ~speeder).sum(),
                    "kept": len(survey)})
print(funnel)

# %% Step 3: Standardize the satisfaction answers
print(survey["q1_satisfaction"].value_counts())

# %% Step 3: Standardize the satisfaction answers
LABELS = ["Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied",
          "Very satisfied"]
digits = {str(k): label for k, label in enumerate(LABELS, start=1)}
sat = survey["q1_satisfaction"].replace(digits)
survey["satisfaction"] = pd.Categorical(sat, categories=LABELS,
                                        ordered=True)
counts = survey["satisfaction"].value_counts(sort=False)
print((counts / counts.sum() * 100).round(1))

# %% Step 3: Standardize the satisfaction answers
top2 = survey["satisfaction"] >= "Satisfied"
print(f"satisfied or very satisfied: {top2.mean():.1%}")

# %% Step 4: Net Promoter Score
survey["nps_group"] = pd.cut(survey["q2_recommend"],
                             bins=[-1, 6, 8, 10],
                             labels=["detractor", "passive",
                                     "promoter"])
shares = survey["nps_group"].value_counts(normalize=True) * 100
nps = shares["promoter"] - shares["detractor"]
print(shares.round(1))
print(f"NPS: {nps:.0f}")

# %% Step 5: The agree-disagree statements
items = ["q3_taste", "q3_price", "q3_delivery", "q3_packaging",
         "q3_website"]
likert = survey[items].rename(columns=lambda c: c.removeprefix("q3_"))
summary = pd.DataFrame({
    "mean": likert.mean(),
    "agree": (likert >= 4).sum() / likert.notna().sum() * 100,
    "disagree": (likert <= 2).sum() / likert.notna().sum() * 100})
print(summary.sort_values("mean").round(1))

# %% Step 5: The agree-disagree statements
import matplotlib.pyplot as plt

shares = likert.apply(lambda s: s.value_counts(normalize=True))
pct = shares.fillna(0).T * 100
pct = pct.loc[summary.sort_values("agree").index]
colors = ["#b2182b", "#ef8a62", "#d9d9d9", "#67a9cf", "#2166ac"]
left = -(pct[1] + pct[2] + pct[3] / 2)
fig, ax = plt.subplots(figsize=(6.4, 2.8))
for k, color in zip(range(1, 6), colors):
    ax.barh(pct.index, pct[k], left=left, color=color,
            label=["Strongly disagree", "Disagree", "Neutral",
                   "Agree", "Strongly agree"][k - 1])
    left += pct[k]
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Percent of respondents")
ax.legend(ncols=3, fontsize=7, loc=(0, 1.02))
plt.show()

# %% Step 6: How customers brew
brew = (survey[["response_id", "q4_brew"]].dropna()
        .assign(method=lambda d: d["q4_brew"].str.split(";"))
        .explode("method"))
print(brew["method"].value_counts().tail(6))

# %% Step 6: How customers brew
other = brew["method"].str.startswith("Other: ")
typed = (brew.loc[other, "method"].str.replace("Other: ", "")
         .str.lower().str.replace(" ", ""))
print(typed.value_counts())

# %% Step 6: How customers brew
nicer = {"aeropress": "AeroPress", "chemex": "Chemex"}
brew.loc[other, "method"] = typed.map(nicer).fillna("Other")
answered = brew["response_id"].nunique()
methods = brew["method"].value_counts() / answered * 100
print(methods.round(1))

# %% Step 7: Age groups and weighting
website = survey["q3_website"]
agree = (website >= 4).astype(float)
survey["agree_website"] = agree.where(website.notna())
by_age = survey.groupby("age_group").agg(
    responses=("response_id", "count"),
    satisfied=("satisfaction", lambda s: (s >= "Satisfied").mean()),
    website=("agree_website", "mean"))
print((by_age * [1, 100, 100]).round(1))

# %% Step 7: Age groups and weighting
ages = pd.read_csv("data/customer_ages.csv", index_col="age_group")
mix = ages.assign(
    sample=survey["age_group"].value_counts(normalize=True))
mix["weight"] = mix["share_of_customers"] / mix["sample"]
print(mix.round(2))

# %% Step 7: Age groups and weighting
survey["weight"] = survey["age_group"].map(mix["weight"])

def weighted_share(flag, weight):
    ok = flag.notna()
    return (flag[ok] * weight[ok]).sum() / weight[ok].sum() * 100

w = survey["weight"]
for name, flag in [("satisfied", top2),
                   ("website easy", survey["agree_website"])]:
    print(f"{name:13} {flag.mean() * 100:5.1f}"
          f" {weighted_share(flag, w):5.1f}")

# %% Step 8: Save the results
with pd.ExcelWriter("survey_report.xlsx") as writer:
    funnel.to_frame("count").to_excel(writer, sheet_name="Cleaning")
    summary.round(1).to_excel(writer, sheet_name="Statements")
    methods.round(1).to_frame("percent").to_excel(
        writer, sheet_name="Brewing")
    mix.round(3).to_excel(writer, sheet_name="Weights")
    survey.drop(columns="q1_satisfaction").to_excel(
        writer, sheet_name="Clean responses", index=False)
print(f"{len(survey)} responses, NPS {nps:.0f}")
