# Public Tree Map Data Pipeline

## Building the database

### Prerequisites
- `uv` installed
- `stiles.trees.csv` in project root (pre-generated LA tree data)
- `data/trees.csv` (Santa Monica trees)
- `data/species_attributes.csv`
- `data/images.csv` (one-time export — see below)

### Build trees.db

```bash
uv run --with pandas --with geopandas --with shapely build_sqlite.py
```

This produces `trees.db` (~300-500 MB) with all tables, R-tree index, and caches.

### One-time: export images from MySQL

Only needed once to create `data/images.csv`:

```bash
# Start cloud-sql-proxy first
TREE_DB_PASS="$TREE_DB_PASS" \
  TREE_DB_CONNECTION_STR="lively-sentry-336718:us-west1:public-tree-map-db" \
  uv run --with pymysql export_images.py
```

## Running the TreeAPI locally

### Start the FastAPI server

```bash
cd treeapi
TREE_DB_PATH=../trees.db \
  uv run --with fastapi --with "uvicorn[standard]" \
  uvicorn main:app --reload --port 8080
```

The API will be available at http://127.0.0.1:8080.

### API Endpoints
- `GET /species/all` - all species with tree counts
- `GET /species/{species_id}` - tree locations for a species
- `GET /tree/{tree_id}` - single tree details
- `GET /trees/?lat1=&lng1=&lat2=&lng2=&lat3=&lng3=&lat4=&lng4=` - trees in a bounding box
- `GET /random/?species_id=` - heatmap intensity data
- `GET /cities/` - tree counts per city with centroid lat/lng
