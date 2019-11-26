import os.path
import pandas as pd

from tests import get_script_dir
from find_missing_species import species_id_col_name, filter_new_species_ids


def test_find_missing_species():
    csv_file_name = os.path.join(get_script_dir(__file__), 'tree_inventory.csv')
    tree_inventory_df = pd.read_csv(csv_file_name)

    species_id_numbers = set([75, 80, 46, 1434])
    species_df = pd.DataFrame([{species_id_col_name: species_id} for species_id in species_id_numbers])
    # show existing values
    print(tree_inventory_df[species_id_col_name].head(10))
    results = filter_new_species_ids(tree_inventory_df, species_df)

    assert tree_inventory_df[tree_inventory_df[species_id_col_name] == 56].equals(results)