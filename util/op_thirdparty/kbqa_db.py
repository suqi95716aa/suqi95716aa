from typing import Union, Optional, List, Tuple

from sqlalchemy import select, update, desc, or_

from util.retry import a_retry
from models.database.knowledge import KnowledgeInfo
from models.database.knowledgebase import KnowledgeBaseInfo


@a_retry
async def kbqa_insert(session, item: Union[KnowledgeBaseInfo, KnowledgeInfo]):
    """insert item"""
    session.add(item)
    await session.commit()
    return True


@a_retry
async def kbqa_del(session, item: Union[KnowledgeInfo, KnowledgeBaseInfo]) -> bool:
    """delete item"""
    await session.delete(item)
    await session.commit()
    return True


@a_retry
async def kbqa_kbid_exist_Knowledgebaseinfo(session, kbid: str, uid: str) -> Optional[KnowledgeBaseInfo]:
    """find kb by kbid"""
    result = await session.execute(
        select(KnowledgeBaseInfo).filter(
            KnowledgeBaseInfo.uid == uid,
            KnowledgeBaseInfo.kbid == kbid,
            KnowledgeBaseInfo.kbDeleteTime == None
        )
    )
    return result.first()


@a_retry
async def kbqa_kbid_name_exist_Knowledgebaseinfo(session, uid: str, KBName: str) -> Optional[KnowledgeBaseInfo]:
    """find kb by name"""
    result = await session.execute(
        select(KnowledgeBaseInfo).filter(
            KnowledgeBaseInfo.uid == uid,
            KnowledgeBaseInfo.kbName == KBName,
            KnowledgeBaseInfo.kbDeleteTime == None
        )
    )
    return result.first()


@a_retry
async def kbqa_update_Knowledgebaseinfo(session, obj: KnowledgeBaseInfo) -> bool:
    """insert item if not exists, otherwise update"""
    d = obj.to_dict()
    if d.get("kbid"): del d["kbid"]

    KnowledgeBase_update_stmt = update(KnowledgeBaseInfo). \
        where(KnowledgeBaseInfo.kbid == obj.kbid). \
        values(**d)
    await session.execute(KnowledgeBase_update_stmt)
    await session.commit()
    return True


@a_retry
async def kbqa_all_Knowledgebaseinfo(session, Uid: str) -> List[KnowledgeBaseInfo]:
    """find all kb for user"""
    result = await session.execute(
        select(KnowledgeBaseInfo).filter(KnowledgeBaseInfo.uid == Uid, KnowledgeBaseInfo.kbDeleteTime == None).order_by(
            desc(KnowledgeBaseInfo.kbCreateTime))
    )
    return result.fetchall()


@a_retry
async def kbqa_in_kbids_KnowledgeInfo(session, uid: str, kbisd: List) -> List[Tuple[KnowledgeInfo]]:
    """find the knowledge ids by specify kids"""
    result = await session.execute(
        select(KnowledgeInfo).where(
            KnowledgeInfo.uid == uid,
            KnowledgeInfo.kbid.in_(kbisd),
        )
    )
    return result.fetchall()


@a_retry
async def kbqa_all_kb_KnowledgeInfo(session, uid: str, kbid: str) -> List[KnowledgeInfo]:
    """find all k for user"""
    result = await session.execute(
        select(KnowledgeInfo).filter(KnowledgeInfo.uid == uid, KnowledgeInfo.kbid == kbid).order_by(
            desc(KnowledgeInfo.kCreateTime))
    )
    return result.fetchall()


@a_retry
async def kbqa_kid_exist_KnowledgeInfo(session, uid: str, kbid: str, kid: str) -> KnowledgeInfo:
    """whether the k exists"""
    result = await session.execute(
        select(KnowledgeInfo).filter(
            KnowledgeInfo.uid == uid,
            KnowledgeInfo.kbid == kbid,
            KnowledgeInfo.kid == kid,
            KnowledgeInfo.kDeleteTime == None
        )
    )
    return result.first()


@a_retry
async def kbqa_in_kids_KnowledgeInfo(session, uid: str, kids: List) -> List[Tuple[KnowledgeInfo]]:
    """find the knowledge ids by specify kids"""
    result = await session.execute(
        select(KnowledgeInfo).where(
            KnowledgeInfo.uid == uid,
            KnowledgeInfo.kid.in_(kids),
        )
    )
    return result.fetchall()


@a_retry
async def kbqa_kid_user_KnowledgeInfo(session, uid: str) -> List[Tuple[KnowledgeInfo]]:
    """find all the kids for specify user"""
    result = await session.execute(
        select(KnowledgeInfo).filter(KnowledgeInfo.uid == uid, KnowledgeInfo.kDeleteTime == None)
    )
    return result.fetchall()



