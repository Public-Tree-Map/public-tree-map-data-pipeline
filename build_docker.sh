#!/bin/bash
version=$(cat version.txt)
docker build --no-cache -t publictreemap/public-tree-map:${version} .
docker push publictreemap/public-tree-map:${version}