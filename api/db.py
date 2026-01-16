import pandas as pd
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "exam_timetabling",
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def query_df(sql, params=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or [])
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(rows)

