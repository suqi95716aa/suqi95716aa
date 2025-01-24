from typing import List, Optional, Any

from pymilvus.orm import utility

from util.retry import retry, a_retry
from models.milvus.connect import *
from service.ragfusion.core.document.document import Document
from service.ragfusion.core.runnables.sync import run_in_executor


@retry
def kbqa_collection_exist(
    mconn: Milvus
) -> bool:
    """
    sync function to check collection exist.

    :param mconn: Milvus connection
    :return:
    """
    if utility.has_collection(mconn.collection_name, using=mconn.alias):
        return True
    return False


@retry
def kbqa_collection_create(
    mconn: Milvus,
    texts: List[str],
    metadatas: Optional[list[dict]] = None,
    partition_names: Optional[list] = None,  # the partition need to load, not create
    replica_number: int = 1,
    timeout: Optional[float] = None,
):

    """
    sync function to create collection.

    :param mconn: Milvus connection
    :param texts:
    :param metadatas:
    :param partition_names:
    :param replica_number:
    :param timeout:
    :return:
    """

    kwargs = {
        "embeddings": mconn.embedding_func.embed_documents(texts),
        "metadatas": metadatas,
        "partition_names": partition_names,
        "replica_number": replica_number,
        "timeout": timeout
    }
    mconn._init(**kwargs)


# 要先切换，col_name和self.col
# 然后按to_vector组织数据结构插入
@retry
def kbqa_collection_switch(
    mconn: Milvus,
    col_name: str,
    texts: List[str],
    metadatas: Optional[list[dict]] = None,
    partition_names: Optional[list] = None,  # the partition need to load, not create
    replica_number: int = 1,
    timeout: Optional[float] = None,
):
    """
    switch collection in conn

    :param mconn:
    :param col_name:
    :return:
    """
    mconn.collection_name = col_name
    kwargs = {
        "embeddings": mconn.embedding_func.embed_documents(texts),
        "metadatas": metadatas,
        "partition_names": partition_names,
        "replica_number": replica_number,
        "timeout": timeout
    }
    mconn._init(**kwargs)



@a_retry
async def a_kbqa_partition_exist(
    mconn: Milvus,
    partition_name: str
) -> bool:
    """
    Async function to check partition exist

    :param mconn: Milvus connection
    :param partition_name: (``List[str]``, optional): A list of partition names to query in. Defaults to None.

    Returns: Bool of exist partition
    """
    return await run_in_executor(None, mconn.col.has_partition, partition_name)


@a_retry
async def a_kbqa_partition_create(
        mconn: Milvus,
        partition_name: str
) -> bool:
    """
    Async function to create partition

    :param mconn: Milvus connection
    :param partition_name: (``List[str]``, optional): A list of partition names to query in. Defaults to None.

    Returns: Bool of success create partition
    """
    return await run_in_executor(None, mconn.col.create_partition, partition_name)


@a_retry
async def a_kbqa_insert(
        mconn: Milvus,
        docs: List[Document],
        partition_name: str,
        meta_col_name: List[str] = None,
) -> List[str]:
    """
    Async function to insert document which is generate with parent-child document relation

    :param mconn: Milvus connection
    :param docs: (``List[Document]``): Docs object need to insert.
    :param partition_name: (``List[str]``): A list of partition names to query in. Defaults to None.
    :param meta_col_name: Specify the fields to be extracted

    """
    # extract content
    page_contents = [doc.page_content for doc in docs]
    if meta_col_name:
        metadatas = [{k: v for doc in docs for k, v in doc.metadata.items() if k in meta_col_name}]
    else:
        metadatas = [doc.metadata for doc in docs]

    return await run_in_executor(
        None,
        mconn.add_texts,
        texts=page_contents,
        metadatas=metadatas,
        partition_name=partition_name,
        # _async=True,
        batch_size=30,
        timeout=12000
    )


@a_retry
async def a_kbqa_delete(
        mconn: Milvus,
        pks: List[int],
        partition_name: str = None
) -> bool:
    """
    Async function to delete document by parent_id

    :param mconn: Milvus connection
    :param pk: list of document id
    :param partition_name: (``List[str]``, optional): A list of partition names to query in. Defaults to None.

    Returns:
        MutationResult: contains `delete_count` properties represents how many entities might be deleted.
    """

    try:
        await run_in_executor(
            None,
            mconn.col.delete,
            expr=f"pk in {pks}",
            partition_name=partition_name
        )
        return True
    except Exception as error:
        print("a_kbqa_delete error：", error)
        return False


@a_retry
async def a_kbqa_expr_query(
        mconn: Milvus,
        expr: str,
        partition_name: str = None,
        output_fields_list: List[str] = None,
        limit: int = None,
        offset: int = None
) -> Any:
    """
    Async function to query document by expr

    :param mconn: Milvus connection
    :param expr: Filtering expression. Defaults to None.
    :param partition_name: (``List[str]``, optional): A list of partition names to query in. Defaults to None.
    :param output_fields_list: output fields list. Defaults to None
    :param limit: Combined with limit to enable pagination
    :param offset: Combined with limit to enable pagination

    Returns:
            List, contains all results
    """
    return await run_in_executor(
        None,
        mconn.col.query,
        expr=expr,
        partition_name=[partition_name] if partition_name else None,
        output_fields=output_fields_list,
        limit=limit,
        offset=offset
    )


@a_retry
async def a_kbqa_similarity_search_with_score(
        mconn: Milvus,
        query: str,
        k: int,
        param: Optional[dict] = None,
        expr: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
) -> List[Document]:
    """
    Async function to search similar docs with score

    :param mconn: Milvus connection
    :param query: The text to search.
    :param k: How many results to return. Defaults to 4.
    :param param: The search params for the index type.
        Defaults to None.
    :param expr: Filtering expression. Defaults to None.
    :param timeout: How long to wait before timeout error.
        Defaults to None.
    :param kwargs: Collection.search() keyword arguments.

    Returns:
        List[Document]: Document results for search.
    """

    return await run_in_executor(
        None,
        mconn.similarity_search_with_score,
        query=query,
        k=k,
        param=param,
        expr=expr,
        timeout=timeout,
        **kwargs
    )



# if __name__ == "__main__":
#     import asyncio
#
#     # asyncio.run(a_kbqa_delete([], "079f209"))
#
#     pks = asyncio.run( a_kbqa_expr_query(
#                 expr="kid == '12420f9'",
#                 partition_name=None,
#                 output_fields_list=["pk"]
#             ))
#     pks = [v for pk in pks for k, v in pk.items()]
#
#     print(pks)
