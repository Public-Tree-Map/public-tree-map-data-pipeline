import argparse
import getpass
import json
from pathlib import Path
from typing import List, Set

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from upload_trees import DBTreeUploader


class CityParser(object):

    # these are case insensitive
    name_common_columns = ['name_common', 'species', 'com_name', 'trees_spec', 'commonname', 'common_name']
    name_botanical_columns = ['name_botanical', 'botanical', 'botanicaln', 'botanicalna', 'trees_bota', 'botanical_', 'botname', 'botanical_name']
    condition = ['condition', 'treecondition', 'treeconditi']
    address_columns = ['address']
    diameter_min_in_columns = ['diameter_min_in']
    diameter_max_in_columns = ['diameter_max_in']
    exact_diameter_columns = ['exact_diameter', 'diameter', 'exact_dbh', 'trunk_diam', 'actualdbh', 'exactdbh']
    height_min_feet_columns = ['height_min_feet']
    height_max_feet_columns = ['height_max_feet']
    exact_height_columns = ['exact_height', 'exact_heigh', 'height', 'actualheight', 'exact_heig']
    tree_id_columns = ['tree_id', 'inventoryid', 'tree', 'inventoryi', 'treeid', 'objectid', 'trees_ogc_']
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
        csvs = []
        if path:
            geo_jsons = [p for p in path.iterdir() if p.is_file() and p.suffix == '.geojson']
            csvs = [p for p in path.iterdir() if p.is_file() and p.suffix == '.csv']
            assert len(geo_jsons) <= 1
            assert len(csvs) <= 1
        if len(csvs) > 0:
            self.csv_path = csvs[-1]
        else:
            self.csv_path = None
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
            for col in [range_col, range_col.upper(), range_col.lower()]:
                if col in df.columns:
                    try:
                        return self.cat_parser(df, min_col, max_col, col), col
                    except AttributeError:
                        pass
        return df, None

    def get_column(self, df, potential_columns: List[str], exclude_col: str = None, titleize=False):
        column_name = potential_columns[0]
        df_columns = [s.strip().lower() for s in df.columns]
        for potential_column in potential_columns:
            if potential_column in df_columns:
                if exclude_col is not None and exclude_col.lower() == potential_column.lower():
                    continue
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
            'geometry',
            'city',
            'diameter_min_in',
            'diameter_max_in',
            'height_min_feet',
            'height_max_feet',
            'latitude',
            'longitude',
        }
        actual_columns = potential_columns & set(df.columns)
        return df[list(actual_columns)].rename(
            columns={
                'height_min_feet': 'height_min_ft',
                'height_max_feet': 'height_max_ft',
            }
        )

    def read_df(self):
        assert self.geo_json_path or self.csv_path
        if self.csv_path:
            df = pd.read_csv(self.csv_path.absolute()).assign(city=self.city)
            df = gpd.GeoDataFrame(df)
        else:
            df = gpd.read_file(str(self.geo_json_path.absolute())).assign(city=self.city)

        if 'geometry' not in df.columns or df['geometry'].isnull().all():
            lon_cols = ['lon', 'longitude', 'LONGITUDE', 'X']
            lat_cols = ['lat', 'latitude', 'LATITUDE', 'Y']

            lon_col = next((c for c in lon_cols if c in df.columns), None)
            lat_col = next((c for c in lat_cols if c in df.columns), None)

            if lon_col and lat_col:
                # convert to numeric, coercing errors
                df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
                df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
                # drop rows where conversion failed
                df.dropna(subset=[lon_col, lat_col], inplace=True)

                df = df.set_geometry(gpd.points_from_xy(df[lon_col], df[lat_col]))

        return df

    def cleanup_columns(self, df):
        str_cols = [
            'name_common',
            'name_botanical',
            'condition',
            'tree_id',
            'address',
        ]
        for col in str_cols:
            df[col] = df[col].str.strip()

    def get_maximal_df(self, df=None):
        if df is None:
            df = self.read_df()

        df = self.get_column(df, self.address_columns, titleize=True)
        df = self.get_column(df, self.name_common_columns, titleize=True)
        df = self.get_column(df, self.name_botanical_columns, titleize=True)
        df = self.get_column(df, self.tree_id_columns)
        df = self.get_column(df, self.condition)
        df = self.get_column(df, self.est_value_columns)

        df, height_col = self.get_min_max_columns(df, self.height_tuples)
        df, diameter_col = self.get_min_max_columns(df, self.diameter_tuples)

        df = self.get_column(df, self.exact_height_columns, exclude_col=height_col)
        df = self.get_column(df, self.exact_diameter_columns, exclude_col=diameter_col)

        df = self.get_column(df, self.diameter_min_in_columns)
        df = self.get_column(df, self.diameter_max_in_columns)
        df = self.get_column(df, self.height_max_feet_columns)
        df = self.get_column(df, self.height_min_feet_columns)

        if 'geometry' in df.columns and not df.geometry.empty:
            # Ensure CRS is set to WGS84 (EPSG:4326) for lat/lon
            if df.crs is None:
                df.set_crs(epsg=4326, inplace=True)
            else:
                df.to_crs(epsg=4326, inplace=True)
            df['longitude'] = df.geometry.x
            df['latitude'] = df.geometry.y

        return self.filter_columns(df).drop_duplicates()

    @staticmethod
    def cat_parser(df, min_field, max_field, og_field, cats=None):
        if cats is None:
            cats = [cat.strip() for cat in df[og_field].unique().tolist() if cat is not None and set(cat.strip()) != {'-'}]
        df[min_field] = None
        df[max_field] = None
        for cat in cats:
            mask = df[og_field].str.strip() == cat
            
            # Use regex to extract numbers, ignoring non-numeric characters
            import re
            numbers = re.findall(r'\d+', cat)
            
            if len(numbers) == 2:
                min_val, max_val = numbers
                df.loc[mask, min_field] = int(min_val)
                df.loc[mask, max_field] = int(max_val)
            elif len(numbers) == 1:
                min_val = numbers[0]
                if '+' in cat or '>' in cat:
                    df.loc[mask, min_field] = int(min_val)

        return df


class AgouraHillsParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class AlhambraParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class ArcadiaParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDR'].str.split('ARCADIA').str[0].str.title()
        )
        return super().get_maximal_df(df=df)


class BellflowerParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class BellGardensParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' ')
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class ArtesiaParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class BeverlyHillsParser(CityParser):
    def get_maximal_df(self):
        df = self.read_df()
        df = df.rename(columns={'height': 'exact_height'})
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class BurbankParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.rename(columns={'SPP': 'botanical'})
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class CarsonParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class CovinaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class CulverCityParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class DiamondBarParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class DuarteParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class ElMonteParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class ElSegundoParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class GlendoraParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class LaMiradaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class LaVerneParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class LomitaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class LongBeachParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df().drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class SantaClaritaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df[df['PROP_ADR'].notnull()]
        df = df.assign(
            address=df['PROP_ADR'].astype(str).str.cat(df['PROPSTREET'].str.title(), sep=' '),
        )
        return super().get_maximal_df(df=df)


class SantaClaritaParksParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


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

        return super().get_maximal_df(df=df)


class GlendaleParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.drop('Address', axis=1)
        df['address'] = df['OnAddress'].astype(str).str.cat(df['OnStreet'].astype(str).str.strip(), sep=' ')
        return super().get_maximal_df(df=df)


class PomonaParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['address'] = df['ADDRESS'].astype(str).str.cat(df['STREET'].astype(str).str.strip(), sep=' ')
        df = df.drop('ADDRESS', axis=1)

        return super().get_maximal_df(df=df)


