import os

import pandas as pd
from flask import Flask
from sm_parser import parse_trees
import upload_trees
import parse_la_data
import download_images

app = Flask(__name__)


def download_tree_images():
    img_download = download_images.ImageDownloader()
    trees_df, hashed_urls = img_download.get_trees_without_images()
    for idx, row in enumerate(trees_df.itertuples()):
        img_download.get_tree_images(row.id, row.eol_id, hashed_urls)


@app.route("/")
def upload_sm_trees():
    df = pd.read_csv('https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000')
    df = parse_trees(df=df, stdout=False)
    matcher = parse_la_data.SpeciesMatcher(df)
    matched_df = matcher.match(how='left').drop('species_id', axis=1)
    uploader = upload_trees.SMTreeUploader()
    species_mapper = uploader.get_species_ids_mapper()
    matched_df['species_id'] = matched_df['botanical_name'].map(species_mapper)
    uploader.truncate_sm_trees()
    uploader.prepare_df(matched_df)
    uploader.upload_trees(uploader.df, batch_size=0)

    download_tree_images()

    return 'SUCCESS'


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))