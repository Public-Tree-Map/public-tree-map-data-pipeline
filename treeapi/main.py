import json
from typing import List

import sqlalchemy
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from database import SessionLocal

app = FastAPI()
origins = [
    "*",
    "http://localhost",
    "http://localhost:8080",
]

LOCAL = True

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Async engine setup for SQLAlchemy 1.4+

@app.get("/species/all")
async def get_species(db: Session = Depends(get_db)):
    import time
    sql = f"""
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
    result_set = db.execute(sqlalchemy.text(sql)).mappings().all()

    result_dicts = []
    for result in result_set:
        result = dict(result)
        result['botanical_name'] = str.title(result['botanical_name'])
        result['common_name'] = str.title(result['common_name'])
        result_dicts.append(result)

    return sorted(result_dicts, key=lambda x: x['common_name'])


@app.get("/species/{species_id}")
async def get_trees(species_id, db: Session = Depends(get_db)):
    sql = f"""
        SELECT 
            ST_LATITUDE(location) AS latitude,
            ST_LONGITUDE(location) AS longitude
        FROM trees T
        WHERE
            species_id = :species_id
    """

    return db.execute(
        sqlalchemy.text(sql),
        {'species_id': species_id}
    ).mappings().fetchall()


@app.get("/random/")
async def get_random_tree(species_id: List[int] | None = Query(default=None), db: Session = Depends(get_db)):
    where_str = ""
    args = None
    if species_id is not None:
        where_str = f"""
            AND species_id IN :species_ids
        """
        args = {'species_ids': tuple(species_id)}
    sql = f"""
        SELECT
            ROUND(ST_LATITUDE(location), 3) AS lat,
            ROUND(ST_LONGITUDE(location), 3) AS lng,
            COUNT(*) / MAX(COUNT(*)) OVER () AS intensity
        FROM
            trees
        WHERE 1 = 1 {where_str}
        GROUP BY 1, 2
    """
    return db.execute(
        sqlalchemy.text(sql),
        args
    ).mappings().all()


@app.get("/tree/{tree_id}")
async def get_tree(tree_id, db: Session = Depends(get_db)):
    sql = f"""
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
            ST_LATITUDE(location) AS latitude,
            ST_LONGITUDE(location) AS longitude,
            heritage,
            heritage_number AS heritageNumber,
            heritage_text AS heritageText,
            heritage_year AS heritageYear,
            JSON_ARRAYAGG(
                JSON_OBJECT(
                        'url', original_url,
                        'author', JSON_OBJECT(
                                'name', author,
                                'url', author_url
                            )
                    )
            ) AS images,
            T.id AS tree_id
        FROM trees T
        INNER JOIN species s on T.species_id = s.id
        LEFT JOIN images i on s.id = i.species_id
        WHERE
            T.id = :tree_id
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27
    """

    resultset = db.execute(sqlalchemy.text(sql), {'tree_id': tree_id}).mappings()
    result = resultset.fetchone()

    if result:
        result = dict(result)
        result['images'] = json.loads(result['images'])
        return result


@app.get("/trees/")
async def get_trees(lat1, lng1, lat2, lng2, lat3, lng3, lat4, lng4, db: Session = Depends(get_db)):
    lats = [lat1, lat2, lat3, lat4]
    lngs = [lng1, lng2, lng3, lng4]
    lat_lngs = []
    for lat, lng in zip(lats, lngs):
        lat_lngs.append(f'{lat} {lng}')
    csv = ','.join(lat_lngs)
    polygon_str = f'POLYGON(({csv}, {lat_lngs[0]}))'
    sql = f"""
        SELECT 
            T.id AS tree_id,
            botanical_name AS name_botanical,
            common_name AS name_common,
            family_botanical_name AS family_name_botanical,
            family_common_name AS family_name_common,
            iucn_status,
            native AS nativity,
            ST_LATITUDE(location) AS latitude,
            ST_LONGITUDE(location) AS longitude,
            heritage
        FROM trees T
        INNER JOIN species s on T.species_id = s.id
        WHERE
            MBRContains(
                ST_GeomFromText(:polygon, 4269),
                location
            ) AND
            T.id IS NOT NULL
    """

    resultset = db.execute(
        sqlalchemy.text(sql),
        {'polygon': polygon_str}
    ).mappings()
    results = resultset.fetchall()

    if results:
        results = [dict(r) for r in results]
        for tree in results:
            tree['heritage'] = True if tree['heritage'] else False
    return results

