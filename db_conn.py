# db_conn.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_conn():
    dbname=os.getenv("DB_NAME")
    user=os.getenv("DB_USER")
    password=os.getenv("DB_PASSWORD")
    host=os.getenv("DB_HOST")
    port=os.getenv("DB_PORT")

    if port:
        return psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=int(port)
        )
    else:
        return psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host
        )