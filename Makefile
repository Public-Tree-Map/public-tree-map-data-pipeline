# Anything that needs to be done before the other rules run
SHELL := /bin/bash
setup:
	mkdir -p build/data

# Runs the entire pipeline using real data sources
release: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node parse-trees.js \
	  | python pruning_planting.py \
	  | node download-images.js \
	  | node split-trees.js build/data


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

find-missing-species:
	python find_missing_species.py

# Removes build artifacts
clean:
	rm -rf build

circleci-local: clean
	circleci local execute --job deploy