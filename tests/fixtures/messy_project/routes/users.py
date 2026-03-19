import sqlalchemy
from sqlalchemy import create_engine
import httpx

print("Loading users route...")


def get_users():
    engine = create_engine("sqlite:///db.sqlite")
    return []
