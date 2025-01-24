"""

Validate for user.

"""
from typing import List, Optional, Union

from models.database.user import UserInfo
from logic.user.base import UserBaseModel
from logic.screen.screen import Screen
from util.op_thirdparty.db_screen import query_list_screen, query_condition_screen


class UserForScreen(UserBaseModel):
    """
    This model is to manage screen
    """

    def __init__(
            self,
            session,
            _user: UserInfo = None,
            *args,
            **kwargs
    ):
        """
        :param session: database connection
        :param _user: default None, userInfo object
        :param args:
        :param kwargs:
        """
        super().__init__(_user, *args, **kwargs)

        # business property
        self.session = session
        self.screens: List[Screen] = []

    def __repr__(self):
        return f"User({self._user!r})"

    async def flush(
            self,
            conditions: Union[List, str] = "*",
    ) -> Optional[List[Screen]]:
        """
        flush and obtain screen with current user

        :param conditions: query conditions, only support *(all)、List(cids)

        :return:
            `bool`, all cb item query correct
        """
        if conditions == "*":
            _screens = await query_list_screen(self.session, self._user.uid)
        elif isinstance(conditions, List):
            _screens = await query_condition_screen(self.session, self._user.uid, conditions)
        else:
            raise NotImplemented("Not Support Conditions Type")

        self.screens = [Screen(self.session, screen) for screen in _screens]
        return self.screens

    async def format(self) -> List:

        """
        return list of metadata of current user

        :return:
            `List`
        """
        if not self._user: return []
        if not self.screens: await self.flush()

        return [screen.format() for screen in self.screens]











