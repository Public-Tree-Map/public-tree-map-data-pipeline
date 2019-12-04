#!/bin/bash
set -e
ln -s /public-tree-map/node_modules /public-tree-map-local/node_modules

# run whatever comes next (usually bash)
exec "$@"