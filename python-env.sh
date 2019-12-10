#!/bin/bash 

# FIXME: the first time the projection conversion logic is loaded,
# there seems to be some error around setting up the right paths.
# As far as I can tell, this needs to be fixed upstream.
# Here we trigger that error during setup.
python -c "from pruning_planting import load_dataset; load_dataset('data/planting/TreePlanting_Streets.shp')" || true
