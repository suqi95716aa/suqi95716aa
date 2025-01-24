from functools import wraps
from contextvars import ContextVar

from conf.parser import conf2Dict

from pymilvus import (
    connections,
    Collection,
)

DB_CONF = conf2Dict()['MILVUS_CONFIG']
_base_model_session_ctx = ContextVar("session")


def create_collection_conn(collection_name: str):
    connections.connect(host=DB_CONF.get("host"), port=DB_CONF.get("port"))
    return Collection(collection_name)


def attach_v_session(collection_name: str):
    def decorator(f):
        @wraps(f)
        async def wrapped(request, *args, **kwargs):
            # establish
            request.ctx.v_session = create_collection_conn(collection_name)
            request.ctx.v_session_ctx_token = _base_model_session_ctx.set(request.ctx.v_session)
            # do
            response = await f(request, *args, **kwargs)
            # release
            if hasattr(request.ctx, "v_session_ctx_token"):
                _base_model_session_ctx.reset(request.ctx.v_session_ctx_token)
                connections.disconnect("default")
            return response

        return wrapped
    return decorator



