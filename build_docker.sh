#!/bin/bash
version=$(cat version.txt)
docker build -t captainrandom/public-tree-map:${version} .
docker push captainrandom/public-tree-map:${version}