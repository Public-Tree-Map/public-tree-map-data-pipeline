#!/bin/bash

mkdir -p build/data

curl 'https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000' | node parse-trees.js | node download-images.js > build/data/trees.json
