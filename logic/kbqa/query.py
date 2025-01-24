from logic.kbqa.core.recall import *
from logic.kbqa.core.toanwser import generate_answer
from util.op_common.tomartdown import transfer_answer_markdown


async def query_single_jump(
        session,
        uid: str,
        query: str,
        kbids: Optional[List],
        relevant_hits: Optional[int] = 4,
        similarity_threshold: Optional[Union[float, int]] = 0,
) -> Tuple[Optional[str], Optional[List[Document]]]:

    # We first judge relative docs
    if not kbids:
        kid_objects_tuple = await kbqa_kid_user_KnowledgeInfo(session, uid)
    else:
        kid_objects_tuple = await kbqa_in_kbids_KnowledgeInfo(session, uid, kbids)
    kids = [doc_tuple[0].kid for doc_tuple in kid_objects_tuple]
    if not kids: return None, None

    # One-stage retriever
    ONE_STAGE_HINTS = 4
    # Search the most similar docs with vector
    vector_search_res = await text_similarity_search_with_score(
        kids=kids,
        query=query,
        k=ONE_STAGE_HINTS,
        param=search_params,
        SimilarityThreshold=float(similarity_threshold)
    )
    # Search the most similar docs by bm25
    bm25_res = await bm25_search(
        kids=kids,
        partition_name=uid,
        query=query,
        k=ONE_STAGE_HINTS
    )

    # Two-stage reranker
    # 1 - deduplication
    deduplication_dict = dict()
    for doc in vector_search_res:
        pk = doc.metadata.get("pk")
        if pk not in deduplication_dict.keys() or \
                deduplication_dict[pk].metadata.get("score") < doc.metadata.get("score"):
            deduplication_dict[pk] = doc
    if not deduplication_dict: return None, None

    # 2 - rerank
    rerank_res = await bge_reranker_with_score(query, list(deduplication_dict.values()), int(relevant_hits))

    # Generate answer
    ans = None
    try:
        ans = await generate_answer(spark, query, rerank_res)
        ans_to_md = ans if ans and len(ans) < 50 else await transfer_answer_markdown(spark, ans)
    except Exception as error:
        ans_to_md = ans if ans else "Your request is in queue, please try again later."
    return ans_to_md, rerank_res




