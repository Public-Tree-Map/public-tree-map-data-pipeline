# Anything that needs to be done before the other rules run
setup:
	mkdir -p build/data

# Runs the entire pipeline using real data sources
release: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node parse-trees.js \
	  | python pruning_planting.py \
	  | node download-images.js \
	  > build/data/trees.json

# Runs the pipeline using local data, but skips the CPU-intensive python tasks
img-test: setup
	cat data/trees.csv \
	  | node parse-trees.js \
	  | node download-images.js \
	  > build/data/trees.json

# Runs the pipeline, but skips downloading images
no-images: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node parse-trees.js \
	  > build/data/trees.json

# Runs with only local data -- uses a sample trees.csv and skips images
local-only: setup
	cat data/trees.csv \
	  | node parse-trees.js \
	  | python pruning_planting.py \
	  > build/data/trees.json

# Removes build artifacts
clean:
	rm -rf build
