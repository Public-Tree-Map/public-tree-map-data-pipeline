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


class LosAngelesCityParser(CityParser):
    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(name_common=df['species'].str.title())
        df = self.lat_lon_from_geometry(df)
        return df[['name_common', 'latitude', 'longitude']]


class LosAngelesCountyParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            name_common=df['SPECIES'].str.title(),
            diameter_min_in=df['DIAMETER']
        )
        return df[['name_common', 'latitude', 'longitude', 'diameter_min_in']]


class AgouraHillsParser(CityParser):

    def __init__(self, path: Path):
        super().__init__(path)

    def get_maximal_df(self):
        df = super().get_maximal_df()
        df = df.assign(
            name_common=df['species'].str.title(),
            name_botanical=df['botanical'].str.title(),
            diameter_min_in=-1,
            diameter_max_in=-1,
            diameter=df['DBH'].str.strip(),
            height=df['height'].str.strip(),
            address=df['Address'].astype(str).str.cat(df['Street'].str.title(), sep=' ')
        )
        diameter_mask = df['DBH'] == '0-6'
        df.loc[diameter_mask, 'diameter_min_in'] = 0
        df.loc[diameter_mask, 'diameter_max_in'] = 6
        diameter_mask = df['DBH'] == '07-12'
        df.loc[diameter_mask, 'diameter_min_in'] = 7
        df.loc[diameter_mask, 'diameter_max_in'] = 12
        diameter_mask = df['DBH'] == '13-18'
        df.loc[diameter_mask, 'diameter_min_in'] = 13
        df.loc[diameter_mask, 'diameter_max_in'] = 18
        diameter_mask = df['DBH'] == '19-24'
        df.loc[diameter_mask, 'diameter_min_in'] = 19
        df.loc[diameter_mask, 'diameter_max_in'] = 24
        diameter_mask = df['DBH'] == '25-30'
        df.loc[diameter_mask, 'diameter_min_in'] = 25
        df.loc[diameter_mask, 'diameter_max_in'] = 30
        diameter_mask = df['DBH'] == '31+'
        df.loc[diameter_mask, 'diameter_min_in'] = 31

        height_mask = df['height'] == '01-15'
        df.loc[height_mask, 'height_min_feet'] = 1
        df.loc[height_mask, 'height_max_feet'] = 15
        height_mask = df['height'] == '15-30'
        df.loc[height_mask, 'height_min_feet'] = 15
        df.loc[height_mask, 'height_max_feet'] = 30
        height_mask = df['height'] == '30-45'
        df.loc[height_mask, 'height_min_feet'] = 30
        df.loc[height_mask, 'height_max_feet'] = 45
        height_mask = df['height'] == '45-60'
        df.loc[height_mask, 'height_min_feet'] = 45
        df.loc[height_mask, 'height_max_feet'] = 60
        height_mask = df['height'] == '60+'
        df.loc[height_mask, 'height_min_feet'] = 60

        return df[
            [
                'name_common',
                'latitude',
                'longitude',
                'diameter_min_in',
                'diameter_max_in',
                'name_botanical',
                'address',
                'height_min_feet',
                'height_max_feet'
            ]
        ]

class StilesDataParser(object):

    mapper = {
        # 'los-angeles-city': LosAngelesCityParser,
        # 'los-angeles-county': LosAngelesCountyParser,
        'agoura-hills': AgouraHillsParser
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
