#!/usr/bin/env bash

conda create -n tree-map
conda activate tree-map
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict
conda install python=3
conda install --file requirements.txt