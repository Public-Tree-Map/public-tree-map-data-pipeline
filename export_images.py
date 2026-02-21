"""One-time script: export the images table from Cloud SQL to data/images.csv.

Prerequisites (same as the old local-dev workflow):
  1. cloud-sql-proxy running against lively-sentry-336718:us-west1:public-tree-map-db
  2. TREE_DB_PASS and TREE_DB_CONNECTION_STR env vars set

Usage:
    python export_images.py
"""

import csv
import os
import sys

import pymysql


def main():
    socket_dir = "/tmp"
    connection_str = os.environ["TREE_DB_CONNECTION_STR"]
    conn = pymysql.connect(
        unix_socket=f"{socket_dir}/{connection_str}",
        user="root",
        password=os.environ["TREE_DB_PASS"],
        database="publictrees",
        cursorclass=pymysql.cursors.DictCursor,
    )

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT species_id, original_url, author, author_url FROM images")
        rows = cursor.fetchall()

    if not rows:
        print("No rows found in images table.", file=sys.stderr)
        return

    out_path = "data/images.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["species_id", "original_url", "author", "author_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
