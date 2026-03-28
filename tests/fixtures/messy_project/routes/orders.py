import psycopg2

print("Loading orders route...")


def get_orders():
    conn = psycopg2.connect("dbname=mydb")  # noqa: F841
    return []
