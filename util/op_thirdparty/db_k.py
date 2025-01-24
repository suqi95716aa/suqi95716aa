from typing import Optional, List

from util.retry import a_retry
from models.database.knowledge import KnowledgeInfo

from sqlalchemy import select, and_, desc


@a_retry
async def query_list_knowledge(
        session,
        kbid: Optional[str],
) -> Optional[List[KnowledgeInfo]]:
    """
    query list of all item in KnowledgeInfo

    :param session:
    :param kbid: knowledgebase id

    :return:
        `Optional[List[KnowledgeInfo]]`, result of query by kbid
    """
    stmt = select(KnowledgeInfo).filter(
        and_(
            KnowledgeInfo.kbid == kbid,
            KnowledgeInfo.kDeleteTime == None
        )
    ).order_by(desc(KnowledgeInfo.kCreateTime))
    result = await session.execute(stmt)
    return [
        item[0]
        for item in sorted(result, key=lambda item: item[0].kCreateTime, reverse=True)
    ]


@a_retry
async def query_condition_knowledge(session, kbid: str, kids: List) -> List[KnowledgeInfo]:
    """
    query list of KnowledgeInfo in specify condition

    :param session:
    :param kbid: current kb id
    :param kids: kid list
    :return:
    """
    stmt = select(KnowledgeInfo).where(
            KnowledgeInfo.kbid == kbid,
            KnowledgeInfo.kid.in_(kids),
        ).order_by(desc(KnowledgeInfo.kCreateTime))
    result = await session.execute(stmt)
    return [
        item[0]
        for item in sorted(result, key=lambda item: item[0].kCreateTime, reverse=True)
    ]


@a_retry
async def query_kid_knowledge(
        session,
        uid: Optional[str],
        kid: Optional[str],
) -> Optional[KnowledgeInfo]:
    """
    query item with cid

    :param session:
    :param uid: user id
    :param kid: knowledge id

    :return:
        `Optional[KnowledgeInfo]`, result of query by kid
    """
    stmt = select(KnowledgeInfo).filter(
        and_(
            KnowledgeInfo.uid == uid,
            KnowledgeInfo.kid == kid,
            KnowledgeInfo.kDeleteTime == None
        )
    )
    result = await session.execute(stmt)
    first = result.first()
    return first[0] if first else None
