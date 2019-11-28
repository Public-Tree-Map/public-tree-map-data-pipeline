FROM node:9.11.1

# TODO: should consider refactoring out node code from python code in different dirs.
COPY src /public-tree-map
ADD package.json /public-tree-map/package.json
ADD package-lock.json /public-tree-map/package-lock.json

WORKDIR /public-tree-map
RUN npm install