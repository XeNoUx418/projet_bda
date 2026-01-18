import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database configuration updated with your Render credentials
DB_CONFIG = {
    "host": os.environ.get("PGHOST", "dpg-d5m16isoud1c7392ekr0-a.frankfurt-postgres.render.com"),
    "port": int(os.environ.get("PGPORT", 5432)),
    "user": os.environ.get("PGUSER", "bda_user"),
    "password": os.environ.get("PGPASSWORD", "vnrGTEe3alm2PN9ykO0MuFs0ArgomSND"),
    "database": os.environ.get("PGDATABASE", "projet_bda_zo94"),
}

def get_conn():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"],
            sslmode='require'  # Essential for Render connections
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def query_df(sql, params=None):
    """Execute SQL query and return results as pandas DataFrame"""
    conn = None
    try:
        conn = get_conn()
        # Using RealDictCursor ensures the rows are easily converted to a DataFrame
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params or [])
        
        rows = cur.fetchall()
        
        # Logic to return empty DataFrame if no rows are found
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        
        cur.close()
        return df
    except Exception as e:
        print(f"Query error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(sql, params=None):
    """Execute INSERT/UPDATE/DELETE query"""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, params or [])
        conn.commit()
        affected = cur.rowcount
        cur.close()
        return affected
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Execute error: {e}")
        raise
    finally:
        if conn:
            conn.close()
