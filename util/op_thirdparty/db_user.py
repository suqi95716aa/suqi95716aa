from typing import Union, Optional

from util.retry import a_retry
from models.database.user import UserInfo

from sqlalchemy import select, and_, or_


@a_retry
async def query_exist_userinfo(
        session,
        username: Optional[str] = None,
        phone: Optional[str] = None,
) -> Union[None, UserInfo]:
    """
    query exist by username or phone

    :param session:
    :param username: username
    :param phone: user phone

    :return:
        `UserInfo` or `None`, result of query by username
    """
    stmt = select(UserInfo).filter(
        or_(
            and_(UserInfo.username == username, UserInfo.deleteTime == None),
            and_(UserInfo.phone == phone, UserInfo.deleteTime == None)
        )
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None


@a_retry
async def validate_uname_userinfo(
        session,
        username: Optional[str] = None,
) -> Union[None, UserInfo]:
    """
    query exist by username

    :param session:
    :param username: username

    :return:
        `UserInfo` or `None`, result of query by username
    """
    stmt = select(UserInfo).filter(
        UserInfo.username == username,
        UserInfo.deleteTime == None
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None


@a_retry
async def validate_phone_userinfo(
        session,
        phone: Optional[str] = None,
) -> Union[None, UserInfo]:
    """
    query exist by phone

    :param session:
    :param phone: user phone

    :return:
        `UserInfo` or `None`, result of query by username
    """
    stmt = select(UserInfo).filter(
        UserInfo.phone == phone,
        UserInfo.deleteTime == None
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None


@a_retry
async def validate_uid_userinfo(
        session,
        uid: Optional[str] = None,
) -> Union[None, UserInfo]:
    """
    query exist by phone

    :param session:
    :param uid: user identify

    :return:
        `UserInfo` or `None`, result of query by username
    """
    stmt = select(UserInfo).filter(
        UserInfo.uid == uid,
        UserInfo.deleteTime == None
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None





