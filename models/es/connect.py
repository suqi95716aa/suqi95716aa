from functools import wraps
from elasticsearch import Elasticsearch
from conf.parser import conf2Dict

DB_CONF = conf2Dict()['ES_CONFIG']


def create_es_conn():
    return Elasticsearch(
        hosts=[f"{DB_CONF.get('ES_HOST')}:{DB_CONF.get('ES_PORT')}"]
    )


def attach_es_session(arg1, arg2):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            conn = create_es_conn()
            response = f(conn, *args, **kwargs)
            conn.close()
            return response
        return wrapped
    return decorator
