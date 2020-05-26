#!/usr/bin/env bash

set -o errexit  # abort on nonzero exitstatus
set -o nounset  # abort on unbound variable
set -o pipefail # don't hide errors within pipes

function upload_google_cloud() {
  gcloud_service_key="${1}"
  google_project_id="${2}"
  echo "${gcloud_service_key}" | gcloud auth activate-service-account --key-file=-
  gcloud --quiet config set project "${google_project_id}"
  gsutil cp -Z build/data/map.json gs://public-tree-map/data/
  gsutil -m rsync -r -c  build/data/trees gs://public-tree-map/data/trees
  gsutil setmeta -h "Cache-Control:public, max-age=43200" gs://public-tree-map/data/map.json
  gsutil -m setmeta -h "Cache-Control:public, max-age=43200" gs://public-tree-map/data/trees/*.json
  gsutil -m rsync -r -c build/img gs://public-tree-map/img
}

GCLOUD_SERVICE_KEY="${1:-}"
GOOGLE_PROJECT_ID="${2:-}"
BRANCH_NAME="${3}"

if [[ "${BRANCH_NAME}" == 'master' ]]; then
  if [[ "${GCLOUD_SERVICE_KEY}" != '' && "${GOOGLE_PROJECT_ID}" != '' ]]; then
    upload_google_cloud "${GCLOUD_SERVICE_KEY}" "${GOOGLE_PROJECT_ID}"
  else
    echo either GOOGLE_PROJECT_ID or GCLOUD_SERVICE_KEY has not been specified.
  fi
else
  echo "${BRANCH_NAME}" does not support pushing to google storage.
fi
