import os
import json

import pymysql
from google.cloud.sql.connector import connector
from fastapi import FastAPI

app = FastAPI()


class DBConn(object):
    def __init__(self, password, local=False):
        if local:
            self.connection = pymysql.connect(
                host='localhost',
                password=password,
                db='publictrees',
                user='root'
            )
        else:
            self.connection = connector.connect(
                instance_connection_string=os.environ['TREE_DB_CONNECTION_STR'],
                driver='pymysql',
                user='root',
                password=password,
                db='publictrees'
            )

    def __enter__(self):
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()


@app.get("/random/")
async def get_random_tree():
    sql = f"""
        SELECT
            tree_id,
            name_common,
            name_botanical,
            address,
            city,
            diameter_min_in,
            diameter_max_in,
            exact_diameter,
            height_min_ft,
            height_max_ft,
            exact_height,
            estimated_value,
            tree_condition,
            ST_LATITUDE(location) AS latitude,
            ST_LONGITUDE(location) AS longitude
        FROM trees
        LIMIT 1
    """
    with DBConn(os.environ['TREE_DB_PASS']) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql)
        return cursor.fetchall()


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
            ) AS images
        FROM trees T
        INNER JOIN species s on T.species_id = s.id
        INNER JOIN images i on s.id = i.species_id
        WHERE
            T.id = %s
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27
    """
    with DBConn(os.environ['TREE_DB_PASS']) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql, tree_id)
        result = cursor.fetchone()

    if result:
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
                ST_GeomFromText(%s, 4269),
                location
            )
    """
    with DBConn(os.environ['TREE_DB_PASS']) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql, polygon_str)
        results = cursor.fetchall()

    if results:
        for tree in results:
            tree['heritage'] = True if tree['heritage'] else False
    return results