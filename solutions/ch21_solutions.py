"""Solutions to the Chapter 21 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch21_solutions.py

The explanations are in ch21_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

bikes = pd.read_csv("data/bike_daily.csv", parse_dates=["date"],
                    index_col="date")
daily = bikes.asfreq("D")
daily["rides"] = daily["rides"].interpolate(method="time")
daily["holiday"] = daily["holiday"].astype("boolean").fillna(False)
rides = daily["rides"]
smooth28 = rides.rolling(28, center=True).mean()
train = daily.loc[:"2025-09-30"]
test = daily.loc["2025-10-01":]
actual = test["rides"]


def errors(forecast):
    e = actual - forecast
    return {"MAE": e.abs().mean(),
            "MAPE %": (e / actual).abs().mean() * 100}


def features(df, weather=True):
    X = pd.DataFrame({"t": (df.index - daily.index[0]).days,
                      "holiday": df["holiday"].astype(int)},
                     index=df.index)
    if weather:
        X["temp"] = df["temp_max_c"]
        X["rain"] = np.log1p(df["precip_mm"])
    days = pd.Categorical(df.index.dayofweek, categories=range(7))
    dow = pd.get_dummies(days, prefix="dow", dtype=int)
    return X.join(dow.set_index(df.index))

# %% Exercise 21.1
weeks = rides.loc["2025"].resample("W").sum()
weeks = weeks.iloc[1:-1]                     # drop the partial weeks
print("busiest:", weeks.idxmax().date(), int(weeks.max()))
print("quietest:", weeks.idxmin().date(), int(weeks.min()))
monthly = rides.loc["2025"].resample("MS").mean()
print("best month:", monthly.idxmax().strftime("%B"),
      round(monthly.max()))

# %% Exercise 21.2
year = daily.loc["2025"]
fig, axes = plt.subplots(2, 1, figsize=(6.6, 4), sharex=True)
axes[0].plot(year["rides"].rolling(7).mean(), color="#1d5c8c")
axes[0].set_ylabel("Rides (7-day mean)")
axes[1].plot(year["temp_max_c"].rolling(7).mean(), color="#c0582b")
axes[1].set_ylabel("Max temp °C (7-day)")
fig.tight_layout()
plt.show()

# %% Exercise 21.3
level = rides / smooth28
holidays = level[daily["holiday"]].dropna()
by_day = holidays.groupby(holidays.index.strftime("%m-%d")).mean()
print(by_day.round(2).to_frame("factor").T)
print(f"average holiday: {holidays.mean():.2f}")

# %% Exercise 21.4
from statsmodels.tsa.seasonal import seasonal_decompose

weekly = daily[["rides", "precip_mm"]].resample("W").agg(
    {"rides": "sum", "precip_mm": "sum"}).iloc[1:-1]
parts = seasonal_decompose(weekly["rides"], model="multiplicative",
                           period=52)
resid = parts.resid.dropna()
worst = resid.sort_values().index[:3]
print(pd.DataFrame({"resid": resid[worst].round(2),
                    "rain_mm": weekly.loc[worst, "precip_mm"]}))

# %% Exercise 21.5
last4 = train["rides"].iloc[-28:]
by_dow = last4.groupby(last4.index.dayofweek).mean()
weekday_mean = pd.Series(by_dow.loc[actual.index.dayofweek].values,
                         index=actual.index)
print({k: round(float(v), 1) for k, v in errors(weekday_mean).items()})

# %% Exercise 21.6
fit_on = train.dropna(subset=["temp_max_c"])
for weather in [True, False]:
    model = LinearRegression().fit(features(fit_on, weather),
                                   np.log(fit_on["rides"]))
    pred = np.exp(model.predict(features(test, weather)))
    pred = pd.Series(pred, actual.index)
    print(f"weather={weather}:",
          {k: round(float(v), 1) for k, v in errors(pred).items()})

# %% Exercise 21.7
fit_once = LinearRegression().fit(features(fit_on),
                                  np.log(fit_on["rides"]))
rows = []
for start in pd.date_range("2025-10-01", "2025-12-31", freq="7D"):
    week = daily.loc[start:start + pd.Timedelta(days=6)]
    past = daily.loc[:start - pd.Timedelta(days=1)].dropna(
        subset=["temp_max_c"])
    model = LinearRegression().fit(features(past), np.log(past["rides"]))
    for name, m in [("refit", model), ("once", fit_once)]:
        pred = np.exp(m.predict(features(week)))
        rows.append({"week": start.date(), "model": name,
                     "MAE": np.abs(week["rides"] - pred).mean()})
table = pd.DataFrame(rows).pivot(index="week", columns="model",
                                 values="MAE")
print(table.round(0).head(4))
print(table.mean().round(1).to_dict())
