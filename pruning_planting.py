"""
Data processing for tree data.
"""

import geohash
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString


PRECISION = 9


def load_dataset(name, line_to_points=False):
    """
    Given a file path, load the data into a geodataframe,
    reproject it into WGS84, and return the geodataframe.
    """
    # Load the street planting shape data, reprojecting into WGS84
    gdf = gpd.read_file(name, crs='2229')
    gdf = gdf.to_crs(4326)
    if line_to_points:
        dfs = []
        for row in gdf.itertuples():
            if isinstance(row.geometry, LineString):
                points = list(row.geometry.coords)
            elif isinstance(row.geometry, MultiLineString):
                points = []
                for line in row.geometry.geoms:
                    points += list(line.coords)
            else:
                raise RuntimeError('Geometry is not a Line nor a MultiLine')
            dfs.append(pd.DataFrame({'point': points}).assign(SEGMENT=row.SEGMENT))
        exploded_df = pd.concat(dfs, sort=False)
        return pd.merge(gdf, exploded_df, on='SEGMENT')
    return gdf


def geohash_series(series, precision=9):
    hashes = []
    for point in series:
        hashes.append(geohash.encode(*point[::-1], precision=precision))
    return hashes


def planting_for_trees(trees: pd.DataFrame):
    """
    Match a replacement species and planting year for
    all the trees in a dataframe.

    The input is a dataframe with a record for each tree.
    The columns of the dataframe are the same as the JSON properties
    described in the "parse-trees.js" script.

    This returns a new dataframe which is the same as the old one,
    but includes columns for street segment, planting year, and
    replacement species.
    """
    # Load the street planting shape data, reprojecting into WGS84
    planting_street_segments = load_dataset("data/planting/TreePlanting_Streets.shp", True)
    planting_street_segments = planting_street_segments.assign(
        geohash=geohash_series(planting_street_segments['point'], precision=PRECISION)
    )
    planting_median_segments = load_dataset("data/planting/TreePlanting_Medians.shp", True)
    planting_median_segments = planting_median_segments.assign(
        geohash=geohash_series(planting_median_segments['point'], precision=PRECISION)
    )

    trees['POINTS'] = [(tree.longitude, tree.latitude) for tree in trees.itertuples()]
    trees['geohash'] = geohash_series(trees['POINTS'], precision=PRECISION)

    median_mask = trees['location_description'].astype(str).str.lower() == 'median'
    median_trees = match_trees_off_hashes(
        planting_median_segments, trees[median_mask]
    )
    off_median_trees = match_trees_off_hashes(
        planting_street_segments, trees[~median_mask]
    )
    trees = pd.concat([median_trees, off_median_trees], sort=False)
    planting_segments = pd.concat(
        [planting_street_segments.drop_duplicates('SEGMENT'), planting_median_segments.drop_duplicates('SEGMENT')]
    )
    trees = trees.merge(
        planting_segments[["SEGMENT", "YEAR", "REPLACE"]], on="SEGMENT", how="left"
    )
    trees = trees.rename(
        columns={"YEAR": "planting_year", "REPLACE": "replacement_species"}
    )
    return trees


def match_trees_off_hashes(candidate_matches, to_match_df):
    digits = PRECISION
    og_df = to_match_df.copy()
    mapper = {}
    while digits > 0 and len(to_match_df) > 0:
        candidate_matches = candidate_matches.assign(geohash_digits=candidate_matches['geohash'].str[:digits])
        to_match_df = to_match_df.assign(geohash_digits=to_match_df['geohash'].str[:digits])
        merged = pd.merge(candidate_matches, to_match_df, on='geohash_digits')
        if len(merged):
            mapper.update(merged.set_index('tree_id').to_dict()['SEGMENT'])
        to_match_df = to_match_df[~to_match_df['tree_id'].isin(mapper)]
        digits -= 1

    return og_df.assign(SEGMENT=og_df['tree_id'].map(mapper))


def pruning_for_trees(trees):
    """
    Match pruning year for a trees dataframe.

    This takes the same dataframe type that is described in `planting_for_trees`,
    but it assumes that planting_for_trees has already been run, as it
    relies on the street segment having been identified.

    Returns a dataframe with a "pruning_year" column.
    """
    years = {"1718": "2017-2018", "1819": "2018-2019", "1920": "2019-2020"}
    for year in years:
        name_streets = f"data/pruning/pruning{year}_streets.shp"
        name_medians = f"data/pruning/pruning{year}_medians.shp"
        pruning = pd.concat([load_dataset(name_streets), load_dataset(name_medians)])
        pruning[year] = years[year]

        trees = trees.merge(pruning[["SEGMENT", year]], on="SEGMENT", how="left")

    def collapse_years(tree):
        for year in years:
            if not pd.isnull(tree[year]):
                return tree[year]

        return tree[year]

    trees = gpd.GeoDataFrame(
        trees,
        geometry=gpd.points_from_xy(trees['longitude'], trees['latitude']),
        crs=4326
    )

    trees["pruning_year"] = trees.apply(collapse_years, axis=1)
    trees = trees.drop([y for y in years], axis=1)

    pruning_zones = load_dataset("data/pruning/pruning_zones.shp").rename(columns={'Id': 'pruning_zone'})
    trees = gpd.sjoin(pruning_zones, trees, how='right', op='contains').drop(
        columns=['index_left', 'Shape_Leng', 'Shape_Area', 'geometry', 'geohash', 'POINTS']
    )
    return trees


if __name__ == "__main__":
    import sys

    # Load the trees dataset.
    infile = sys.stdin
    outfile = sys.stdout
    if len(sys.argv) > 1:
        infile = open(sys.argv[1], 'r')
    if len(sys.argv) > 2:
        outfile = open(sys.argv[2], 'w')

    trees = pd.read_json(infile)
    trees = planting_for_trees(trees)
    trees = pruning_for_trees(trees)
    rename_columns = {
        "SEGMENT": "segment",
    }
    trees = trees.rename(columns=rename_columns)
    tmp = pd.DataFrame(trees).to_json(orient="records", indent=2)
    outfile.write(tmp)
