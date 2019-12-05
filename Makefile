python-dir=./python/src
node-dir=./node/src

# Anything that needs to be done before the other rules run
setup:
	mkdir -p build/data

# Runs the entire pipeline using real data sources
release: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node $(node-dir)/parse-trees.js \
	  | python $(python-dir)/pruning_planting.py \
	  | node $(node-dir)/download-images.js \
	  | node $(node-dir)/split-trees.js build/data

release-docker: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/parse-trees.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-python:latest python /public-tree-map/pruning_planting.py \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/download-images.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data -v $$(pwd)/build:/public-tree-map/build public-tree-map-node:latest node /public-tree-map/split-trees.js build/data

# Runs the pipeline using local data, but skips the CPU-intensive python tasks
img-test: setup
	cat data/trees.csv \
	  | node $(node-dir)/parse-trees.js \
	  | node $(node-dir)/download-images.js \
	  | node $(node-dir)/split-trees.js build/data

img-test-docker: setup
	cat data/trees.csv \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/parse-trees.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/download-images.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data -v $$(pwd)/build:/public-tree-map/build public-tree-map-node:latest node /public-tree-map/split-trees.js build/data

# Runs the pipeline, but skips downloading images
no-images: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | node $(node-dir)/parse-trees.js \
	  | node $(node-dir)/split-trees.js build/data

no-images-docker: setup
	curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$$limit=50000' \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/parse-trees.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data -v $$(pwd)/build:/public-tree-map/build public-tree-map-node:latest node /public-tree-map/split-trees.js build/data

# Runs with only local data -- uses a sample trees.csv and skips images
local-only: setup
	cat data/trees.csv \
	  | node $(node-dir)/parse-trees.js \
	  | python $(python-dir)/pruning_planting.py \
	  | node $(node-dir)/split-trees.js build/data

local-only-docker: setup
	cat data/trees.csv \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/parse-trees.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-python:latest python /public-tree-map/pruning_planting.py 2>/dev/null \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data -v $$(pwd)/build:/public-tree-map/build public-tree-map-node:latest node /public-tree-map/split-trees.js build/data

# Runs with only local data and skips python processing
fast: setup
	cat data/trees.csv \
	  | node $(node-dir)/parse-trees.js \
	  | node $(node-dir)/split-trees.js build/data

fast-docker: setup
	cat data/trees.csv \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data public-tree-map-node:latest node /public-tree-map/parse-trees.js \
	  | docker run -i --rm -v $$(pwd)/data:/public-tree-map/data -v $$(pwd)/build:/public-tree-map/build public-tree-map-node:latest node /public-tree-map/split-trees.js build/data

# Removes build artifacts
clean:
	rm -rf build
