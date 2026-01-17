# db.py - PostgreSQL version for Render.com
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database configuration from environment variables
DB_CONFIG = {
    "host": os.environ.get("PGHOST"),
    "port": int(os.environ.get("PGPORT", 5432)),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", ""),
    "database": os.environ.get("PGDATABASE", "exam_timetabling"),
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
            sslmode='require'  # Required for Render
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def query_df(sql, params=None):
    """
    Execute SQL query and return results as pandas DataFrame
    
    Args:
        sql: SQL query string
        params: Query parameters (list or tuple)
    
    Returns:
        pandas DataFrame with query results
    """
    conn = None
    try:
        conn = get_conn()
        
        # Use RealDictCursor to get results as dictionaries
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params or [])
        
        # Fetch all results
        rows = cur.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        cur.close()
        return df
        
    except Exception as e:
        print(f"Query error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(sql, params=None):
    """
    Execute INSERT/UPDATE/DELETE query
    
    Args:
        sql: SQL query string
        params: Query parameters (list or tuple)
    
    Returns:
        Number of affected rows
    """
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
