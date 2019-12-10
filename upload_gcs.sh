#!/bin/bash

set -e

GOOGLE_PROJECT_ID=$1
GCLOUD_SERVICE_KEY=$2

if ! make release; then
    exit -1;
fi

echo ${GCLOUD_SERVICE_KEY} | gcloud auth activate-service-account --key-file=-
gcloud --quiet config set project ${GOOGLE_PROJECT_ID}
gsutil cp -Z build/data/map.json gs://public-tree-map/data/
gsutil -m cp -Z build/data/trees/*.json gs://public-tree-map/data/trees/
gsutil setmeta -h "Cache-Control:public, max-age=43200" gs://public-tree-map/data/map.json
gsutil -m setmeta -h "Cache-Control:public, max-age=43200" gs://public-tree-map/data/trees/*.json
gsutil -m cp -r build/img gs://public-tree-map/