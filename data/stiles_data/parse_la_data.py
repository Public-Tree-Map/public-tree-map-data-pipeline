import argparse
from pathlib import Path
from typing import List

import geopandas as gpd


class CityParser(object):

    # these are case insensitive
    name_common_columns = ['name_common', 'species', 'com_name']
    name_botanical_columns = ['name_botanical', 'botanical', 'botanicaln']
    address_columns = ['address']
    diameter_min_in_columns = ['diameter_min_in']
    diameter_max_in_columns = ['diameter_max_in']
    diameter_columns = ['diameter']
    height_min_feet_columns = ['height_min_feet']
    height_max_feet_columns = ['height_max_feet']
    tree_id_columns = ['tree_id', 'inventoryid', 'tree', 'inventoryi', 'treeid']
    est_value_columns = ['estimated_value', 'est_value', 'estvalue']

    height_tuples = [
        ('height', 'height_min_feet', 'height_max_feet'),
        ('HEIGHT_RAN', 'height_min_feet', 'height_max_feet'),
    ]
    diameter_tuples = [
        ('diameter', 'diameter_min_in', 'diameter_max_in'),
        ('DBH', 'diameter_min_in', 'diameter_max_in'),
    ]

    def __init__(self, path: Path):
        geo_jsons = [p for p in path.iterdir() if p.is_file() and p.suffix == '.geojson']
        self.city = path.parts[-1]
        assert len(geo_jsons) <= 1
        if len(geo_jsons) > 0:
            self.geo_json_path = geo_jsons[-1]
        else:
            self.geo_json_path = None

    def get_min_max_columns(self, df, range_col_tuples):
        for (range_col, min_col, max_col) in range_col_tuples:
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
            cats = [cat.strip() for cat in df[og_field].unique().tolist() if set(cat.strip()) != {'-'}]
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


class LosAngelesCityParser(CityParser):
    def __init__(self, path: Path):
        super().__init__(path)


class LosAngelesCountyParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)


class AgouraHillsParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

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

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDR'].str.split('ARCADIA').str[0].str.title()
        )
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class BellflowerParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class BellGardensParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' ')
        ).drop('ADDRESS', axis=1)
        df = super().get_maximal_df(df=df)
        return self.filter_columns(df)


class ArtesiaParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

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


# class SantaClarita(CityParser):


class StilesDataParser(object):

    mapper = {
        # 'los-angeles-city': LosAngelesCityParser,
        # 'los-angeles-county': LosAngelesCountyParser,
        # 'agoura-hills': AgouraHillsParser,
        # 'alhambra' : AlhambraParser,
        # 'arcadia': ArcadiaParser,
        # 'artesia': ArtesiaParser,
        # 'bell-gardens': BellGardensParser,
        # 'bellflower': BellflowerParser,
        # 'beverly-hills': BeverlyHillsParser,
        'long-beach': LongBeachParser
    }

    def __init__(self, data_path):
        root_path = Path(data_path)
        self.data_dirs = ([x for x in root_path.iterdir() if x.is_dir()])

    def parse_all(self):
        for data_dir in self.data_dirs:
            city = data_dir.parts[-1]
            if city != 'all':
                if city in self.mapper:
                    city_parser = self.mapper[city](data_dir)
                    if city_parser.geo_json_path:
                        df = city_parser.get_maximal_df()
                        print(city, len(df))
                        print(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datapath", required=True, type=str)
    args = parser.parse_args()

    data_parser = StilesDataParser(args.datapath)
    data_parser.parse_all()