class AddressStreetParser(CityParser):
    """Shared parser for cities with title-case Address (int) + Street columns."""
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class DowneyParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.rename(columns={'SPP': 'botanical'})
        return super().get_maximal_df(df=df)


class LancasterParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.rename(columns={
            'btncl_n': 'botanical',
            'cmmn_nm': 'species',
            'exct_db': 'exact_diameter',
        })
        return super().get_maximal_df(df=df)


class LawndaleParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df[df['PROP_ADR'].notnull()]
        df = df.rename(columns={'BOTANICAL_': 'botanical'}).drop(columns=['BOTANICAL'], errors='ignore')
        df = df.assign(
            address=df['PROP_ADR'].astype(int).astype(str).str.cat(
                df['PROP_STREE'].str.title(), sep=' '
            ),
        )
        return super().get_maximal_df(df=df)


class NorwalkParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class RanchoPalosVerdesParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.assign(
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
        ).drop('ADDRESS', axis=1)
        return super().get_maximal_df(df=df)


class RedondoBeachParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class SanMarinoParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df = df.rename(columns={'BOTANI8D': 'botanical'})
        df['PROP_ADR'] = df['PROP_ADR'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['PROP_ADR'].astype(str).str.cat(df['PROPST18'].str.title(), sep=' '),
        )
        return super().get_maximal_df(df=df)


class WhittierParser(CityParser):
    def get_maximal_df(self, df=None):
        df = self.read_df()
        df['Address'] = df['Address'].astype(pd.Int64Dtype())
        df = df.assign(
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
        ).drop('Address', axis=1)
        return super().get_maximal_df(df=df)


class StilesDataParser(object):

    mapper = {
        'los-angeles-city': CityParser,
        'los-angeles-county': CityParser,
        'agoura-hills': AgouraHillsParser,
        'alhambra': AlhambraParser,
        'arcadia': ArcadiaParser,
        'artesia': ArtesiaParser,
        'bell-gardens': BellGardensParser,
        'bellflower': BellflowerParser,
        'beverly-hills': BeverlyHillsParser,
        'burbank': BurbankParser,
        'carson': CarsonParser,
        'cerritos': CityParser,
        'covina': CovinaParser,
        'culver-city': CulverCityParser,
        'diamond-bar': DiamondBarParser,
        'downey': DowneyParser,
        'duarte': DuarteParser,
        'el-monte': ElMonteParser,
        'el-segundo': ElSegundoParser,
        'glendale': GlendaleParser,
        'glendora': GlendoraParser,
        'inglewood': CityParser,
        'la-mirada': LaMiradaParser,
        'la-verne': LaVerneParser,
        'lancaster': LancasterParser,
        'lawndale': LawndaleParser,
        'lomita': LomitaParser,
        'long-beach': LongBeachParser,
        'malibu': CityParser,
        'norwalk': NorwalkParser,
        'palmdale': CityParser,
        'paramount': AddressStreetParser,
        'pasadena': PasadenaParser,
        'pomona': PomonaParser,
        'rancho-palos-verdes': RanchoPalosVerdesParser,
        'redondo-beach': RedondoBeachParser,
        'san-dimas': AddressStreetParser,
        'san-fernando': AddressStreetParser,
        'san-gabriel': AddressStreetParser,
        'san-marino': SanMarinoParser,
        'santa-clarita': SantaClaritaParser,
        'santa-clarita-parks': SantaClaritaParksParser,
        'santa-fe-springs': AddressStreetParser,
        'simi-valley': CityParser,
        'south-gate': AddressStreetParser,
        'south-pasadena': AddressStreetParser,
        'temple-city': AddressStreetParser,
        'walnut': AddressStreetParser,
        'west-hollywood': CityParser,
        'whittier': WhittierParser,
    }

    def __init__(self, data_path):
        root_path = Path(data_path)
        self.data_dirs = {x.name: x for x in root_path.iterdir() if x.is_dir()}
        for county_dir in ['ventura-county']:
            county_path = root_path / county_dir
            if county_path.exists():
                for x in county_path.iterdir():
                    if x.is_dir():
                        self.data_dirs[x.name] = x
        all_path = Path(f'{data_path}/all')
        self.geojsons = {geojson_path.name.split('.')[0]: geojson_path for geojson_path in all_path.glob('*.geojson')}

    def parse_all(self):
        dfs = []
        for city in self.mapper:
            if city in self.mapper:
                city_parser = self.mapper[city](
                    city,
                    self.data_dirs[city] if city in self.data_dirs else None,
                    self.geojsons[city] if city in self.geojsons else None
                )
                if city_parser.geo_json_path:
                    df = city_parser.get_maximal_df()
                    dfs.append(df)
            else:
                assert False

        df = pd.concat(dfs)
        str_cols = [
            'name_common',
            'name_botanical',
            'address',
            'city',
            'condition',
        ]
        for col in str_cols:
            mask = df[col].notnull()
            df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()

        return df


