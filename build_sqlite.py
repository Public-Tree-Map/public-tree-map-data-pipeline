"""Build trees.db from local files — no MySQL dependency.

Usage:
    python build_sqlite.py [--la-datapath PATH] [--output trees.db]

Data sources:
    - data/species_attributes.csv     → species table
    - stiles.trees.csv (or fresh parse via --la-datapath) → LA trees
    - data/trees.csv                  → Santa Monica trees (via sm_parser)
    - data/images.csv                 → images table

Outputs:
    trees.db with tables: species, trees, trees_spatial (R-tree),
    images, heatmap_cache, cities_cache
"""

import argparse
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

from parse_la_data import SpeciesMatcher
from sm_parser import parse_trees as parse_sm_trees


def sanitize(val):
    """Convert NaN/NaT to None for SQLite compatibility."""
    if val is None:
        return None
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    return val


def to_int(val):
    if val is None:
        return None
    if isinstance(val, float):
        if np.isnan(val):
            return None
        return int(val)
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def build_species_table(conn, species_df):
    """Write species table from species_attributes.csv DataFrame."""
    print("Building species table...")
    conn.execute("DROP TABLE IF EXISTS species")
    conn.execute("""
        CREATE TABLE species (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            botanical_name TEXT NOT NULL UNIQUE,
            common_name TEXT,
            family_botanical_name TEXT,
            family_common_name TEXT,
            native TEXT,
            eol_id INTEGER,
            eol_overview_url TEXT,
            simplified_iucn_status TEXT,
            iucn_status TEXT,
            iucn_doi_or_url TEXT,
            shade_production TEXT,
            form TEXT,
            type TEXT,
            cal_ipc_url TEXT,
            irrigation_requirements TEXT,
            species_id INTEGER
        )
    """)

    rows = []
    for row in species_df.itertuples():
        rows.append((
            sanitize(row.botanical_name),
            sanitize(row.common_name),
            sanitize(row.family_botanical_name),
            sanitize(row.family_common_name),
            sanitize(row.native),
            to_int(row.EOL_ID) if hasattr(row, 'EOL_ID') else to_int(getattr(row, 'eol_id', None)),
            sanitize(getattr(row, 'EOL_overview_URL', None) or getattr(row, 'eol_overview_url', None)),
            sanitize(getattr(row, 'simplified_IUCN_status', None) or getattr(row, 'simplified_iucn_status', None)),
            sanitize(getattr(row, 'IUCN_status', None) or getattr(row, 'iucn_status', None)),
            sanitize(getattr(row, 'IUCN_DOI_or_URL', None) or getattr(row, 'iucn_doi_or_url', None)),
            sanitize(row.shade_production),
            sanitize(row.form),
            sanitize(row.type),
            sanitize(getattr(row, 'CAL_IPC_url', None) or getattr(row, 'cal_ipc_url', None)),
            sanitize(getattr(row, 'Irrigation_Requirements', None) or getattr(row, 'irrigation_requirements', None)),
            to_int(getattr(row, '_16', None)),  # Species ID column
        ))

    conn.executemany("""
        INSERT INTO species (
            botanical_name, common_name, family_botanical_name, family_common_name,
            native, eol_id, eol_overview_url, simplified_iucn_status, iucn_status,
            iucn_doi_or_url, shade_production, form, type, cal_ipc_url,
            irrigation_requirements, species_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    print(f"  {len(rows)} species inserted")

    # Return botanical_name → id mapping
    cur = conn.execute("SELECT id, botanical_name FROM species")
    return {row[1]: row[0] for row in cur.fetchall()}


def load_la_trees(la_datapath):
    """Load LA trees either from pre-generated CSV or by parsing fresh."""
    stiles_csv = "stiles.trees.csv"

    if la_datapath:
        print(f"Parsing LA trees fresh from {la_datapath}...")
        from parse_la_data import StilesDataParser
        import geopandas as gpd
        from shapely.geometry import Point

        parser = StilesDataParser(la_datapath)
        df = parser.parse_all()

        # Filter to LA bounding box
        geom = gpd.GeoSeries(df['geometry'])
        df = df[(geom.y >= 32) & (geom.y <= 36) & (geom.x >= -119) & (geom.x <= -117)]

        df['latitude'] = df.geometry.y
        df['longitude'] = df.geometry.x
        return df

    if os.path.exists(stiles_csv):
        print(f"Loading pre-generated {stiles_csv}...")
        return pd.read_csv(stiles_csv)

    print(f"ERROR: No LA tree data found. Provide --la-datapath or place {stiles_csv} in project root.",
          file=sys.stderr)
    sys.exit(1)


def load_sm_trees():
    """Load Santa Monica trees from data/trees.csv."""
    print("Parsing Santa Monica trees...")
    sm_df = pd.read_csv("data/trees.csv")
    return parse_sm_trees(df=sm_df)


def build_trees_table(conn, la_df, sm_df, species_id_map):
    """Write unified trees table."""
    print("Building trees table...")
    conn.execute("DROP TABLE IF EXISTS trees")
    conn.execute("""
        CREATE TABLE trees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tree_id INTEGER,
            species_id INTEGER NOT NULL,
            address TEXT,
            state TEXT,
            city TEXT,
            tree_condition TEXT,
            diameter_min_in REAL,
            diameter_max_in REAL,
            exact_diameter REAL,
            height_min_ft REAL,
            height_max_ft REAL,
            exact_height REAL,
            estimated_value REAL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            heritage INTEGER DEFAULT 0,
            heritage_year INTEGER,
            heritage_number INTEGER,
            heritage_text TEXT,
            FOREIGN KEY (species_id) REFERENCES species(id)
        )
    """)

    # --- LA trees ---
    # Match species
    matcher = SpeciesMatcher(la_df)
    la_matched = matcher.match()
    la_matched['species_id'] = la_matched['botanical_name'].map(species_id_map)
    la_matched = la_matched.dropna(subset=['species_id'])
    la_matched['species_id'] = la_matched['species_id'].astype(int)

    la_rows = []
    for row in la_matched.itertuples():
        la_rows.append((
            to_int(getattr(row, 'tree_id', None)),
            int(row.species_id),
            sanitize(getattr(row, 'address', None)),
            'CA',
            sanitize(getattr(row, 'city', None)),
            sanitize(getattr(row, 'condition', None)),
            sanitize(getattr(row, 'diameter_min_in', None)),
            sanitize(getattr(row, 'diameter_max_in', None)),
            sanitize(getattr(row, 'exact_diameter', None)),
            sanitize(getattr(row, 'height_min_ft', None)),
            sanitize(getattr(row, 'height_max_ft', None)),
            sanitize(getattr(row, 'exact_height', None)),
            sanitize(getattr(row, 'estimated_value', None)),
            float(row.latitude) if pd.notna(getattr(row, 'latitude', None)) else None,
            float(row.longitude) if pd.notna(getattr(row, 'longitude', None)) else None,
            0,   # heritage
            None, None, None,
        ))

    print(f"  Inserting {len(la_rows)} LA trees...")
    conn.executemany("""
        INSERT INTO trees (
            tree_id, species_id, address, state, city, tree_condition,
            diameter_min_in, diameter_max_in, exact_diameter,
            height_min_ft, height_max_ft, exact_height,
            estimated_value, lat, lng, heritage,
            heritage_year, heritage_number, heritage_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, la_rows)
    conn.commit()

    # --- SM trees ---
    sm_matcher = SpeciesMatcher(sm_df)
    sm_matched = sm_matcher.match()
    sm_matched['species_id'] = sm_matched['botanical_name'].map(species_id_map)
    sm_matched = sm_matched.dropna(subset=['species_id'])
    sm_matched['species_id'] = sm_matched['species_id'].astype(int)

    sm_rows = []
    for row in sm_matched.itertuples():
        sm_rows.append((
            to_int(getattr(row, 'tree_id', None)),
            int(row.species_id),
            sanitize(getattr(row, 'address', None)),
            sanitize(getattr(row, 'state', None)),
            sanitize(getattr(row, 'city', None)),
            None,  # tree_condition
            sanitize(getattr(row, 'diameter_min_in', None)),
            sanitize(getattr(row, 'diameter_max_in', None)),
            None,  # exact_diameter
            sanitize(getattr(row, 'height_min_ft', None)),
            sanitize(getattr(row, 'height_max_ft', None)),
            None,  # exact_height
            None,  # estimated_value
            float(row.latitude) if pd.notna(getattr(row, 'latitude', None)) else None,
            float(row.longitude) if pd.notna(getattr(row, 'longitude', None)) else None,
            1 if getattr(row, 'heritage', False) else 0,
            to_int(getattr(row, 'heritageYear', None)),
            to_int(getattr(row, 'heritageNumber', None)),
            sanitize(getattr(row, 'heritageText', None)),
        ))

    print(f"  Inserting {len(sm_rows)} SM trees...")
    conn.executemany("""
        INSERT INTO trees (
            tree_id, species_id, address, state, city, tree_condition,
            diameter_min_in, diameter_max_in, exact_diameter,
            height_min_ft, height_max_ft, exact_height,
            estimated_value, lat, lng, heritage,
            heritage_year, heritage_number, heritage_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sm_rows)
    conn.commit()

    total = len(la_rows) + len(sm_rows)
    print(f"  {total} total trees inserted")
    return total


def build_spatial_index(conn):
    """Create R-tree spatial index for bounding-box queries."""
    print("Building R-tree spatial index...")
    conn.execute("DROP TABLE IF EXISTS trees_spatial")
    conn.execute("""
        CREATE VIRTUAL TABLE trees_spatial USING rtree(
            id,
            min_lat, max_lat,
            min_lng, max_lng
        )
    """)
    conn.execute("""
        INSERT INTO trees_spatial (id, min_lat, max_lat, min_lng, max_lng)
        SELECT id, lat, lat, lng, lng FROM trees
        WHERE lat IS NOT NULL AND lng IS NOT NULL
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM trees_spatial").fetchone()[0]
    print(f"  {count} entries in R-tree")


def build_images_table(conn):
    """Import images from data/images.csv."""
    images_csv = "data/images.csv"
    if not os.path.exists(images_csv):
        print(f"  WARNING: {images_csv} not found — skipping images table")
        conn.execute("DROP TABLE IF EXISTS images")
        conn.execute("""
            CREATE TABLE images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER NOT NULL,
                original_url TEXT,
                author TEXT,
                author_url TEXT
            )
        """)
        conn.commit()
        return

    print("Building images table...")
    conn.execute("DROP TABLE IF EXISTS images")
    conn.execute("""
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species_id INTEGER NOT NULL,
            original_url TEXT,
            author TEXT,
            author_url TEXT
        )
    """)

    img_df = pd.read_csv(images_csv)
    rows = []
    for row in img_df.itertuples():
        rows.append((
            to_int(row.species_id),
            sanitize(getattr(row, 'original_url', None)),
            sanitize(getattr(row, 'author', None)),
            sanitize(getattr(row, 'author_url', None)),
        ))

    conn.executemany(
        "INSERT INTO images (species_id, original_url, author, author_url) VALUES (?, ?, ?, ?)",
        rows
    )
    conn.commit()
    print(f"  {len(rows)} images inserted")


def build_heatmap_cache(conn):
    """Precompute heatmap intensity data."""
    print("Building heatmap_cache...")
    conn.execute("DROP TABLE IF EXISTS heatmap_cache")
    conn.execute("""
        CREATE TABLE heatmap_cache (
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            intensity REAL NOT NULL,
            PRIMARY KEY (lat, lng)
        )
    """)
    conn.execute("""
        INSERT INTO heatmap_cache (lat, lng, intensity)
        SELECT
            ROUND(lat, 3) AS lat,
            ROUND(lng, 3) AS lng,
            CAST(COUNT(*) AS REAL) / (SELECT MAX(cnt) FROM (
                SELECT COUNT(*) AS cnt FROM trees GROUP BY ROUND(lat, 3), ROUND(lng, 3)
            )) AS intensity
        FROM trees
        GROUP BY 1, 2
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM heatmap_cache").fetchone()[0]
    print(f"  {count} heatmap cells")


def build_cities_cache(conn):
    """Precompute city tree counts and centroids."""
    print("Building cities_cache...")
    conn.execute("DROP TABLE IF EXISTS cities_cache")
    conn.execute("""
        CREATE TABLE cities_cache (
            city TEXT NOT NULL PRIMARY KEY,
            tree_count INTEGER NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO cities_cache (city, tree_count, lat, lng)
        SELECT
            city,
            COUNT(*) AS tree_count,
            AVG(CASE WHEN lat != 0 THEN lat END) AS lat,
            AVG(CASE WHEN lng != 0 THEN lng END) AS lng
        FROM trees
        GROUP BY city
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM cities_cache").fetchone()[0]
    print(f"  {count} cities")


def build_indexes(conn):
    """Create secondary indexes."""
    print("Creating indexes...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_trees_species_id ON trees(species_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_images_species_id ON images(species_id)")
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Build trees.db from local files")
    parser.add_argument("--la-datapath", type=str, default=None,
                        help="Path to LA tree geojson/csv data dirs (optional; uses stiles.trees.csv if absent)")
    parser.add_argument("--output", type=str, default="trees.db",
                        help="Output SQLite database path (default: trees.db)")
    args = parser.parse_args()

    output = args.output
    if os.path.exists(output):
        os.remove(output)

    start = time.time()
    conn = sqlite3.connect(output)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    # 1. Species
    species_df = pd.read_csv("data/species_attributes.csv").drop_duplicates("botanical_name")
    species_id_map = build_species_table(conn, species_df)

    # 2. LA trees
    la_df = load_la_trees(args.la_datapath)

    # 3. SM trees
    sm_df = load_sm_trees()

    # 4–6. Trees table
    build_trees_table(conn, la_df, sm_df, species_id_map)

    # 7. R-tree
    build_spatial_index(conn)

    # 8. Images
    build_images_table(conn)

    # 9. Caches
    build_heatmap_cache(conn)
    build_cities_cache(conn)

    # 10. Indexes
    build_indexes(conn)

    conn.execute("PRAGMA optimize")
    conn.close()

    elapsed = time.time() - start
    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"\nDone: {output} ({size_mb:.1f} MB) in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
