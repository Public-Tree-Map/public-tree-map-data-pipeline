curl https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh;
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
conda env update -f environment.yml 

# FIXME: the first time the projection conversion logic is loaded,
# there seems to be some error around setting up the right paths.
# As far as I can tell, this needs to be fixed upstream.
# Here we trigger that error during setup.
source activate public-tree-map
PYTHONPATH=$(pwd)/python/src python -c "from pruning_planting import load_dataset; load_dataset('data/planting/TreePlanting_Streets.shp')" || true
