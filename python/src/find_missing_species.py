import pandas as pd


species_id_col_name = 'Species ID'

def filter_new_species_ids(trees_inventory_df, species_df):
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
    species_df = pd.read_csv('data/species_attributes.csv')
    tree_inventory_url = 'https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000'
    trees_inventory_df = pd.read_csv(tree_inventory_url)

    if species_id_col_name not in species_df.columns:
        raise ValueError(f'species_df does not have column: {species_id_col_name}')
    elif species_id_col_name not in trees_inventory_df.columns:
        raise ValueError(f'trees_inventory_df does not have column: {species_id_col_name}')

    new_species_tree_inventory_df = filter_new_species_ids(trees_inventory_df, species_df)
    print(new_species_tree_inventory_df.to_csv(index=False))
