"""
Data processing for tree data.
"""
import json

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def load_dataset(name):
    """
    Given a file path, load the data into a geodataframe,
    reproject it into WGS84, and return the geodataframe.
    """
    # Load the street planting shape data, reprojecting into WGS84
    gdf = gpd.read_file(name, crs='+init=epsg:2229')
    gdf = gdf.to_crs({'init': 'epsg:4326', 'no_defs': True})
    return gdf


def planting_for_trees(trees, name_lookup):
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
    planting_street_segments = load_dataset("data/planting/TreePlanting_Streets.shp")
    planting_median_segments = load_dataset("data/planting/TreePlanting_Medians.shp")

    def nearest_planting_segment(tree):
        """
        Given a row from the trees dataset, find the planting segment that contains
        it. Then return that segment id, planting year, and replacement species.
        """
        # Construct a shapely point from the tree data
        pt = Point(tree["longitude"], tree["latitude"])

        # Based on the description of the tree, select which df to search
        segments = planting_median_segments if str(
            tree["location_description"]
        ).lower() == "median" else planting_street_segments

        # Find the row with the minimum distance from the point.
        row = segments.distance(pt).idxmin()
        if pd.isna(row):
            return row
        segment = segments.iloc[row]
        return segment["SEGMENT"]

    trees["SEGMENT"] = trees.apply(nearest_planting_segment, axis=1)
    planting_segments = pd.concat([planting_street_segments, planting_median_segments])
    trees = trees.merge(
        planting_segments[["SEGMENT", "YEAR", "REPLACE"]], on="SEGMENT", how="left"
    )
    trees = trees.rename(
        columns={"YEAR": "planting_year", "REPLACE": "replacement_species"}
    )

    def add_replacement_common_name(row):

        # Loop through multiple, comma separated scientific names and generate a comma separated list of
        # the common names to add as a new column of the tress Dataframe.

        common_names = ""

        for scientific_name in [x.strip() for x in row["replacement_species"].split(',')]:
            if scientific_name in name_lookup.keys():
                common_names = common_names + name_lookup[scientific_name] + ", "
            else:
                common_names += "INVALID, "

        common_names = common_names[:-2]

        return common_names

    trees["replacement_common_name"] = trees.apply(add_replacement_common_name, axis=1)

    return trees


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

    trees["pruning_year"] = trees.apply(collapse_years, axis=1)
    trees = trees.drop([y for y in years], axis=1)


    pruning_zones = load_dataset("data/pruning/pruning_zones.shp")
    def get_pruning_zone(tree):
        """
        Given a row from the trees dataset, find the pruning zone that contains
        it. Then return that segment id, planting year, and replacement species.
        """
        # Construct a shapely point from the tree data
        pt = Point(tree["longitude"], tree["latitude"])
        for zone in pruning_zones.iterrows():
            if zone[1].geometry.contains(pt):
                return zone[1]["Id"]
        return np.nan
    trees["pruning_zone"] = trees.apply(get_pruning_zone, axis=1)

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

    with open('data/botanical_commonname.json') as json_lookup_file:
        name_lookup = json.load(json_lookup_file)

    trees = pd.read_json(infile)
    trees = planting_for_trees(trees, name_lookup)
    trees = pruning_for_trees(trees)
    rename_columns = {
        "SEGMENT": "segment",
    }
    trees = trees.rename(columns=rename_columns)
    tmp = trees.to_json(orient="records")
    outfile.write(json.dumps(json.loads(tmp), indent=2))
