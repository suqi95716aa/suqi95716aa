from typing import Optional, List

from util.retry import a_retry
from models.database.knowledgebase import KnowledgeBaseInfo

from sqlalchemy import select, and_, desc


@a_retry
async def query_list_knowledgebase(
        session,
        uid: Optional[str],
) -> Optional[List[KnowledgeBaseInfo]]:
    """
    query list of all item in KnowledgeBaseInfo with uid

    :param session:
    :param uid: user identify

    :return:
        `Optional[List[KnowledgeBaseInfo]]`, result of query by uid
    """
    stmt = select(KnowledgeBaseInfo).filter(
        and_(
            KnowledgeBaseInfo.uid == uid,
            KnowledgeBaseInfo.kbDeleteTime == None
        )
    ).order_by(desc(KnowledgeBaseInfo.kbCreateTime))
    result = await session.execute(stmt)
    return [
        item[0]
        for item in sorted(result, key=lambda item: item[0].kbCreateTime, reverse=True)
    ]

@a_retry
async def query_condition_knowledgebase(session, uid: str, kbids: List) -> Optional[List[KnowledgeBaseInfo]]:
    """
    query list of knowledgebase with uid and kbids

    :param session:
    :param uid: user identify
    :param kbids: condition
    :return:
    """
    stmt = select(KnowledgeBaseInfo).where(
            KnowledgeBaseInfo.uid == uid,
            KnowledgeBaseInfo.kbid.in_(kbids),
            KnowledgeBaseInfo.kbDeleteTime == None
    ).order_by(desc(KnowledgeBaseInfo.kbCreateTime))
    result = await session.execute(stmt)
    return [
        item[0]
        for item in sorted(result, key=lambda item: item[0].kbCreateTime, reverse=True)
    ]

@a_retry
async def query_kbid_knowledgebase(
        session,
        uid: Optional[str] = None,
        kbid: Optional[str] = None,
) -> Optional[KnowledgeBaseInfo]:
    """
    query exist with kbid

    :param session:
    :param uid: user id
    :param kbid: knowledgebase id

    :return:
        `KnowledgeBaseInfo` or `None`, result of query by kbid
    """
    stmt = select(KnowledgeBaseInfo).filter(
        KnowledgeBaseInfo.uid == uid,
        KnowledgeBaseInfo.kbid == kbid,
        KnowledgeBaseInfo.kbDeleteTime == None
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None


@a_retry
async def query_kbName_knowledgebase(
        session,
        uid: Optional[str] = None,
        kbName: Optional[str] = None,
) -> Optional[KnowledgeBaseInfo]:
    """
    query exist with kbid

    :param session:
    :param uid: user id
    :param kbName: knowledgebase name

    :return:
        `KnowledgeBaseInfo` or `None`, result of query by kbName
    """
    stmt = select(KnowledgeBaseInfo).filter(
        KnowledgeBaseInfo.uid == uid,
        KnowledgeBaseInfo.kbName == kbName,
        KnowledgeBaseInfo.kbDeleteTime == None
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None


