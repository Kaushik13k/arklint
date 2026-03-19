import psycopg2
import requests

print("Loading orders route...")


def get_orders():
    conn = psycopg2.connect("dbname=mydb")
    return []
