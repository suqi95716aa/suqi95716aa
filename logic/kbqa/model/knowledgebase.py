"""


Record of KnowledgeBase


"""
from typing import List, Union, Optional

from logic.kbqa.model.knowledge import Knowledge
from models.database.knowledgebase import KnowledgeBaseInfo
from util.op_thirdparty.common import insert, delete, commit
from util.op_thirdparty.db_kb import query_kbid_knowledgebase, query_kbName_knowledgebase
from util.op_thirdparty.db_k import query_list_knowledge, query_condition_knowledge


class KnowledgeBase(object):
    """
    This model is to:
    1. manage files in this KnowledgeBase;
    2. manage operations of this KnowledgeBase;
    3. support dll
    """

    def __init__(self, session, _kb: KnowledgeBaseInfo = None, *args, **kwargs):
        # business property
        self.session = session
        self._kb = _kb
        self._ks: List[Knowledge] = []

    def __getattr__(self, name):
        if self._kb and hasattr(self._kb, name):
            return getattr(self._kb, name)

        return None

    def __repr__(self):
        return f"{self._kb!r}"

    async def format(self) -> Optional[List]:
        """
        return with formatted type of self._kb

        :return:
            `List`
        """
        if not self._kb: return []
        if not self._ks: await self.flush()

        kb_formated = self._kb.to_dict()
        kb_formated.update({"data": [k.format() for k in self._ks]})
        return kb_formated

    async def get(
            self,
            uid: Optional[str],
            *,
            kbid: Optional[str] = None,
            kbName: Optional[str] = None,
    ) -> Optional[KnowledgeBaseInfo]:
        """
        get KnowledgeBase and fresh self._KnowledgeBase
        If self._KnowledgeBase exists, then this method degenerates into a regular query KnowledgeBase method and does not update self._KnowledgeBase

        :param uid: user id
        :param kbid: KnowledgeBase id
        :param kbName: KnowledgeBase name

        :return:
            `bool`, is that success or not
        """
        if self._kb: return self._kb

        params = [kbid, kbName]
        if sum(param is not None for param in params) != 1:
            raise ValueError("Only one of kbid, kbName should be provided.")

        if kbid:
            _kb = await query_kbid_knowledgebase(self.session, uid, kbid)
        else:
            _kb = await query_kbName_knowledgebase(self.session, uid, kbName)

        self._kb = _kb
        return _kb

    async def insert(self) -> bool:
        """
        add KnowledgeBase, only create KnowledgeBase instance but not indicate that exist in database

        :return:
            `bool`, is that success or not

        """
        if not self._kb: return False

        result = await insert(self.session, self._kb)
        return result

    async def delete(self) -> bool:
        """
        delete KnowledgeBase from database

        :return:
            `bool`, is that success or not
        """
        if not self._kb: return False
        if not self._ks: await self.flush()

        # delete file in permanent zone
        [await k.delete() for k in self._ks]

        # delete file in db
        result = await delete(self.session, self._kb)
        return result

    async def update(self) -> bool:
        """
        commit update

        :return:
            `bool`, is that success or not
        """
        return await commit(self.session)

    async def flush(
            self,
            conditions: Union[List, str] = "*",
    ) -> Optional[List[Knowledge]]:
        """
        flush and obtain case with current Knowledge

        :param conditions: query conditions, only support *(all)、List(cids)

        :return:
            `List[Knowledge]`, all c item query correct
        """

        if conditions == "*":
            _cs = await query_list_knowledge(self.session, self._kb.kbid)
        elif isinstance(conditions, List):
            _cs = await query_condition_knowledge(self.session, self._kb.kbid, conditions)
        else:
            raise NotImplemented("Not Support Conditions Type")

        return [Knowledge(self.session, c) for c in _cs] if _cs else None








