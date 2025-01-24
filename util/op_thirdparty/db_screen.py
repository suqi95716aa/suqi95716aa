from typing import Optional, List

from util.retry import a_retry
from models.database.screen import ScreenInfo

from sqlalchemy import select, and_, desc


@a_retry
async def query_list_screen(
        session,
        uid: Optional[str],
) -> Optional[List[ScreenInfo]]:
    """
    query list of all item in ScreenInfo with uid

    :param session:
    :param uid: user identify

    :return:
        `Optional[List[ScreenInfo]]`, result of query by uid
    """
    stmt = select(ScreenInfo).filter(
        and_(
            ScreenInfo.uid == uid,
            ScreenInfo.deleteTime == None
        )
    ).order_by(desc(ScreenInfo.createTime))
    result = await session.execute(stmt)
    return [
        item[0]
        for item in sorted(result, key=lambda item: item[0].createTime, reverse=True)
    ]


@a_retry
async def query_condition_screen(session, uid: str, screenIds: List) -> Optional[List[ScreenInfo]]:
    """
    query list of ScreenInfo with uid and screenIds

    :param session:
    :param uid: user identify
    :param screenIds: condition
    :return:
    """
    stmt = select(ScreenInfo).where(
        ScreenInfo.uid == uid,
        ScreenInfo.screenId.in_(screenIds),
        ScreenInfo.deleteTime == None
    ).order_by(desc(ScreenInfo.createTime))
    result = await session.execute(stmt)
    return [
        item[0]
        for item in sorted(result, key=lambda item: item[0].createTime, reverse=True)
    ]


@a_retry
async def query_screenid_screen(
        session,
        uid: Optional[str] = None,
        screenid: Optional[str] = None,
) -> Optional[ScreenInfo]:
    """
    query exist with screenid

    :param session:
    :param uid: user id
    :param screenid: screen id

    :return:
        `ScreenInfo` or `None`, result of query by screenid
    """
    stmt = select(ScreenInfo).filter(
        ScreenInfo.uid == uid,
        ScreenInfo.screenId == screenid,
        ScreenInfo.deleteTime == None
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None
