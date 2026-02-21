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

    def delete_non_sm_trees(self):
        with DBCursor() as conn:
            conn.cursor().execute(
                """
                    DELETE FROM trees
                    WHERE city != 'Santa Monica'
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

    def upload_trees(self, df: pd.DataFrame, batch_size=5000):
        s = self._sanitize
        i = self._to_int
        value_template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4269), %s, %s, %s, %s)"
        insert_prefix = """INSERT INTO trees(
                    tree_id, species_id, address, state, city, tree_condition,
                    diameter_min_in, diameter_max_in, exact_diameter,
                    height_min_ft, height_max_ft, exact_height,
                    estimated_value, location, heritage,
                    heritage_year, heritage_number, heritage_text
                ) VALUES """
        with DBCursor() as conn:
            cursor = conn.cursor()
            total = len(df)
            uploaded = 0
            for start in range(0, total, batch_size):
                chunk = df.iloc[start:start + batch_size]
                values_parts = []
                params = []
                for row in chunk.itertuples():
                    values_parts.append(value_template)
                    params.extend([
                        i(row.tree_id),
                        i(row.species_id),
                        s(row.address),
                        s(row.state),
                        s(row.city),
                        s(row.tree_condition) if hasattr(row, 'tree_condition') else None,
                        i(row.diameter_min_in),
                        i(row.diameter_max_in),
                        i(row.exact_diameter) if hasattr(row, 'exact_diameter') else None,
                        i(row.height_min_ft),
                        i(row.height_max_ft),
                        i(row.exact_height) if hasattr(row, 'exact_height') else None,
                        i(row.estimated_value) if hasattr(row, 'estimated_value') else None,
                        row.location,
                        s(row.heritage) if hasattr(row, 'heritage') else False,
                        i(row.heritage_year) if hasattr(row, 'heritage_year') else None,
                        i(row.heritage_number) if hasattr(row, 'heritage_number') else None,
                        s(row.heritage_text) if hasattr(row, 'heritage_text') else None,
                    ])
                sql = insert_prefix + ", ".join(values_parts)
                cursor.execute(sql, params)
                conn.commit()
                uploaded += len(chunk)
                print(f'  Uploaded {uploaded}/{total} rows', flush=True)

    @staticmethod
    def _sanitize(val):
        """Convert NaN/NaT to None for MySQL compatibility."""
        if isinstance(val, float) and np.isnan(val):
            return None
        return val

    @staticmethod
    def _to_int(val):
        """Safely convert to int, returning None for NaN or unparseable values."""
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

    def update_species(self, df):
        s = self._sanitize
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
                        s(row.common_name),
                        s(row.family_botanical_name),
                        s(row.family_common_name),
                        s(row.native),
                        int(row.eol_id) if pd.notna(row.eol_id) else None,
                        s(row.eol_overview_url),
                        s(row.simplified_iucn_status),
                        s(row.iucn_status),
                        s(row.iucn_doi_or_url),
                        s(row.shade_production),
                        s(row.form),
                        s(row.type),
                        s(row.cal_ipc_url),
                        s(row.irrigation_requirements),
                        s(row.species_id),
                        row.botanical_name,
                    ) for row in update_df.itertuples()
                ]

            )

        write_df = df[~df['botanical_name'].isin(botanical_names)]
        self.upload_species(write_df)

    @staticmethod
    def upload_species(df: pd.DataFrame):
        s = DBTreeUploader._sanitize
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
            conn.cursor().executemany(
                sql,
                [
                    (
                        row.botanical_name,
                        s(row.common_name),
                        s(row.family_botanical_name),
                        s(row.family_common_name),
                        s(row.native),
                        int(row.eol_id) if pd.notna(row.eol_id) else None,
                        s(row.eol_overview_url),
                        s(row.simplified_iucn_status),
                        s(row.iucn_status),
                        s(row.iucn_doi_or_url),
                        s(row.shade_production),
                        s(row.form),
                        s(row.type),
                        s(row.cal_ipc_url),
                        s(row.irrigation_requirements),
                        s(row.species_id)
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