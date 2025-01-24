import aioredis
from typing import Union, Dict

from util.retry import a_retry


@a_retry
async def hset(
    session: aioredis.Redis,
    field: str,
    key: str = None,
    value: Union[str, int] = None,
    mapping: Dict = None,
    expired: int = None
) -> bool:
    """
    set/overwrite hash key in cache

    :param session: Redis session
    :param field: field name
    :param key: key name
    :param value: value to set/overwrite
    :param mapping: dict of key-value pairs
    :param expired: ttl
    :return:
        `bool` Success to execute atom
    """
    if not field: return False

    # mapping first priority
    if mapping: is_success = await session.hset(field, mapping=mapping)
    # key and value set is second priority
    elif field and key: is_success = await session.hset(field, key, value)
    # otherwise get false
    else: return False

    if expired and is_success: await session.expire(field, expired)
    return True


@a_retry
async def hget(
    session: aioredis.Redis,
    field: str,
    key: str,
) -> bool:
    """
    get single hash key in cache

    :param session: Redis session
    :param field: field name
    :param key: key name

    :return:
        `bool` content of key
    """
    return await session.hget(field, key)


@a_retry
async def hgetall(
    session: aioredis.Redis,
    field: str,
) -> Union[None, Dict]:
    """
    get hash keys in cache

    :param session: Redis session
    :param field: field name

    :return:
        `bool` all keys content
    """
    return await session.hgetall(field)


@a_retry
async def getttl(
    session: aioredis.Redis,
    field: str,
) -> int:
    """
    get key ttl

    :param session: Redis session
    :param field: field name

    :return:
        `int` get ttl about key
    """
    return await session.ttl(field)


@a_retry
async def setttl(
    session: aioredis.Redis,
    field: str,
    ttl: int
) -> int:
    """
    get key ttl

    :param session: Redis session
    :param field: field name
    :param ttl: expire time in seconds

    :return:
        `int` get ttl about key
    """
    return await session.expire(field, ttl)



if __name__ == "__main__":
    import asyncio
    from models.cache.connect import rins_sms

    res = asyncio.run(getttl(rins_sms, "key1"))
    print(res)
