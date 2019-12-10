setup:
	mkdir -p build/data

# Runs the entire pipeline using real data sources
release: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node parse-trees.js \
	  | python pruning_planting.py \
	  | node download-images.js \
	  | node split-trees.js build/data

deploy:
	echo $(GCLOUD_SERVICE_KEY) | gcloud auth activate-service-account --key-file=-
	gcloud --quiet config set project $(GOOGLE_PROJECT_ID)
	gsutil cp -Z build/data/map.json gs://public-tree-map/data/
	gsutil -m cp -Z build/data/trees/*.json gs://public-tree-map/data/trees/
	gsutil setmeta -h "Cache-Control:public, max-age=43200" gs://public-tree-map/data/map.json
	gsutil -m setmeta -h "Cache-Control:public, max-age=43200" gs://public-tree-map/data/trees/*.json
	gsutil -m cp -r build/img gs://public-tree-map/

# Runs the pipeline using local data, but skips the CPU-intensive python tasks
img-test: setup
	cat data/trees.csv \
	  | node parse-trees.js \
	  | node download-images.js \
	  | node split-trees.js build/data

# Runs the pipeline, but skips downloading images
no-images: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node parse-trees.js \
	  | node split-trees.js build/data

# Runs with only local data -- uses a sample trees.csv and skips images
local-only: setup
	cat data/trees.csv \
	  | node parse-trees.js \
	  | python pruning_planting.py \
	  | node split-trees.js build/data

# Runs with only local data and skips python processing
fast: setup
	cat data/trees.csv \
	  | node parse-trees.js \
	  | node split-trees.js build/data

# Removes build artifacts
clean:
	rm -rf build

build-proj:
	circleci build --job deploy