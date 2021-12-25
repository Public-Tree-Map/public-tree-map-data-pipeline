import os

import pymysql
from google.cloud.sql.connector import connector
from fastapi import FastAPI

app = FastAPI()


class DBConn(object):
    def __init__(self, password):
        self.connection = connector.connect(
            instance_connection_string='total-ensign-336021:us-west1:public-tree-map',
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


@app.get("/trees/")
async def get_tree(lat1, lng1, lat2, lng2, lat3, lng3, lat4, lng4):
    lats = [lat1, lat2, lat3, lat4]
    lngs = [lng1, lng2, lng3, lng4]
    lat_lngs = ' '.join(zip(lats, lngs))
    csv = ','.join(lat_lngs)
    polygon_str = f'POLYGON(({csv}, {lat_lngs[0]}))'
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
            ST_LATITUDE(MY_POINT) AS latitude,
            ST_LONGITUDE(location) AS longitude
        FROM trees
        WHERE
            MBRContains(
                ST_GeomFromText('%s'),
                location
            )
    """
    with DBConn(os.environ['TREE_DB_PASS']) as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql, polygon_str)
        results = cursor.fetchall()

    return results