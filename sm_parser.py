import sys
from io import StringIO

import pandas as pd


def parse_trees(df=None, stdout=False):
    heritage_trees = pd.read_csv('data/heritage_trees.csv')
    if df is None:
        df = pd.read_csv(StringIO(''.join(sys.stdin.readlines()))).rename(columns={'Tree ID': 'tree_id'})
    else:
        df = df.rename(columns={'Tree ID': 'tree_id'})
    df = pd.merge(df, heritage_trees, how='left', on='tree_id').rename(
        columns={
            'Species ID': 'species_id',
            'Name Botanical': 'name_botanical',
            'Height Min': 'height_min_ft',
            'Height Max': 'height_max_ft',
            'DBH Min': 'diameter_min_in',
            'DBH Max': 'diameter_max_in',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Location Description': 'location_description',
            'year_added': 'heritageYear',
            'heritage_number': 'heritageNumber',
            'text': 'heritageText'
        }
    )
    df = df.assign(
        address=df['Address'].astype(str).str.cat(df['Street'], sep=' '),
        city='Santa Monica',
        state='CA',
        heritage=df['heritageNumber'].notnull()
    )
    if stdout:
        print(df.to_json(orient='records'), file=sys.stdout)
    else:
        return df


if __name__ == "__main__":
    parse_trees(True)