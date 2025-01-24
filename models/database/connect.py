from functools import wraps
from contextvars import ContextVar

from conf.parser import conf2Dict

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from urllib.parse import quote_plus as urlquote


DB_CONF = conf2Dict()['DB_CONFIG']
_base_model_session_ctx = ContextVar("session")


bind = create_async_engine(
    f"mysql+aiomysql://"
    f"{DB_CONF.get('MYSQL_USERNAME')}:"
    f"{urlquote(DB_CONF.get('MYSQL_PASSWORD'))}@"
    f"{DB_CONF.get('MYSQL_HOST')}:"
    f"{DB_CONF.get('MYSQL_PORT')}/"
    f"{DB_CONF.get('MYSQL_DATABASE')}?charset={DB_CONF.get('MYSQL_CHARSET')}"
    , echo=True, max_overflow=-1, pool_pre_ping=True, pool_recycle=-1)


def attach_db_session(f):
    @wraps(f)
    async def wrapped(request, *args, **kwargs):
        # establish
        request.ctx.session = sessionmaker(bind, class_=AsyncSession, expire_on_commit=False, autoflush=False)()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)

        # do
        response = await f(request, *args, **kwargs)

        # release
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()
        return response
    return wrapped




