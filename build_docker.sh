#!/bin/bash
docker build -t public-tree-map:latest .
docker build -t public-tree-map-prod:latest -f Dockerfile-prod .