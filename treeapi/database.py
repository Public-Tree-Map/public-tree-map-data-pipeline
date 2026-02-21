import os
import sqlite3

DB_PATH = os.environ.get("TREE_DB_PATH", "trees.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
