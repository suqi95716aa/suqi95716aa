from typing import Optional

from util.op_thirdparty.db_user import (
    query_exist_userinfo,
    validate_uname_userinfo,
    validate_phone_userinfo,
    validate_uid_userinfo
)
from util.op_thirdparty.common import insert, delete, commit
from models.database.user import UserInfo


# 用户基类

class UserBaseModel:
    """
    This model is base model of user
    """

    def __init__(self, _user: UserInfo = None, *args, **kwargs):
        self._user = _user

    def __getattr__(self, name):
        if self._user:
            return getattr(self._user, name)
        return None

    async def get(
            self,
            username: Optional[str] = None,
            phone: Optional[str] = None,
            uid: Optional[str] = None,
          ) -> Optional[UserInfo]:
        """
        get user and fresh self._user
        If self._user exists, then this method degenerates into a regular query user method and does not update self_ user

        :param username: username
        :param phone: phone
        :param uid: uid

        :return:
            `bool`, is that success or not
        """
        if self._user: return self._user

        params = [username, phone, uid]
        if sum(param is not None for param in params) != 1:
            raise ValueError("Only one of username, phone, uid, or _user should be provided.")

        if username:
            _user = await validate_uname_userinfo(self.session, username)
        elif phone:
            _user = await validate_phone_userinfo(self.session, phone)
        else:
            _user = await validate_uid_userinfo(self.session, uid)

        self._user = _user
        return _user

    async def insert(self) -> bool:
        """
        add user, only create User instance but not indicate that exist in database

        :return:
            `bool`, is that success or not

        """
        if not self._user: return False
        return await insert(self.session, self._user)

    async def delete(self) -> bool:
        """
        delete add from database

        :return:
            `bool`, is that success or not
        """
        if not self._user: return False
        return await delete(self.session, self._user)

    async def update(self) -> bool:
        """
        commit update

        :return:
            `bool`, is that success or not
        """
        if not self._user: return False
        return await commit(self.session, self._user)

    async def user_exist_by_uname_or_phone(
            self,
            username: Optional[str] = None,
            phone: Optional[str] = None
    ) -> Optional[UserInfo]:
        """
        user exist

        :param session:
        :param username: identify, username
        :param phone: identify, phone

        :return:
            `UserInfo` or `None`, result of query by phone or username
        """

        if not (username and phone):
            return None

        user = await query_exist_userinfo(self.session, username, phone)
        return user
