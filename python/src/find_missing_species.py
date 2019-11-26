import pandas as pd


def filter_new_species_ids(trees_inventory_df, species_df):
    return pd.\
        merge(
            trees_inventory_df,
            species_df['Species ID'],
            on='Species ID',
            how='left',
            indicator=True
        ).\
        query('_merge == "left_only"').\
        drop('_merge', 1)

if __name__ == '__main__':
    species_df = pd.read_csv('data/species_attributes.csv')
    tree_inventory_url = 'https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000'
    trees_inventory_df = pd.read_csv(tree_inventory_url)

    new_species_tree_inventory_df = filter_new_species_ids(trees_inventory_df, species_df)
    print(new_species_tree_inventory_df.to_csv(index=False))
