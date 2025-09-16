from sqlalchemy import create_engine
import ssl
from os import environ

connect = None
DictCursor = None
IntegrityError = None

SCHEME = 'mysql+pymysql'
PORT = 3306
CHARSET = 'utf8'
USER = 'root'
DATABASE = 'oncall'

def init(config):
    global connect
    global DictCursor
    global IntegrityError

    connect_args = {}
    if config['conn'].get('use_ssl'):
        ssl_ctx = ssl.create_default_context()
        connect_args["ssl"] = ssl_ctx

    password = environ.get('MYSQL_ROOT_PASSWORD')
    host = environ.get('MYSQL_HOST', 'localhost')

    connect_str = f'{SCHEME}://{USER}:{password}@{host}:{PORT}/{DATABASE}?charset=utf8'
    engine = create_engine(
        connect_str
    )

    dbapi = engine.dialect.dbapi
    IntegrityError = dbapi.IntegrityError

    DictCursor = dbapi.cursors.DictCursor
    connect = engine.raw_connection
