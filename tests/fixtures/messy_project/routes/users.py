from sqlalchemy import create_engine

print("Loading users route...")


def get_users():
    engine = create_engine("sqlite:///db.sqlite")  # noqa: F841
    return []
