import json
import sqlite3
import time
from typing import List

from fastapi import FastAPI, Depends, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from database import get_db

# In-memory cache for unfiltered heatmap (pre-serialized JSON bytes)
_heatmap_json: bytes | None = None
_heatmap_cache_time: float = 0
_HEATMAP_TTL = 3600  # 1 hour

# In-memory cache for cities (pre-serialized JSON bytes)
_cities_json: bytes | None = None
_cities_cache_time: float = 0
_CITIES_TTL = 3600  # 1 hour

app = FastAPI()
origins = [
    "*",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    GZipMiddleware,
    minimum_size=500
)


@app.get("/species/all")
async def get_species(db: sqlite3.Connection = Depends(get_db)):
    sql = """
        SELECT
            LOWER(species.common_name) AS common_name,
            LOWER(species.botanical_name) AS botanical_name,
            species.id,
            COUNT(*) AS cnt
        FROM trees
        INNER JOIN species ON trees.species_id = species.id
        WHERE LOWER(common_name) != 'vacant site'
        GROUP BY 1, 2, 3
    """
    rows = db.execute(sql).fetchall()

    result_dicts = []
    for row in rows:
        d = dict(row)
        d['botanical_name'] = str.title(d['botanical_name'])
        d['common_name'] = str.title(d['common_name'])
        result_dicts.append(d)

    return sorted(result_dicts, key=lambda x: x['common_name'])


@app.get("/species/{species_id}")
async def get_trees_by_species(species_id, db: sqlite3.Connection = Depends(get_db)):
    sql = """
        SELECT lat AS latitude, lng AS longitude
        FROM trees
        WHERE species_id = ?
    """
    rows = db.execute(sql, (species_id,)).fetchall()
    return [dict(r) for r in rows]


@app.get("/random/")
async def get_random_tree(species_id: List[int] | None = Query(default=None), db: sqlite3.Connection = Depends(get_db)):
    if species_id is not None:
        placeholders = ",".join("?" for _ in species_id)
        sql = f"""
            SELECT
                ROUND(lat, 3) AS lat,
                ROUND(lng, 3) AS lng,
                CAST(COUNT(*) AS REAL) / MAX(COUNT(*)) OVER () AS intensity
            FROM trees
            WHERE species_id IN ({placeholders})
            GROUP BY 1, 2
        """
        rows = db.execute(sql, species_id).fetchall()
        return [dict(r) for r in rows]

    # Unfiltered: use precomputed heatmap_cache table with in-memory TTL
    global _heatmap_json, _heatmap_cache_time
    now = time.monotonic()
    if _heatmap_json is not None and (now - _heatmap_cache_time) < _HEATMAP_TTL:
        return Response(content=_heatmap_json, media_type="application/json")

    rows = db.execute("SELECT lat, lng, intensity FROM heatmap_cache").fetchall()
    _heatmap_json = json.dumps([dict(r) for r in rows]).encode()
    _heatmap_cache_time = now
    return Response(content=_heatmap_json, media_type="application/json")


@app.get("/cities/")
async def get_cities(db: sqlite3.Connection = Depends(get_db)):
    global _cities_json, _cities_cache_time
    now = time.monotonic()
    if _cities_json is not None and (now - _cities_cache_time) < _CITIES_TTL:
        return Response(content=_cities_json, media_type="application/json")

    rows = db.execute("SELECT city, tree_count, lat, lng FROM cities_cache ORDER BY tree_count DESC").fetchall()
    _cities_json = json.dumps([dict(r) for r in rows]).encode()
    _cities_cache_time = now
    return Response(content=_cities_json, media_type="application/json")


@app.get("/tree/{tree_id}")
async def get_tree(tree_id, db: sqlite3.Connection = Depends(get_db)):
    sql = """
        SELECT
            botanical_name AS name_botanical,
            common_name AS name_common,
            family_botanical_name AS family_name_botanical,
            family_common_name AS family_name_common,
            address,
            city,
            state,
            diameter_min_in,
            diameter_max_in,
            exact_diameter,
            height_min_ft,
            height_max_ft,
            exact_height,
            native AS nativity,
            estimated_value,
            tree_condition,
            shade_production,
            irrigation_requirements,
            form,
            type,
            iucn_status,
            iucn_doi_or_url,
            lat AS latitude,
            lng AS longitude,
            heritage,
            heritage_number AS heritageNumber,
            heritage_text AS heritageText,
            heritage_year AS heritageYear,
            json_group_array(
                json_object(
                    'url', i.original_url,
                    'author', json_object(
                        'name', i.author,
                        'url', i.author_url
                    )
                )
            ) AS images,
            T.id AS tree_id
        FROM trees T
        INNER JOIN species s ON T.species_id = s.id
        LEFT JOIN images i ON s.id = i.species_id
        WHERE T.id = ?
        GROUP BY T.id
    """
    row = db.execute(sql, (tree_id,)).fetchone()

    if row:
        result = dict(row)
        result['images'] = json.loads(result['images'])
        # Filter out null-url entries from LEFT JOIN with no matching images
        result['images'] = [img for img in result['images'] if img.get('url') is not None]
        return result


@app.get("/trees/")
async def get_trees(lat1, lng1, lat2, lng2, lat3, lng3, lat4, lng4, exclude_vacant: bool = True, db: sqlite3.Connection = Depends(get_db)):
    lats = [float(lat1), float(lat2), float(lat3), float(lat4)]
    lngs = [float(lng1), float(lng2), float(lng3), float(lng4)]

    min_lat = min(lats)
    max_lat = max(lats)
    min_lng = min(lngs)
    max_lng = max(lngs)

    sql = """
        SELECT
            T.id AS tree_id,
            botanical_name AS name_botanical,
            common_name AS name_common,
            family_botanical_name AS family_name_botanical,
            family_common_name AS family_name_common,
            iucn_status,
            native AS nativity,
            T.lat AS latitude,
            T.lng AS longitude,
            heritage
        FROM trees T
        INNER JOIN trees_spatial sp ON T.id = sp.id
        INNER JOIN species s ON T.species_id = s.id
        WHERE
            sp.min_lat >= ? AND sp.max_lat <= ?
            AND sp.min_lng >= ? AND sp.max_lng <= ?
    """
    params = [min_lat, max_lat, min_lng, max_lng]
    if exclude_vacant:
        sql += "            AND LOWER(s.common_name) != 'vacant site'\n"
    rows = db.execute(sql, params).fetchall()

    results = [dict(r) for r in rows]
    for tree in results:
        tree['heritage'] = True if tree['heritage'] else False
    return results
