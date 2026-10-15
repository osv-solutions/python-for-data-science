"""Code from "5.7 SQLAlchemy and other databases" that is shown in the book but not run on its own:
it needs your own data, a server or extra setup, or it is one step of an example
that the book builds up gradually. See the book for details."""

import os
from sqlalchemy import create_engine

user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
host = "analytics.example.com"
url = f"postgresql+psycopg://{user}:{password}@{host}:5432/sales"
engine = create_engine(url)
