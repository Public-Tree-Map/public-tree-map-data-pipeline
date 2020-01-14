import argparse

import pandas as pd


species_id_col_name = 'Species ID'


def parse_args():
    parser = argparse.ArgumentParser(description='Finds rows in trees inventory with species id missing from species_attributes.csv.')
    parser.add_argument('-u', '--trees-inventory-url',
        default='https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000',
        help='trees inventory url')
    parser.add_argument('-s', '--species-attributes-csv',
        default='data/species_attributes.csv',
        help='file path for species_attributes.csv')

    return parser.parse_args()


def filter_new_species_ids(trees_inventory_df, species_df):
    """
    This finds full rows (aka all columns) from trees_inventory_df where
    the species_id_col_name is missing from the species_df.

    This is done by doing a left join from trees_inventory_df
    to species_df on species_id_col_name (column) in both dataframes
    (using the merge method). Keep in mind that this creates an extra
    column "_merged" in the resulting dataframe.

    Then we filter where we only have the trees_inventory_df row but no
    corresponding species_df.

    Finally we drop the "_merge" column, because it is a useless
    byproduct of the merge operation.

    :param trees_inventory_df: dataframe containing all trees from the tree inventory dataset
    :param species_df: the dataframe containing all rows from the species attributes dataset

    :return: dataframe where all rows from trees_inventory_df "Species ID" not found in the species_df
    """
    return pd.\
        merge(
            trees_inventory_df,
            species_df[species_id_col_name],
            on=species_id_col_name,
            how='left',
            indicator=True
        ).\
        query('_merge == "left_only"').\
        drop('_merge', 1)

if __name__ == '__main__':
    args = parse_args()

    # read in the data
    species_df = pd.read_csv(args.species_attributes_csv)
    trees_inventory_df = pd.read_csv(args.trees_inventory_url)

    # verify that both dataframes have the join column
    if species_id_col_name not in species_df.columns:
        raise ValueError(f'species_df does not have column: {species_id_col_name}')
    elif species_id_col_name not in trees_inventory_df.columns:
        raise ValueError(f'trees_inventory_df does not have column: {species_id_col_name}')

    # do a left join to find rows with new species ids and print them out
    new_species_tree_inventory_df = filter_new_species_ids(trees_inventory_df, species_df)
    print(new_species_tree_inventory_df.to_csv(index=False))
