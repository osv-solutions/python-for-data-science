"""Code from "17.4 Maps" that is shown in the book but not run on its own:
it needs your own data, a server or extra setup, or it is one step of an example
that the book builds up gradually. See the book for details."""

fig = px.scatter_map(requests, lat="latitude", lon="longitude",
                     color="type", zoom=11,
                     map_style="carto-positron")
fig.show()
