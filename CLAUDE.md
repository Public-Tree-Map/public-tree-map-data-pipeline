# Public Tree Map Data Pipeline

## Running the TreeAPI locally

### Prerequisites
- `uv` installed
- `cloud-sql-proxy` binary in project root
- GCP credentials file: `lively-sentry-336718-fc01c1868439.json` in project root
- `TREE_DB_PASS` environment variable set (not stored here)

### 1. Start the Cloud SQL Proxy

```bash
# Remove stale socket if needed
rm -f /tmp/lively-sentry-336718:us-west1:public-tree-map-db

# Start the proxy
./cloud-sql-proxy --unix-socket /tmp \
  --credentials-file lively-sentry-336718-fc01c1868439.json \
  lively-sentry-336718:us-west1:public-tree-map-db
```

### 2. Start the FastAPI server

```bash
cd treeapi
LOCAL=1 \
  TREE_DB_PASS="$TREE_DB_PASS" \
  TREE_DB_CONNECTION_STR="lively-sentry-336718:us-west1:public-tree-map-db" \
  uv run --with fastapi --with "uvicorn[standard]" --with pymysql --with sqlalchemy \
  uvicorn main:app --reload --port 8080
```

The API will be available at http://127.0.0.1:8080.

### API Endpoints
- `GET /species/all` - all species with tree counts
- `GET /species/{species_id}` - tree locations for a species
- `GET /tree/{tree_id}` - single tree details
- `GET /trees/?lat1=&lng1=&lat2=&lng2=&lat3=&lng3=&lat4=&lng4=` - trees in a bounding polygon
- `GET /random/?species_id=` - heatmap intensity data
