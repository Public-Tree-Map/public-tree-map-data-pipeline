import argparse
from pathlib import Path
from typing import List, Set

import pandas as pd
import geopandas as gpd


class CityParser(object):

    # these are case insensitive
    name_common_columns = ['name_common', 'species', 'com_name']
    name_botanical_columns = ['name_botanical', 'botanical', 'botanicaln']
    condition = ['condition', 'treecondition']
    address_columns = ['address']
    diameter_min_in_columns = ['diameter_min_in']
    diameter_max_in_columns = ['diameter_max_in']
    exact_diameter_columns = ['exact_diameter', 'diameter', 'exact_dbh', 'trunk_diam', 'actualdbh']
    height_min_feet_columns = ['height_min_feet']
    height_max_feet_columns = ['height_max_feet']
    exact_height_columns = ['exact_height', 'exact_heigh', 'height', 'actualheight']
    tree_id_columns = ['tree_id', 'inventoryid', 'tree', 'inventoryi', 'treeid', 'objectid']
    est_value_columns = ['estimated_value', 'est_value', 'estvalue']

    height_tuples = [
        ('height', 'height_min_feet', 'height_max_feet'),
        ('HEIGHT_RAN', 'height_min_feet', 'height_max_feet'),
    ]
    diameter_tuples = [
        ('diameter', 'diameter_min_in', 'diameter_max_in'),
        ('DBH', 'diameter_min_in', 'diameter_max_in'),
    ]

    def __init__(self, city, path: Path, geojson_path: Path=None):
        self.city = city
        geo_jsons = []
        if path:
            geo_jsons = [p for p in path.iterdir() if p.is_file() and p.suffix == '.geojson']
            assert len(geo_jsons) <= 1
        if len(geo_jsons) > 0:
            self.geo_json_path = geo_jsons[-1]
        elif geojson_path:
            self.geo_json_path = geojson_path
        else:
            self.geo_json_path = None

    def get_min_max_columns(self, df, range_col_tuples, skip_col: Set[str] = None):
        for (range_col, min_col, max_col) in range_col_tuples:
            if skip_col and range_col in skip_col:
                continue
            if range_col in df.columns:
                return self.cat_parser(df, min_col, max_col, range_col)
        return df

    def get_column(self, df, potential_columns: List[str], titleize=False):
        column_name = potential_columns[0]
        df_columns = [s.strip().lower() for s in df.columns]
        for potential_column in potential_columns:
            if potential_column in df_columns:
                idx = df_columns.index(potential_column)
                column = df.columns[idx]
                if titleize:
                    df[column_name] = df[column].str.title()
                else:
                    df[column_name] = df[column]
                return df
        return df

    def filter_columns(self, df):
        potential_columns = {
            'name_common',
            'name_botanical',
            'condition',
            'exact_diameter',
            'exact_height',
            'tree_id',
            'estimated_value',
            'address',
            'latitude',
            'longitude',
            'city',
            'diameter_min_in',
            'diameter_max_in',
            'height_min_feet',
            'height_max_feet',
        }
        actual_columns = potential_columns & set(df.columns)
        return df[list(actual_columns)]

    def read_df(self):
        assert self.geo_json_path
        return gpd.read_file(str(self.geo_json_path.absolute())).assign(city=self.city)

    def get_maximal_df(self, df=None):
        if df is None:
            df = self.read_df()
        df = self.lat_lon_from_geometry(df)
        df = self.get_column(df, self.address_columns, titleize=True)
        df = self.get_column(df, self.name_common_columns, titleize=True)
        df = self.get_column(df, self.name_botanical_columns, titleize=True)

        df = self.get_min_max_columns(df, self.height_tuples)
        df = self.get_min_max_columns(df, self.diameter_tuples)

        df = self.get_column(df, self.diameter_min_in_columns)
        df = self.get_column(df, self.diameter_max_in_columns)

        return self.filter_columns(df).drop_duplicates()

    @staticmethod
    def lat_lon_from_geometry(df, y_is_lat=True):
        if y_is_lat:
            return df.assign(
                latitude=df['geometry'].apply(lambda p: p.y),
                longitude=df['geometry'].apply(lambda p: p.x)
            )
        return df.assign(
            latitude=df['geometry'].apply(lambda p: p.x),
            longitude=df['geometry'].apply(lambda p: p.y)
        )

    @staticmethod
    def cat_parser(df, min_field, max_field, og_field, cats=None):
        if cats is None:
            cats = [cat.strip() for cat in df[og_field].unique().tolist() if cat is not None and set(cat.strip()) != {'-'}]
        df[min_field] = None
        df[max_field] = None
        for cat in cats:
            mask = df[og_field].str.strip() == cat
            if len(cat.split('-')) == 2:
                min_val, max_val = cat.split('-')
                df.loc[mask, min_field] = int(min_val)
                df.loc[mask, max_field] = int(max_val)
            elif cat.endswith('+'):
                min_val = int(cat[:-1])
                df.loc[mask, min_field] = int(min_val)
            elif cat.startswith('>'):
                min_val = int(cat[1:])
                df.loc[mask, min_field] = int(min_val)

        return df


class AgouraHillsParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        ).drop('Address', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class AlhambraParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        ).drop('Address', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class ArcadiaParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDR'].str.split('ARCADIA').str[0].str.title()
        )
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class BellflowerParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class BellGardensParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' ')
        ).drop('ADDRESS', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class ArtesiaParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class BeverlyHillsParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.rename(columns={'height': 'exact_height'})
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class LongBeachParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df().drop('ADDRESS', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class SantaClaritaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df[df['PROP_ADR'].notnull()]
        df = df.assign(
            address=df['PROP_ADR'].astype(str).str.cat(df['PROPSTREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class PasadenaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Botanical'] = df['Genus'].str.cat(df['Species'], sep=' ').str.title()
        df = df.drop('Species', axis=1)

        df['House_Numb'] = df['House_Numb'].astype(pd.Int64Dtype())
        mask = df['Street_Dir'].isnull()
        df['Street'] = df['Street_Nam'].astype(str).str.cat(df['Street_Typ'], sep=' ')
        df['Address'] = df['House_Numb'].astype(str).str.cat(df['Street'], sep=' ')
        df.loc[mask, 'Address'] = df.loc[mask, 'House_Numb'].astype(str).str.cat(
            df.loc[mask, 'Street_Nam'], sep=' '
        ).str.cat(df.loc[mask, 'Street_Typ'], sep=' ')

        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class GlendaleParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.drop('Address', axis=1)
        df['address'] = df['OnAddress'].astype(str).str.cat(df['OnStreet'].astype(str).str.strip(), sep=' ')
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class PomonaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['address'] = df['ADDRESS'].astype(str).str.cat(df['STREET'].astype(str).str.strip(), sep=' ')
        df = df.drop('ADDRESS', axis=1)

        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class StilesDataParser(object):

    mapper = {
        # 'los-angeles-city': CityParser,
        # 'los-angeles-county': CityParser,
        # 'agoura-hills': AgouraHillsParser,
        # 'alhambra' : AlhambraParser,
        # 'arcadia': ArcadiaParser,
        # 'artesia': ArtesiaParser,
        # 'bell-gardens': BellGardensParser,
        # 'bellflower': BellflowerParser,
        # 'beverly-hills': BeverlyHillsParser,
        # 'long-beach': LongBeachParser,
        # 'santa-clarita': SantaClaritaParser,
        # 'pasadena': PasadenaParser,
        # 'glendale': GlendaleParser,
        'pomona': PomonaParser,
    }

    def __init__(self, data_path):
        root_path = Path(data_path)
        self.data_dirs = {x.name: x for x in root_path.iterdir() if x.is_dir()}
        all_path = Path(f'{data_path}/all')
        self.geojsons = {geojson_path.name.split('.')[0]: geojson_path for geojson_path in all_path.glob('*.geojson')}

    def parse_all(self):
        for city in self.mapper:
            if city in self.mapper:
                city_parser = self.mapper[city](
                    city,
                    self.data_dirs[city] if city in self.data_dirs else None,
                    self.geojsons[city] if city in self.geojsons else None
                )
                if city_parser.geo_json_path:
                    df = city_parser.get_maximal_df()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datapath", required=True, type=str)
    args = parser.parse_args()

    data_parser = StilesDataParser(args.datapath)
    data_parser.parse_all()
