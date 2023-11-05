# Database Connection

You need to set the environment variables
```angular2html
EXPORT TREE_DB_PASS="password"
EXPORT TREE_DB_CONNECTION_STR="lively-sentry-336718:us-west1:public-tree-map-db"
```

Also make sure in `main.py` that `LOCAL=True` for local development.


Assuming the database instance is running, you need to run `cloud-sql-proxy` which uses unix-sockets.
```angular2html
./cloud-sql-proxy --unix-socket ~/cloudsql --credentials-file lively-sentry-336718-fc01c1868439.json lively-sentry-336718:us-west1:public-tree-map-db
```