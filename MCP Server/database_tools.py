# db_tools.py
import sqlite3
import os
import csv
from mcp.server.fastmcp import FastMCP as MCP
mcp = MCP("Database Tools")

# Database file inside sandbox
DB_PATH = os.path.abspath("./workspace/database.db")

# Collect all tools here
tools = []


def _get_conn():
    """Create a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def _run_sql(query: str, params: tuple = ()) -> dict:
    """
    Helper to run SQL queries safely.
    Returns rows for SELECT queries, otherwise just success.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(query, params)

        rows = []
        if query.strip().lower().startswith("select"):
            rows = cur.fetchall()

        conn.commit()
        conn.close()

        return {"rows": rows, "status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools)
def run_query(query: str) -> dict:
    """
    Run a raw SQL query against the database.
    SELECT queries return rows, others return success.
    """
    return _run_sql(query)


@mcp.tool(tools)
def init_db(schema: str) -> dict:
    """
    Initialize or reset the database with a schema.
    Example:
    CREATE TABLE users(id INTEGER, name TEXT);
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.executescript(schema)
        conn.commit()
        conn.close()
        return {"status": "Database initialized successfully."}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools)
def list_tables() -> dict:
    """
    List all tables in the database.
    """
    return _run_sql("SELECT name FROM sqlite_master WHERE type='table';")


@mcp.tool(tools)
def describe_table(table: str) -> dict:
    """
    Describe a table (columns and types).
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table});")
        columns = [{"name": row[1], "type": row[2]} for row in cur.fetchall()]
        conn.close()
        return {"columns": columns}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools)
def insert_data(table: str, values: dict) -> dict:
    """
    Insert a row safely into a table.
    Example:
    insert_data("users", {"id": 1, "name": "Alice"})
    """
    try:
        cols = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        return _run_sql(sql, tuple(values.values()))
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools)
def export_to_csv(table: str, filename: str) -> dict:
    """
    Export a table to CSV inside workspace.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
        conn.close()

        path = os.path.join("./workspace", filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return {"status": f"Exported {table} to {filename}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools)
def import_from_csv(table: str, filename: str) -> dict:
    """
    Import rows from a CSV file into a table.
    """
    try:
        path = os.path.join("./workspace", filename)
        conn = _get_conn()
        cur = conn.cursor()
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)  # first row = column names
            for row in reader:
                placeholders = ", ".join(["?"] * len(row))
                sql = f"INSERT INTO {table} ({', '.join(headers)}) VALUES ({placeholders})"
                cur.execute(sql, row)
        conn.commit()
        conn.close()
        return {"status": f"Imported CSV {filename} into {table}"}
    except Exception as e:
        return {"error": str(e)}
