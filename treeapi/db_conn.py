import os

import sqlalchemy


def init_connection_engine(local=False):
    prepend_str = '/Users/allent/' if local else ''
    return sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username='root' if local else os.environ['TREE_DB_USER'],
            password=os.environ['TREE_DB_PASS'],
            database="publictrees",
            query={
                "unix_socket": f"{prepend_str}/cloudsql/{os.environ['TREE_DB_CONNECTION_STR']}"
            }
        ),
    )
