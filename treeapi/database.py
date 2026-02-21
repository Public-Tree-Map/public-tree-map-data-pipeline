
import os

from sqlalchemy.orm import sessionmaker
import sqlalchemy
from sqlalchemy import create_engine

LOCAL = True

prepend_str = '/Users/allent/' if LOCAL else ''
engine = create_engine(
    sqlalchemy.engine.url.URL.create(
        drivername="mysql+pymysql",
        username='root' if LOCAL else os.environ['TREE_DB_USER'],
        password=os.environ['TREE_DB_PASS'],
        database="publictrees",
        query={
            "unix_socket": f"{prepend_str}/cloudsql/{os.environ['TREE_DB_CONNECTION_STR']}"
        }
    ),
)

# Session factory bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
