FROM continuumio/miniconda3:4.7.10

# Setup conda env
RUN conda update setuptools
RUN conda update -n base -c defaults conda

# This is from the geopandas install page: http://geopandas.org/install.html#creating-a-new-environment
RUN conda config --env --add channels conda-forge
RUN conda config --env --set channel_priority strict

ADD requirements.txt /public-tree-map/requirements.txt
RUN conda install --file /public-tree-map/requirements.txt

COPY src /public-tree-map

WORKDIR /public-tree-map