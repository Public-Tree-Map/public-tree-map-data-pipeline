#!/bin/bash
set -e

# when running locally setup the node dependencies
if [ -d "/public-tree-map-local" ]; then
    ln -s /public-tree-map/node_modules /public-tree-map-local/node_modules
fi

# run whatever command to run (usually bash)
exec "$@"