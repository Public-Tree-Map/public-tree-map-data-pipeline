import argparse
from pathlib import Path

import geopandas as gpd


class CityParser(object):

    def __init__(self, path: Path):
        geo_jsons = [p for p in path.iterdir() if p.is_file() and p.suffix == '.geojson']
        self.city = path.parts[-1]
        assert len(geo_jsons) <= 1
        if len(geo_jsons) > 0:
            self.geo_json_path = geo_jsons[-1]
        else:
            self.geo_json_path = None

    def get_maximal_df(self):
        assert self.geo_json_path
        df = gpd.read_file(str(self.geo_json_path.absolute())).assign(city=self.city)
        return self.lat_lon_from_geometry(df)

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
    def cat_parser(df, min_field, max_field, og_field, cats):
        actual_cats = [cat for cat in df[og_field].unique().tolist() if set(cat.strip()) != {'-'}]
        if len(actual_cats) > len(cats):
            raise RuntimeError(f'{len(cats)} categories but categories in df={df[og_field].unique().tolist()}')
        df[min_field] = -1
        df[max_field] = -1
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

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(name_common=df['species'].str.title())
        df = self.lat_lon_from_geometry(df)
        return df[['name_common', 'latitude', 'longitude', 'city']]


class LosAngelesCountyParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            name_common=df['SPECIES'].str.title(),
            diameter_min_in=df['DIAMETER']
        )
        return df[['name_common', 'latitude', 'longitude', 'diameter_min_in', 'city']]


class AgouraHillsParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            tree_id=df['InventoryID'],
            name_common=df['species'].str.title(),
            name_botanical=df['botanical'].str.title(),
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        )
        df = self.cat_parser(
            df,
            'diameter_min_in',
            'diameter_max_in',
            'DBH',
            ['0-6', '07-12', '13-18', '19-24', '25-30', '31+']
        )
        df = self.cat_parser(
            df,
            'height_min_feet',
            'height_max_feet',
            'height',
            ['01-15', '15-30', '30-45', '45-60', '60+']
        )

        return df[
            [
                'tree_id',
                'name_common',
                'name_botanical',
                'address',
                'height_min_feet',
                'city',
                'height_max_feet',
                'latitude',
                'longitude',
                'diameter_min_in',
                'diameter_max_in',
            ]
        ]


class AlhambraParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            name_common=df['species'].str.title(),
            name_botanical=df['BotanicalN'].str.title(),
            tree_id=df['Tree'],
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        )
        df = self.cat_parser(
            df,
            'diameter_min_in',
            'diameter_max_in',
            'DBH',
            ['0-6', '07-12', '13-18', '19-24', '25-30', '31+']
        )
        df = self.cat_parser(
            df,
            'height_min_feet',
            'height_max_feet',
            'height',
            ['01-15', '15-30', '30-45', '45-60', '60+']
        )
        return df[
            [
                'name_common',
                'name_botanical',
                'city',
                'tree_id',
                'address',
                'height_min_feet',
                'height_max_feet',
                'latitude',
                'longitude',
                'diameter_min_in',
                'diameter_max_in',

            ]
        ]


class ArcadiaParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            tree_id=df['TREE_ID'],
            name_common=df['COM_NAME'].str.title(),
            address=df['ADDR'].str.split('ARCADIA').str[0].str.title()
        )
        return df[
            [
                'name_common',
                'city',
                'tree_id',
                'address',
                'latitude',
                'longitude',

            ]
        ]


class BellflowerParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            estimated_value=df['EstValue'],
            name_common=df['species'].str.title(),
            name_botanical=df['botanical'].str.title(),
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' '),
            tree_id=df['InventoryID'],
        )
        df = self.cat_parser(
            df,
            'diameter_min_in',
            'diameter_max_in',
            'DBH',
            ['0-6', '07-12', '13-18', '19-24', '25-30', '31+', '---']
        )
        df = self.cat_parser(
            df,
            'height_min_feet',
            'height_max_feet',
            'height',
            ['01-15', '15-30', '30-45', '45-60', '60+', '---']
        )

        return df[
            [
                'name_common',
                'name_botanical',
                'city',
                'tree_id',
                'address',
                'estimated_value',
                'height_min_feet',
                'height_max_feet',
                'latitude',
                'longitude',
                'diameter_min_in',
                'diameter_max_in',
            ]
        ]


class BellGardensParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            name_common=df['species'].str.title(),
            name_botanical=df['BOTANICALN'].str.title(),
            tree_id=df['INVENTORYI'],
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' ')
        )
        df = self.cat_parser(
            df,
            'diameter_min_in',
            'diameter_max_in',
            'DBH',
            ['0-6', '07-12', '13-18', '19-24', '25-30', '31+']
        )
        df = self.cat_parser(
            df,
            'height_min_feet',
            'height_max_feet',
            'height',
            ['01-15', '15-30', '30-45', '45-60', '60+']
        )

        return df[
            [
                'name_common',
                'name_botanical',
                'city',
                'tree_id',
                'address',
                'height_min_feet',
                'height_max_feet',
                'latitude',
                'longitude',
                'diameter_min_in',
                'diameter_max_in',
            ]
        ]


class ArtesiaParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            tree_id=df['INVENTORYI'],
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
            name_botanical=df['BOTANICALN'].str.title(),
            name_common=df['species'].str.title(),
        )
        df = self.cat_parser(
            df,
            'diameter_min_in',
            'diameter_max_in',
            'DBH',
            ['0-6', '07-12', '13-18', '19-24', '25-30', '31+']
        )
        df = self.cat_parser(
            df,
            'height_min_feet',
            'height_max_feet',
            'height',
            ['01-15', '15-30', '30-45', '45-60', '60+']
        )
        return df[
            [
                'name_common',
                'name_botanical',
                'city',
                'tree_id',
                'address',
                'height_min_feet',
                'height_max_feet',
                'latitude',
                'longitude',
                'diameter_min_in',
                'diameter_max_in',

            ]
        ]


class BeverlyHillsParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            tree_id=df['TREEID'],
            address=df['ADDRESS'].astype(str).str.cat(df['STREET'].str.title(), sep=' '),
            name_botanical=df['BOTANICAL'].str.title(),
            name_common=df['species'].str.title(),
        )
        df = self.cat_parser(
            df,
            'height_min_feet',
            'height_max_feet',
            'HEIGHT_RAN',
            ['1-15', '16-30', '31-45', '46-60', '>60', '------', '']
        )
        return df[
            [
                'name_common',
                'name_botanical',
                'city',
                'tree_id',
                'address',
                'height_min_feet',
                'height_max_feet',
                'latitude',
                'longitude',
            ]
        ]


class StilesDataParser(object):

    mapper = {
        'los-angeles-city': LosAngelesCityParser,
        'los-angeles-county': LosAngelesCountyParser,
        'agoura-hills': AgouraHillsParser,
        'alhambra' : AlhambraParser,
        'arcadia': ArcadiaParser,
        'artesia': ArtesiaParser,
        'bell-gardens': BellGardensParser,
        'bellflower': BellflowerParser,
        'beverly-hills': BeverlyHillsParser
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
                        city_parser.get_maximal_df()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datapath", required=True, type=str)
    args = parser.parse_args()

    data_parser = StilesDataParser(args.datapath)
    data_parser.parse_all()
