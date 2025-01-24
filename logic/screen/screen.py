"""


Record of Screen


"""
from typing import Optional, Dict

from models.database.screen import ScreenInfo
from util.op_thirdparty.common import insert, delete, commit
from util.op_thirdparty.db_screen import query_screenid_screen


class Screen(object):
    """
    This model is to manage screen.
    """

    def __init__(self, session, _screen: ScreenInfo = None, *args, **kwargs):
        # business property
        self.session = session
        self._screen = _screen

    def __getattr__(self, name):
        if self._screen and hasattr(self._screen, name):
            return getattr(self._screen, name)

        if self._screen and self._screen.screenQAConfig.get(name):
            return self._screen.screenQAConfig.get(name)

        return None

    def __repr__(self):
        return f"{self._screen!r}"

    def format(self) -> Optional[Dict]:
        """
        return with formatted type of self._screen

        :return:
            `List`
        """
        return self._screen.to_dict()

    async def get(
            self,
            uid: Optional[str],
            screenid: Optional[str] = None,
    ) -> Optional[ScreenInfo]:
        """
        get ScreenInfo and fresh self._screen
        If self._screen exists, then this method degenerates into a regular query ScreenInfo method and does not update self._screen

        :param uid: user id
        :param screenid: screen id

        :return:
            `bool`, is that success or not
        """
        if self._screen: return self._screen

        _screen = await query_screenid_screen(self.session, uid, screenid)

        self._screen = _screen
        return _screen

    async def insert(self) -> bool:
        """
        add ScreenInfo, only create ScreenInfo instance but not indicate that exist in database

        :return:
            `bool`, is that success or not

        """
        if not self._screen: return False

        result = await insert(self.session, self._screen)
        return result

    async def delete(self) -> bool:
        """
        delete ScreenInfo from database

        :return:
            `bool`, is that success or not
        """
        if not self._screen: return False

        # delete item in db
        result = await delete(self.session, self._screen)
        return result

    async def update(self) -> bool:
        """
        commit update

        :return:
            `bool`, is that success or not
        """
        return await commit(self.session)