class SpeciesMatcher(object):
    def __init__(self, df):
        self.species_df = pd.read_csv('data/species_attributes.csv')
        # TODO (Remove this after Emily renames)
        self.species_df = self.species_df.drop_duplicates('botanical_name')
        self.synonym_df = SpeciesMatcher.generate_synonyms(
            self.species_df.copy(), 'botanical_name', ['sm_botanical_name'], ['botanical_synonyms']
        )
        self.df = df

    @staticmethod
    def generate_synonyms(df, base_column, regular_columns, json_columns):
        synonyms = []
        for row in df.itertuples():
            row_synonyms = set()
            base_name = getattr(row, base_column)
            row_synonyms.add(base_name.lower())
            for column in regular_columns:
                if not isinstance(getattr(row, column), float) and getattr(row, column):
                    row_synonyms.add(getattr(row, column).lower())
            for column in json_columns:
                json_value = getattr(row, column)
                if not isinstance(json_value, float):
                    try:
                        row_synonyms |= set([s.lower() for s in json.loads(json_value)])
                    except json.JSONDecodeError:
                        row_synonyms.add(json_value.lower())
            synonyms.append(list(row_synonyms))

        df['synonym'] = synonyms
        return df.explode('synonym')

    def match(self, how='inner'):
        df = self.df.assign(synonym=self.df['name_botanical'].str.lower())
        return pd.merge(
            df,
            self.synonym_df[['synonym', 'botanical_name']],
            how=how,
            on='synonym'
        ).drop(['name_botanical', 'synonym'], axis=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datapath", required=True, type=str)
    parser.add_argument("--host", required=False, type=str, default=None)
    args = parser.parse_args()

    data_parser = StilesDataParser(args.datapath)
    df = data_parser.parse_all()

    # Drop rows with coordinates outside LA area bounding box
    geom = gpd.GeoSeries(df['geometry'])
    df = df[(geom.y >= 32) & (geom.y <= 36) & (geom.x >= -119) & (geom.x <= -117)]

    df['location'] = gpd.GeoSeries(df['geometry']).apply(lambda x: Point(x.y, x.x)).to_wkt()
    df.to_csv('stiles.trees.csv', index=False)
    df = pd.read_csv('stiles.trees.csv')
    matcher = SpeciesMatcher(df)
    matched_df = matcher.match()
    uploader = DBTreeUploader()
    uploader.delete_non_sm_trees()
    uploader.update_species(
        matcher.species_df.rename(columns={'Species ID': 'species_id'}).rename(
            columns={col: col.lower() for col in matcher.species_df.columns}
        )
    )
    species_mapper = uploader.get_species_ids_mapper()
    matched_df['species_id'] = matched_df['botanical_name'].map(species_mapper)
    assert matched_df['species_id'].notnull().all()
    uploader.upload_trees(
        matched_df.assign(state='CA').rename(columns={'Species ID': 'species_id'}).rename(
            columns={col: col.lower() for col in matched_df.columns}
        )
    )
