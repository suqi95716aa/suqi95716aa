from logic.kbqa.core.intent import generate_intent
from util.op_thirdparty.kbqa_vector import *
from util.op_thirdparty.kbqa_db import *
from models.llm import *
from service.ragfusion.core.document.document import Document
from service.ragfusion.embeddings.bge_rerank import BGERankerEmbedding
from service.ragfusion.retrievers.remark_bm25 import BM25Retriever


async def to_generate_intent(query: str, llm: Union[Spark, DeepSeekCode, DeepSeekChat] = None) -> int:
    """
    Intent to judge the query belongs to

    id of intent type:
    1. Single jump Q&A
    2. Multi jump Q&A
    3. Paragraph Q&A

    :params llm：llm to chat
    :params question：user's query

    :return: Sequence of intent id
    """
    llm = llm or deepseek_chat
    intent_ids: int = await generate_intent(llm, query)
    return intent_ids


async def text_similarity_search_with_score(
        mconn: Milvus,
        kids: Optional[List[str]],
        query: Optional[str],
        k: Optional[int] = 4,
        param: Optional[dict] = None,
        timeout: Optional[float] = None,
        SimilarityThreshold: Optional[Union[float, int]] = 0,
        **kwargs: Any,
) -> List[Document]:
    """
    Async function to search parent similar docs with similarity algorithm.

    :param mconn: Milvus connection
    :param kid: knowledge id
    :param query: The text to search.
    :param k: How many results to return. Defaults to 4.
    :param param: The search params for the index type.
        Defaults to None.
    :param timeout: How long to wait before timeout error.
        Defaults to None.
    :param kwargs: Collection.search() keyword arguments.
    :param SimilarityThreshold: The minimum similarity threshold for retrieving and recalling documents.

    Returns:
        Optional[Tuple[Document, score]]: Document results for search.
    """

    # First find the parent ids of those relative child docs
    child_docs = await a_kbqa_similarity_search_with_score(
        mconn=mconn,
        query=query,
        k=k,
        param=param,
        expr=f"kid in {kids} && child_id != '-1'",
        timeout=timeout,
        **kwargs
    )
    parent_ids = list(set([doc_obj[0].metadata["parent_id"] for doc_obj in child_docs]))
    # Then find the parent docs
    parent_docs = await a_kbqa_similarity_search_with_score(
        mconn=mconn,
        query=query,
        k=k,
        param=param,
        expr=f"kid in {kids} && child_id == '-1' && parent_id in {parent_ids}",
        timeout=timeout,
        **kwargs
    )
    filter_docs = [
        Document(page_content=doc.page_content, metadata={**doc.metadata, "score": sim})
        for doc, sim in sorted(parent_docs, key=lambda x: x[1], reverse=True)
        if sim >= SimilarityThreshold
    ]
    return filter_docs


async def entity_similarity_search_with_score(
        mconn: Milvus,
        kids: Optional[List[str]],
        query: Optional[str],
        k: Optional[int] = 4,
        param: Optional[dict] = None,
        timeout: Optional[float] = None,
        SimilarityThreshold: Optional[Union[float, int]] = 0,
        **kwargs: Any,
) -> List[Document]:
    """
    Async function to search parent similar docs with similarity algorithm.

    :param mconn: Milvus connection
    :param kid: knowledge id
    :param query: The text to search.
    :param k: How many results to return. Defaults to 4.
    :param param: The search params for the index type.
        Defaults to None.
    :param timeout: How long to wait before timeout error.
        Defaults to None.
    :param kwargs: Collection.search() keyword arguments.
    :param SimilarityThreshold: The minimum similarity threshold for retrieving and recalling documents.

    Returns:
        Optional[Tuple[Document, score]]: Document results for search.
    """

    # First find the parent ids of those relative child docs
    docs = await a_kbqa_similarity_search_with_score(
        mconn=mconn,
        query=query,
        k=k,
        param=param,
        expr=f"kid in {kids}",
        timeout=timeout,
        **kwargs
    )
    docs = [
        Document(page_content=doc.page_content, metadata={**doc.metadata, "score": sim})
        for doc, sim in sorted(docs, key=lambda x: x[1], reverse=True)
        if sim >= SimilarityThreshold
    ]
    return docs


async def bm25_search(
        mconn: Milvus,
        kids: Optional[List[str]],
        query: str,
        k: Optional[int] = 4,
        threshold: float = 0,
        **kwargs: Any,
) -> Optional[List[Document]]:
    """
    Async function to search parent similar docs with okapi bm25.

    :param mconn: Milvus connection
    :param kids: knowledge ids
    :param k: How many results to return. Defaults to 4.
    :param query: The text to search. Defaults Not None.
    :param threshold: if score less than threshold, then drop away. Defaults to 0
    :param kwargs: Collection.search() keyword arguments.

    Returns:
        List[Document]: Document results for search.
    """
    text_maps = await a_kbqa_expr_query(
        mconn=mconn,
        expr=f"kid in {kids} && child_id == '-1'",
        output_fields_list=["text", "parent_id"]
    )
    docs = [
        Document(page_content=text_map.get("text"), metadata={k: v for k, v in text_map.items() if k != "text"})
        for text_map in text_maps
    ]
    if not docs: return list()

    retriever = BM25Retriever(docs)
    relative_docs_with_score = await retriever.aget_relevant_documents(query=query, topK=k)
    if threshold:
        relative_docs_with_score = [doc for doc in relative_docs_with_score if doc.metadata["score"] >= threshold]

    return relative_docs_with_score


async def bge_reranker_with_score(query: str, docs: List[Document], k: int) -> List[Document]:
    """
    BGE rerank method, order by score descending.

    :param query: query to rerank(base side).
    :param docs: docs for reranking.
    :param k: return top k .

    Returns:
        top k of texts mostly close query in two stage rerank.
    """
    reranker = BGERankerEmbedding()
    rerank_res = await reranker.aembed_documents(query=query, docs=docs, k=k)
    return [Document(page_content=k, metadata={"score": v}) for k, v in rerank_res.items()]


async def similarity_search_with_pre_next():
    raise NotImplemented
