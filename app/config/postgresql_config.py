import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_DBNAME = os.getenv("PG_DBNAME", "lifematch_db")
PG_USER = os.getenv("PG_USER", "leejunho")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

_db_pool = None

def init_db_pool(minconn: int = 1, maxconn: int = 5):
    global _db_pool
    if _db_pool is None:
        _db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn, maxconn,
            host=PG_HOST, port=PG_PORT, dbname=PG_DBNAME, user=PG_USER, password=PG_PASSWORD
        )

def get_db_conn():
    if _db_pool is None:
        init_db_pool()
    return _db_pool.getconn()

def put_db_conn(conn):
    if _db_pool:
        _db_pool.putconn(conn)