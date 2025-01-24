
# Redis is an open-source, in-memory data structure store that is used as a distributed cache and
# message broker. It supports various data structures such as strings, lists, sets,
# and sorted sets with range queries, maps, hyperloglogs, geospatial indexes, and bitmaps.

# aioredis official documentation: https://aioredis.readthedocs.io/en/latest/

import aioredis
import asyncio

from conf.parser import conf2Dict

CACHE_CONFIG = conf2Dict()['CACHE_CONFIG']
REDIS_HOST = CACHE_CONFIG["REDIS_HOST"]
REDIS_PORT = CACHE_CONFIG["REDIS_PORT"]
REDIS_AUTH = CACHE_CONFIG["REDIS_AUTH"]
REDIS_PASSWORD = CACHE_CONFIG["REDIS_PASSWORD"]


async def establish_cache_conn(
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        password: str = REDIS_PASSWORD,
        db: int = 0
):
    """
    :param host: Cache host
    :param port: Cache port
    :param password: Cache password
    :param db: Cache db number
    :return:
    """
    return await aioredis.Redis(
        host=host,
        port=port,
        password=password,
        db=db,
        socket_keepalive=True,
        socket_timeout=4.0,
        socket_connect_timeout=3.0,
        retry_on_timeout=True,
        max_connections=10000,
        health_check_interval=20,
        decode_responses=True
    )


rins_sms = asyncio.run(establish_cache_conn(db=1))



