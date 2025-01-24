from typing import Union

from util.retry import a_retry
from models.database.user import UserInfo
from models.database.knowledge import KnowledgeInfo
from models.database.knowledgebase import KnowledgeBaseInfo


@a_retry
async def insert(session, item: Union[KnowledgeInfo, KnowledgeBaseInfo, UserInfo]) -> bool:
    """insert item"""
    session.add(item)
    await session.commit()
    return True


@a_retry
async def delete(session, item: Union[KnowledgeInfo, KnowledgeBaseInfo, UserInfo]) -> bool:
    """delete item"""
    await session.delete(item)
    await session.commit()
    return True


@a_retry
async def commit(session) -> bool:
    """
    commit transcation

    :param session:
    :return:
    """
    await session.commit()
    return True




