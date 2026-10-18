"""Riverton bike-share dashboard (Project 15).
Run it with:  streamlit run dashboard.py
It reads bikes.sqlite, which pipeline.py keeps up to date."""
import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Riverton bikes", layout="wide")


@st.cache_data(ttl=600)
def load(db="bikes.sqlite"):
    with sqlite3.connect(db) as con:
        trips = pd.read_sql("""
            SELECT t.*, s.neighborhood FROM trips AS t
            JOIN stations AS s ON s.station_id = t.start_station""",
            con, parse_dates=["started_at"])
        stations = pd.read_sql("SELECT * FROM stations", con)
        loads = pd.read_sql("SELECT * FROM loads", con)
    trips["day"] = trips["started_at"].dt.normalize()
    trips["hour"] = trips["started_at"].dt.hour
    return trips, stations, loads


trips, stations, loads = load()
st.title("Riverton Bikes: the last four weeks")

hoods = sorted(trips["neighborhood"].unique())
chosen = st.sidebar.multiselect("Start neighborhood", hoods,
                                default=hoods)
rider = st.sidebar.radio("Riders", ["all", "member", "casual"])
view = trips[trips["neighborhood"].isin(chosen)]
if rider != "all":
    view = view[view["rider"] == rider]

days = view["day"].nunique()
a, b, c, d = st.columns(4)
a.metric("Trips", f"{len(view):,}")
b.metric("Trips per day", f"{len(view) / max(days, 1):,.0f}")
c.metric("Members", f"{(view['rider'] == 'member').mean():.0%}")
d.metric("Median trip", f"{view['duration_min'].median():.0f} min")

left, right = st.columns(2)
left.subheader("Trips per day")
left.bar_chart(view.groupby(["day", "rider"]).size().unstack("rider"))
right.subheader("Trips by hour")
right.line_chart(view.groupby(["hour", "rider"]).size()
                 .unstack("rider"))

st.subheader("Busiest start stations")
busiest = (view.groupby("start_station").size().rename("trips")
           .reset_index().merge(stations, left_on="start_station",
                                right_on="station_id")
           .nlargest(8, "trips")[["name", "neighborhood", "trips"]])
st.dataframe(busiest, hide_index=True)

last = loads["day"].max()
st.caption(f"Data through {last}; loaded {loads['loaded_at'].max()}. "
           f"{len(loads)} days in the database.")
