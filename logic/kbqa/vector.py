from util.op_thirdparty.kbqa_vector import *
from models.milvus.connect import *
from service.ragfusion.core.document.document import Document


# async def to_vector_entity(
#         mconn: Milvus,
#         docs: List[Document],
#         partition_name: str
# ) -> Optional[List[str]]:
#     """
#     To vector entity store
#
#     :param mconn: Milvus connection
#     :param docs: aggregate parent doc and child doc
#     :param partition_name: partition name
#
#     :return: primary key list
#     """
#     # if not exist collection then create
#     if not kbqa_collection_exist(mconn):
#         kbqa_collection_create(
#             mconn,
#             texts=[doc.page_content for doc in docs[0:1]],
#             metadatas=[{
#                 "parent_id": doc.metadata.get("parent_id"),
#                 "child_id": doc.metadata.get("child_id"),
#                 "sequence": doc.metadata.get("sequence"),
#                 "kbid": doc.metadata.get("kbid"),
#                 "kid": doc.metadata.get("kid")
#             } for doc in docs[0:1]],
#         )
#
#     # if not exist partition then create
#     if not (await a_kbqa_partition_exist(mconn, partition_name)):
#         is_create = await a_kbqa_partition_create(mconn, partition_name)
#         if not is_create: return None
#
#     # insert data
#     pks = await a_kbqa_insert(mconn, docs, partition_name)
#     return pks


async def to_vector_text(
        mconn: Milvus,
        docs: List[Document],
        partition_name: str,
        meta_col_name: List[str] = None,
) -> Optional[List[str]]:
    """
    To vector store

    :param mconn: Milvus connection
    :param docs: aggregate parent doc and child doc
    :param partition_name: partition name
    :param meta_col_name: Specify the fields to be extracted

    :return: primary key list
    """
    # if not exist collection then create
    if not kbqa_collection_exist(mconn):
        page_content = [docs[0].page_content]
        if meta_col_name:
            metadata = [{k: v for k, v in docs[0].metadata.items() if k in meta_col_name}]
        else:
            metadata = [docs[0].metadata]
        kbqa_collection_create(mconn, texts=page_content, metadatas=metadata)

    # if not exist partition then create
    if not (await a_kbqa_partition_exist(mconn, partition_name)):
        is_create = await a_kbqa_partition_create(mconn, partition_name)
        if not is_create: return None

    # insert data
    pks = await a_kbqa_insert(mconn, docs, partition_name)
    return pks


def to_mconn_switch(
        mconn: Milvus,
        docs: List[Document],
        col_name: str,
        meta_col_name: List[str] = None
) -> Optional[List[str]]:
    """
    To vector connection switch

    :param mconn: Milvus connection
    :param docs: aggregate parent doc and child doc
    :param col_name: collection name
    :param meta_col_name: Specify the fields to be extracted

    :return: primary key list
    """
    page_content = [docs[0].page_content]
    if meta_col_name:
        metadata = [{k: v for k, v in docs[0].metadata.items() if k in meta_col_name}]
    else:
        metadata = [docs[0].metadata]

    kbqa_collection_switch(
        mconn=mconn,
        col_name=col_name,
        texts=page_content,
        metadatas=metadata
    )


async def to_vector_restore(
        mconn: Milvus,
        pks: List[int],
        partition_name: str = None
) -> Any:
    """
    To restore(delete) vector

    :param mconn: Milvus connection
    :param pks: primary key will be deleted.
    :param partition_name: primary key in partition.

    Returns:
        MutationResult: contains `delete_count` properties represents how many entities might be deleted.

    """
    return await a_kbqa_delete(mconn, pks, partition_name)

