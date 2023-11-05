import os
import json

import sqlalchemy
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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

random_tree_cache = {}

def init_connection_engine(local=False):
    prepend_str = '/Users/allent/' if local else ''
    return sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username='root' if local else os.environ['TREE_DB_USER'],
            password=os.environ['TREE_DB_PASS'],
            database="publictrees",
            query={
                "unix_socket": f"{prepend_str}/cloudsql/{os.environ['TREE_DB_CONNECTION_STR']}"
            }
        ),
    )


@app.get("/random/")
async def get_random_tree(request: Request):
    ip_address = request.client.host
    ip_hash = sum([int(x) for x in ip_address if x.isdigit()]) % 11
    if ip_hash in random_tree_cache:
        return random_tree_cache[ip_hash]
    else:
        sql = f"""
            SELECT
                ST_LATITUDE(location) AS lat,
                ST_LONGITUDE(location) AS lng
            FROM trees
            WHERE id % 11 = :ip_hash
        """
        with init_connection_engine(LOCAL).connect() as conn:
            random_tree_cache[ip_hash] = conn.execute(
                sqlalchemy.text(sql),
                {'ip_hash': ip_hash}
            ).mappings().all()
        return random_tree_cache[ip_hash]


@app.get("/tree/{tree_id}")
async def get_tree(tree_id):
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
                        'url',
                        CONCAT('https://storage.googleapis.com/public-tree-map-images/', hashed_original_url, '.',
                               extension),
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
    with init_connection_engine(LOCAL).connect() as conn:
        resultset = conn.execute(sqlalchemy.text(sql), {'tree_id': tree_id}).mappings()
        result = resultset.fetchone()

    if result:
        result = dict(result)
        result['images'] = json.loads(result['images'])
        return result


@app.get("/trees/")
async def get_trees(lat1, lng1, lat2, lng2, lat3, lng3, lat4, lng4):
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

    with init_connection_engine(LOCAL).connect() as conn:
        resultset = conn.execute(
            sqlalchemy.text(sql),
            {'polygon': polygon_str}
        ).mappings()
        results = resultset.fetchall()

    if results:
        results = [dict(r) for r in results]
        for tree in results:
            tree['heritage'] = True if tree['heritage'] else False
    return results

