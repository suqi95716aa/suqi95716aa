"""

Validate for user.

"""
import os
from io import BytesIO
from typing import Optional, Dict, List, Tuple, Union

from models.graph.connect import create_g_conn
from router import KBQA_STORAGE_TMP_PATH, KBQA_STORAGE_PATH
from logic.kbqa.flow.flow_chunks import flow as flow_to_chunk
from logic.kbqa.flow.flow_entity_extraction import flow as flow_to_entity_extract
from logic.kbqa.flow.flow_upsert import flow as flow_upsert
from logic.kbqa.chunk import to_chunks, to_generate_parent_docs, read_content_from, to_generate_parent_docs_by_docs
from api.umi_ocr import umi_file_upload, umi_task_result, umi_file_delete, umi_image_result
from models.database.knowledge import KnowledgeInfo
from models.milvus.connect import create_v_conn
from service.ragfusion.core.document.document import Document
from service.ragfusion.vectorstore.milvus import Milvus
from util.common import docx_2_pdf
from util.str import get_fs_path, build_col_name
from util.op_thirdparty.db_k import query_kid_knowledge
from util.op_thirdparty.common import delete, commit
from util.op_thirdparty.kbqa_vector import a_kbqa_expr_query, a_kbqa_delete
from util.op_thirdparty.fs_minio import delete_file, stat_file, download_file_to_memory

from urllib3 import BaseHTTPResponse

ENTITY_SUPPORT_TYPES = ["pdf", "word"]
USER_FILE_BUCKET = os.environ["USER_FILE_BUCKET"]
TEXT_METADATA_NAMES = ["parent_id", "child_id", "sequence", "kbid", "kid"]


