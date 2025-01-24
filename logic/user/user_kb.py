"""

Validate for user.

"""
import os
from io import BytesIO
from typing import List, Optional, Union

from models.database.user import UserInfo
from logic.user.base import UserBaseModel
from logic.kbqa.model.knowledgebase import KnowledgeBase

from router import KBQA_STORAGE_TMP_PATH
from util.str import get_fs_path
from util.op_thirdparty.db_kb import query_list_knowledgebase, query_condition_knowledgebase
from util.op_thirdparty.fs_minio import list_directory, delete_file, upload_file_with_stream, stat_file

USER_FILE_BUCKET = os.environ["USER_FILE_BUCKET"]


class UserForKnowledgeBase(UserBaseModel):
    """
    This model is to:
     1. return knowledgebase with different condition.
     2. validate control.
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
        self.kbs: List[KnowledgeBase] = []

    def __repr__(self):
        return f"User({self._user!r})"

    async def flush(
            self,
            conditions: Union[List, str] = "*",
    ) -> Optional[List[KnowledgeBase]]:
        """
        flush and obtain knowledgebase with current user

        :param conditions: query conditions, only support *(all)、List(cids)

        :return:
            `bool`, all cb item query correct
        """
        if conditions == "*":
            _kbs = await query_list_knowledgebase(self.session, self._user.uid)
        elif isinstance(conditions, List):
            _kbs = await query_condition_knowledgebase(self.session, self._user.uid, conditions)
        else:
            raise NotImplemented("Not Support Conditions Type")

        self.kbs = [KnowledgeBase(self.session, kb) for kb in _kbs]
        return self.kbs

    async def format(self) -> List:

        """
        return list of metadata of current user

        :return:
            `List`
        """
        if not self._user: return []
        if not self.kbs: await self.flush()

        return [await kb.format() for kb in self.kbs]

    def get_temporary_zone(self) -> Optional[List[str]]:
        """
        get list of filename of kbid's staging zone

        :return:
            `Optional[List[str]]`, list of filenames
        """

        file_path = get_fs_path(self._user.uid,  KBQA_STORAGE_TMP_PATH, "/")
        list_file_names = list_directory(bucket_name=USER_FILE_BUCKET, remote_path_prefix=file_path)
        return list_file_names

    def delete_temporary_zone(self, filename: str) -> bool:
        """
        delete file in staging zone

        :param filename: filename will be deleted

        :return:
            `bool`, delete success or not
        """

        tmp_path = get_fs_path("/" + self._user.uid,  KBQA_STORAGE_TMP_PATH, filename)
        deleted = delete_file(bucket_name=USER_FILE_BUCKET, remote_file_path=tmp_path)
        return deleted

    def upload_temporary_zone(self, file) -> bool:
        """
        upload file into staging zone

        :param file: file will be uploaded

        :return:
            `bool`, delete success or not
        """

        tmp_path = get_fs_path("/" + self._user.uid, KBQA_STORAGE_TMP_PATH, file.name)
        uploaded = upload_file_with_stream(
            bucket_name=USER_FILE_BUCKET,
            remote_file_path=tmp_path,
            file_body=BytesIO(file.body),
            file_length=len(file.body)
        )
        return uploaded

    def judge_temporary_zone(self, filename) -> bool:
        """
        query file in s3 of staging zone

        :return:
            `bool`, state of exist file
        """
        remote_tmp_path = get_fs_path(self._user.uid, KBQA_STORAGE_TMP_PATH, filename)
        file_metadata = stat_file(USER_FILE_BUCKET, remote_tmp_path)
        return True if file_metadata else False









