import os
from typing import Dict
import json
import sys

import pymysql
import geopandas as gpd
import numpy as np
import pandas as pd
import pymysql.cursors
from google.cloud.sql.connector import Connector


class DBCursor(object):
    def __init__(self, password=None):
        self.connection = Connector().connect(
            os.environ['TREE_DB_CONNECTION_STR'],
            'pymysql',
            user='root',
            password=password if password else os.environ['TREE_DB_PASS'],
            db='publictrees'
        )

    def __enter__(self):
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()


class DBTreeUploader(object):

    def truncate_trees(self):
        self._truncate_table('trees')

    def delete_species(self):
        with DBCursor() as conn:
            conn.cursor().execute(
                f"""
                    DELETE FROM species;
                """
            )
            conn.cursor().execute(
                f"""
                    ALTER TABLE species AUTO_INCREMENT = 1;
                """
            )
            conn.commit()

    def _truncate_table(self, table):
        with DBCursor() as conn:
            conn.cursor().execute(
                f"""
                    TRUNCATE TABLE {table};
                """
            )
            conn.cursor().execute(
                f"""
                    ALTER TABLE {table} AUTO_INCREMENT = 1;
                """
            )
            conn.commit()

    def truncate_sm_trees(self):
        with DBCursor() as conn:
            conn.cursor().execute(
                """
                    DELETE FROM trees
                    WHERE city = 'Santa Monica'
                """
            )
            conn.commit()

    def get_species_ids_mapper(self) -> Dict[str, int]:
        with DBCursor() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                """
                    SELECT id, botanical_name
                    FROM species
                """
            )
            results = cursor.fetchall()

        return pd.DataFrame(results).set_index('botanical_name').to_dict()['id']

    def upload_trees(self, df: pd.DataFrame, batch_size=100000):
        with DBCursor() as conn:
            sql = """
                INSERT INTO trees(
                    tree_id,
                    species_id,
                    address,
                    state,
                    city,
                    tree_condition,
                    diameter_min_in,
                    diameter_max_in,
                    exact_diameter,
                    height_min_ft,
                    height_max_ft,
                    exact_height,
                    estimated_value,
                    location,
                    heritage,
                    heritage_year,
                    heritage_number,
                    heritage_text
                ) 
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4269), %s, %s, %s, %s
                )
            """
            if batch_size == 0:
                df['batch'] = 0
            else:
                df['batch'] = np.random.randint(int(len(df) / batch_size), size=len(df))
            df = df.where((pd.notnull(df)), None)
            for _, batch_df in df.groupby('batch'):
                conn.cursor().executemany(
                    sql,
                    [
                        (
                            int(row.tree_id) if row.tree_id is not None and row.tree_id != np.nan else None,
                            row.species_id,
                            row.address,
                            row.state,
                            row.city,
                            row.tree_condition if hasattr(row, 'tree_condition') else None,
                            row.diameter_min_in,
                            row.diameter_max_in,
                            row.exact_diameter if hasattr(row, 'exact_diameter') else None,
                            row.height_min_ft,
                            row.height_max_ft,
                            row.exact_height if hasattr(row, 'exact_height') else None,
                            row.estimated_value if hasattr(row, 'estimated_value') else None,
                            row.location,
                            row.heritage if hasattr(row, 'heritage') else False,
                            row.heritage_year if hasattr(row, 'heritage_year') else None,
                            row.heritage_number if hasattr(row, 'heritage_number') else None,
                            row.heritage_text if hasattr(row, 'heritage_text') else None
                        ) for row in batch_df.itertuples()
                    ]
                )
            conn.commit()

    def update_species(self, df):
        with DBCursor() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                """
                    SELECT botanical_name FROM species
                """
            )
            botanical_names = set([row['botanical_name'] for row in cursor.fetchall()])
            update_df = df[df['botanical_name'].isin(botanical_names)]
            cursor.executemany(
                """
                    UPDATE species
                    SET 
                        common_name = %s,
                        family_botanical_name = %s,
                        family_common_name = %s,
                        native = %s,
                        eol_id = %s,
                        eol_overview_url = %s,
                        simplified_iucn_status = %s,
                        iucn_status = %s,
                        iucn_doi_or_url = %s,
                        shade_production = %s,
                        form = %s,
                        type = %s,
                        cal_ipc_url = %s,
                        irrigation_requirements = %s,
                        species_id = %s
                    WHERE 
                        botanical_name = %s
                """,
                [
                    (
                        row.common_name,
                        row.family_botanical_name,
                        row.family_common_name,
                        row.native,
                        int(row.eol_id) if row.eol_id is not None else None,
                        row.eol_overview_url,
                        row.simplified_iucn_status,
                        row.iucn_status,
                        row.iucn_doi_or_url,
                        row.shade_production,
                        row.form,
                        row.type,
                        row.cal_ipc_url,
                        row.irrigation_requirements,
                        row.species_id,
                        row.botanical_name,
                    ) for row in update_df.itertuples()
                ]

            )

        write_df = df[~df['botanical_name'].isin(botanical_names)]
        self.upload_species(write_df)

    @staticmethod
    def upload_species(df: pd.DataFrame):
        with DBCursor() as conn:
            sql = """
                    INSERT INTO species(
                        botanical_name,
                        common_name,
                        family_botanical_name,
                        family_common_name,
                        native,
                        eol_id,
                        eol_overview_url,
                        simplified_iucn_status,
                        iucn_status,
                        iucn_doi_or_url,
                        shade_production,
                        form,
                        type,
                        cal_ipc_url,
                        irrigation_requirements,
                        species_id
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
            df = df.where((pd.notnull(df)), None)
            conn.cursor().executemany(
                sql,
                [
                    (
                        row.botanical_name,
                        row.common_name,
                        row.family_botanical_name,
                        row.family_common_name,
                        row.native,
                        int(row.eol_id) if row.eol_id is not None else None,
                        row.eol_overview_url,
                        row.simplified_iucn_status,
                        row.iucn_status,
                        row.iucn_doi_or_url,
                        row.shade_production,
                        row.form,
                        row.type,
                        row.cal_ipc_url,
                        row.irrigation_requirements,
                        row.species_id
                    ) for row in df.itertuples()
                ]
            )

            conn.commit()


class SMTreeUploader(DBTreeUploader):

    def __init__(self):
        super().__init__()

    def prepare_df(self, df):
        df['location'] = gpd.GeoSeries(gpd.points_from_xy(df['latitude'], df['longitude'])).to_wkt()
        self.df = df.rename(columns={
            'heritageYear': 'heritage_year',
            'heritageNumber': 'heritage_number',
            'heritageText': 'heritage_text',
        })