class Knowledge:
    """
    This model is to:
     1. manage case metadata.
     2. manage file status.
    """

    def __init__(self, session=None, _k: KnowledgeInfo = None, *args, **kwargs):
        # business property
        self._k = _k
        self.vectors = None
        self.session = session
        self.mconn: Milvus = None
        self.contents: List[Document] = None
        self.file_buffer: Union[BaseHTTPResponse, BytesIO] = None

        if self._k: self._create_conn()

    def __getattr__(self, name):
        if self._k and hasattr(self._k, name):
            return getattr(self._k, name)

        if self._k and self._k.kconfig.get(name):
            return self._k.kconfig.get(name)

        return None

    def get_suffix(self):
        return self._k.kName.split(".")[-1]

    def _create_conn(self):
        def create_vconn(self):
            if not self.mconn:
                self.mconn = create_v_conn(
                    col_name=build_col_name(["v", self._k.uid]),
                    priority_alias=self._k.uid
                )
        def create_gconn(self):
            if not self.gconn:
                self.gconn = create_g_conn()

        create_vconn(self)
        create_gconn(self)


    # def __repr__(self):
    #     return f"{self._k!r}"

    async def get(
            self,
            uid: Optional[str],
            kid: Optional[str]
    ) -> Optional[KnowledgeInfo]:
        """
        get knowledge and fresh self._k
        If self._k exists, then this method degenerates into a regular query knowledge method and does not update self._k

        :param uid: user id
        :param kid: knowledge id

        :return:
            `bool`, is that success or not
        """
        if self._k: return self._k

        _k = await query_kid_knowledge(self.session, uid, kid)
        self._k = _k
        self._create_conn()
        return _k

    async def insert(self) -> bool:
        """
        add knowledge, only create case instance but not indicate that exist in database

        :return:
            `bool`, is that success or not

        """
        if not self._k: return False
        self._create_conn()

        entities: List[Union[Document, Dict]] = []
        relationships: List[Union[Document, Dict]] = []

        try:
            # file exist validate validate
            file_exist = self.query_file_exist()
            if not file_exist: return False

            # file load
            if not self.file_buffer: self.query_file_to_memory()

            # flow to generate chunk、 entity and relationship
            flow_chunk_res = await flow_to_chunk(self)
            flow_entity_res = await flow_to_entity_extract(self)

            # generate document object of entity and relationship (combine same entity and relation)
            text_chunk = flow_chunk_res["k_docs"]
            text_chunk = [
                Document(
                    page_content=doc.page_content,
                    metadata={k: v for k, v in doc.metadata.items() if k in TEXT_METADATA_NAMES})
                for doc in text_chunk
            ]
            for category in flow_entity_res["k_categories"].keys():
                c_entities = flow_entity_res["k_categories"][category]["entities"]
                c_relationships = flow_entity_res["k_categories"][category]["relationship"]
                entities.extend(c_entities)
                relationships.extend(c_relationships)

            # flow to upsert to vector and graph db
            flow_upsert_res = await flow_upsert(self, text_chunk, entities, relationships)
            print(flow_upsert_res)
            return True

        except Exception as e:
            print(e)
            return False

    async def delete(self) -> bool:
        """
        delete knowledge from database
        Notion: The instance returned without querying the database
        needs to be inserted into the database before calling this method.

        :return:
            `bool`, is that success or not
        """
        if not self._k: return False
        self._create_conn()

        del_file = self.delete_file()
        del_vec = await self._delete_v_chunk()
        del_item = await delete(self.session, self._k)
        return del_file and del_vec and del_item

    async def update(self) -> bool:
        """
        commit update

        :return:
            `bool`, is that success or not
        """
        return await commit(self.session)

    def query_file_exist(self) -> bool:
        """
        query file with _k attribute `kPath` in s3

        :return:
            `bool`, state of exist file
        """

        file_metadata = stat_file(USER_FILE_BUCKET, self._k.kPath)
        return True if file_metadata else False

    def delete_file(self) -> bool:
        """
        delete file with _k attribute `kPath` in s3

        :return:
            `bool`, state of exist file
        """

        return delete_file(bucket_name=USER_FILE_BUCKET, remote_file_path=self._k.kPath)

    def query_file_to_memory(self) -> Optional[BaseHTTPResponse]:
        """
        download file with _k attribute `kPath` in s3

        :return:
            `BaseHTTPResponse`, byteio of file
        """
        self.file_buffer = download_file_to_memory(
            bucket_name=USER_FILE_BUCKET,
            remote_file_path=self._k.kPath
        )
        return self.file_buffer

    async def to_chunks(self) -> Tuple[Optional[List[Document]], Optional[List[Document]]]:
        """
        To generate parent document

        :return:
            `Tuple[List[Document], List[Document]]`
        """
        parentDocs, childDocs = await to_generate_parent_docs(
            int(self._k.ktype),
            self._k.kPath,
            kbid=self._k.kbid,
            kid=self._k.kid,
            **self._k.kconfig,
            buffer=self.file_buffer
        )
        return parentDocs, childDocs

    async def query_vector(self, type: str = "all") -> List[Dict]:
        """
        Async function to query document y expr

        :param type: query type of docs, default is "all" means parent and docs, support `all`、 `parent`、`child`

        :return:
            `List[Dict]`, docs
        """

        if type == "all":
            expr = f"kid == '{self._k.kid}'"
        elif type == "parent":
            expr = f"child_id == '-1' && kid == '{self._k.kid}' && kbid == '{self._k.kbid}'",
        else:
            expr = f"child_id != '-1' && kid == '{self._k.kid}' && kbid == '{self._k.kbid}'",

        vitems = await a_kbqa_expr_query(
            mconn=self.mconn,
            expr=expr,
            partition_name=self._k.uid,
            output_fields_list=["pk", "kid", "sequence"]
        )
        self.vectors = vitems
        return vitems

    async def _delete_v_chunk(self) -> bool:
        """
        Async function to delete document by parent_id

        :return:
            `bool`, delete all vector about doc
        """
        vitems = await self.query_vector()
        pks = [vitem.get("pk") for vitem in vitems if vitem.get("kid") == self._k.kid]
        deleted = await a_kbqa_delete(self.mconn, pks, self._k.uid)
        self.vectors = None
        return deleted

    async def split_chunk(
        self,
        uid: str = None,
        filename: str = None,
        ktype: str = None,
        kconfig: dict = None,
        zone_type: str = "permanent"
    ) -> Optional[List[Document]]:
        """
        split file content into chunks with type and kconfig

        :param uid: need when zone_type is `temp`
        :param filename: need when zone_type is `temp`
        :param ktype: need when zone_type is `temp`, Only support [1,5]
        :param kconfig: need when zone_type is `temp`, Only support [1,5]
        :param zone_type: default permanent, `temp` is temporary zone, `permanent` is permanent zone

        :return:
            Optional[List[Document]]
        """

        # When zone_type is `permanent`, can use self._k params
        # otherwise, only can transport params when chunk temporary file
        if zone_type == "permanent":
            if not self._k: return None
            file_path = get_fs_path(self._k.uid, self._k.kbid, KBQA_STORAGE_PATH, self._k.kName)
            chunks = await to_chunks(self._k.ktype, file_path, **self._k.kconfig, buffer=self.file_buffer)
        else:
            if not (uid and filename and ktype): return None
            file_path = get_fs_path(uid, KBQA_STORAGE_TMP_PATH, filename)
            chunks = await to_chunks(ktype, file_path, **kconfig, buffer=self.file_buffer)

        return chunks

    def format(self) -> Optional[Dict]:
        """
         return with formatted type of self._cb

         :return:
             `Dict`
         """

        return self._k.to_dict()

    async def query_content_by_page(self, mode="common") -> List[Document]:
        """
        return file content by ocr

        :param mode: support `ocr` or `common`(parse by pypdf) in pdf or word type

        :return:
            `List`, [Document(page_content="", metadata={"page_num": 1})]
        """
        if self.contents: return self.contents
        if not self.file_buffer: self.query_file_to_memory()

        suffix = self.get_suffix()
        # ocr support type judgement
        if suffix not in ENTITY_SUPPORT_TYPES:
            pdocs, cdocs = self.to_chunks()
            result = pdocs + cdocs
        else:
            # extract data buffer
            if suffix == "docx":
                data = docx_2_pdf(self.file_buffer)
            else:
                data = self.file_buffer.data

            # use fully ocr mode
            if mode == "ocr":
                task_id = umi_file_upload(data)
                result = await umi_task_result(task_id)
                umi_file_delete(task_id)

            # use image ocr mode
            elif mode == "common":
                # Firstly, get text content by pypdf
                result = read_content_from(
                    suffix="pdf",
                    buffer=data,
                    mode="paged",
                    extract_images=True
                )

                # Secondly, append image content by ocr to origin text in current page
                for ind, document in enumerate(result):
                    if not document.metadata.get("images"): continue
                    # Use ocr to recognize all images and add them to the original text
                    for image in document.metadata.get("images"):
                        text = umi_image_result(image)
                        if not text: continue
                        result[ind].page_content += text

                pdocs, cdocs = to_generate_parent_docs_by_docs(
                    result,
                    kbid=self._k.kbid,
                    kid=self._k.kid,
                    **self._k.kconfig,
                )
                result = pdocs + cdocs

            else:
                raise NotImplemented

        self.contents = result
        return result







