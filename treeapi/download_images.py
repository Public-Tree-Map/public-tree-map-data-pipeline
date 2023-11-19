import os
from typing import Optional, Set
import dataclasses
import hashlib

from google.cloud import storage
from PIL import Image
from io import BytesIO
import requests
import pandas as pd
import sqlalchemy

from db_conn import init_connection_engine


@dataclasses.dataclass
class TreeImage:
    species_id: int
    retrieval_url: str
    hashed_url: str
    img_type: str
    description: str
    image: Optional
    author: Optional[str]
    author_url: Optional[str]


class ImageDownloader(object):
    MAX_SIZE = (1024, 1024)

    def __init__(self, local):

        self.bucket = storage.Client().bucket('public-tree-map-images')
        self.local = local

    def insert_tree_into_db(self, tree: TreeImage):
        with init_connection_engine(self.local).connect() as conn:
            table = sqlalchemy.Table('images', sqlalchemy.MetaData(), autoload_with=conn)
            stmt = sqlalchemy.insert(table).values(
                extension=tree.img_type,
                original_url=tree.retrieval_url,
                details=tree.description if tree.description else None,
                hashed_original_url=tree.hashed_url,
                species_id=tree.species_id,
                author=tree.author if tree.author else None,
                author_url=tree.author_url if tree.author_url else None
            )

            conn.execute(stmt)
            conn.commit()

    def get_and_upload_image(self, tree_image: TreeImage):
        image_key = f'{tree_image.hashed_url}.{tree_image.img_type}'
        blob = self.bucket.blob(image_key)
        if not blob.exists():
            r = requests.get(tree_image.retrieval_url)
            if r.ok:
                img = Image.open(BytesIO(r.content))
                img.thumbnail(self.MAX_SIZE)
                tree_image.image = img
                byte_stream = BytesIO()
                img.save(byte_stream, format=img.format)
                byte_stream.seek(0)
                blob.upload_from_file(
                    byte_stream,
                    content_type=r.headers['Content-Type']
                )

        self.insert_tree_into_db(tree_image)
        return tree_image

    def get_tree_images(self, tree_id, eol_id, existing_images: Set[str]):

        assert os.environ.get('TREE_SALT') is not None

        url = f'http://eol.org/api/pages/1.0.json?id=${eol_id}&images_per_page=3&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false'
        r = requests.get(url)
        images_to_retrieve = []
        if r.ok:
            request_body = r.json()
            data_objects = request_body['taxonConcept'].get('dataObjects')
            if data_objects:
                for data_object in data_objects:
                    hashed_url = hashlib.md5(f"{data_object['eolMediaURL']}{os.environ['TREE_SALT']}".encode('utf-8')).hexdigest()
                    if hashed_url not in existing_images:
                        images_to_retrieve.append(
                            TreeImage(
                                tree_id,
                                data_object['eolMediaURL'],
                                hashed_url,
                                data_object['dataSubtype'],
                                data_object['description'] if 'description' in data_object else None,
                                None,
                                data_object['rightsHolder'].strip() if 'rightsHolder' in data_object else None,
                                f'https://eol.org/pages/{int(eol_id)}/media'
                            )
                        )

                if images_to_retrieve:
                    for image in images_to_retrieve:
                        uploaded_tree = self.get_and_upload_image(image)
                        if uploaded_tree:
                            existing_images.add(uploaded_tree.hashed_url)

    def get_trees_without_images(self):
        with init_connection_engine(self.local).connect() as conn:
            sql = sqlalchemy.text(
                """
                    SELECT
                        S.id,
                        S.eol_id,
                        COUNT(DISTINCT I.id) AS cnt
                    FROM species S
                    LEFT JOIN images I ON S.id = I.species_id
                    GROUP BY 1, 2
                    HAVING cnt < 3
                """
            )
            tree_results = conn.execute(sql).mappings().fetchall()
            sql = sqlalchemy.text(
                """
                    SELECT
                        hashed_original_url
                    FROM images
                """
            )
            result_set = conn.execute(sql).mappings()
            image_results = set([row['hashed_original_url'] for row in result_set.fetchall()])
        return pd.DataFrame(tree_results), image_results


if __name__ == "__main__":
    img_download = ImageDownloader(local=True)
    trees_df, hashed_urls = img_download.get_trees_without_images()
    for idx, row in enumerate(trees_df.itertuples()):
        print(f'{idx}/{len(trees_df)}')
        img_download.get_tree_images(row.id, row.eol_id, hashed_urls)