"""
The bge-reranker-large is a large-scale,
deep learning-based reranking model designed to enhance the precision of textual relevance scoring.
This model is particularly effective in scenarios where the initial ranking is based on simple matching algorithms,
and a more nuanced understanding of the semantic relationships between queries and documents is required.

ModelScope: https://www.modelscope.cn/models/Xorbits/bge-reranker-large/summary
Huggingface: https://huggingface.co/BAAI/bge-reranker-large

"""
from __future__ import annotations

import json
import requests
from typing import Optional, Dict, List, Any, Callable, Union

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from requests.exceptions import HTTPError
from pydantic import BaseModel

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.embeddings import EmbeddingsReranker

# FIX: Serialize file replace direct write
TOKEN: str = "b8d1e618e3e973b4d7b67fe3467ef43c"
BGE_RERANK_URL: str = "http://116.204.124.212:32222/api/model/bge_call_service/bge_base_rerank"


def _create_retry_decorator(embeddings: BGERankerEmbedding) -> Callable[[Any], Any]:
    multiplier = 1
    min_seconds = 1
    max_seconds = 4
    # Wait 2^x * 1 second between each retry starting with
    # 1 seconds, then up to 4 seconds, then 4 seconds afterwards
    return retry(
        reraise=True,
        stop=stop_after_attempt(embeddings.max_retries),
        wait=wait_exponential(multiplier, min=min_seconds, max=max_seconds),
        retry=(retry_if_exception_type(HTTPError))
    )


def embed_with_retry(embeddings: BGERankerEmbedding, query: str, texts: List[str], k: int) -> Dict:
    """Use tenacity to retry the bge reranker embedding call."""
    retry_decorator = _create_retry_decorator(embeddings)

    @retry_decorator
    def _embed_with_retry(query: str, texts: List[str], k: int) -> Any:
        try:
            response = requests.post(
                url=BGE_RERANK_URL,
                headers={
                    "Content-Type": "application/json",
                    "token": embeddings.token
                },
                data=json.dumps({"query": query, "passages": texts, "top_k": k}),
            )
            if response.status_code == 200:
                return json.loads(response.content)["score_rank_list"]
            elif response.status_code in [400, 401]:
                # Unreachable Code
                raise ValueError(f"HTTP error occurred: status_code: {response.status_code} \n ")
            else:
                raise HTTPError(
                    f"HTTP error occurred: status_code: {response.status_code} \n "
                )
        except Exception as e:
            # Log the exception or handle it as needed
            raise ValueError(f"Error happen: {str(e)}")

    return _embed_with_retry(query, texts, k)


# NOTE!! Without Public URL to use, just build yourself
class BGERankerEmbedding(EmbeddingsReranker, BaseModel):

    """
    Using BGE reranker model to rerank text in tow-stage rank.

    Exeample Code:

        from embeddings import BGETextEmbedding
        data = {
            "token": ""
            "max_retries": 5
        }
        emb = BGERankerEmbedding(**data)
        vec = emb.embed_documents(
        query="get mostly close passages",
        texts=["passages_1", "passages_2", "passages_3"],
        k=2
        )
    """

    """Initial header in the embedding"""
    token: Optional[str] = TOKEN
    """Set max retry nums, default 2"""
    max_retries: Optional[int] = 2

    def embed_query(self, query: str, texts: List[str], k: int) -> Dict:
        """
        Multi text to rerank

        Args:
            query: query to rerank(base side).
            texts: texts for reranking.
            k: return top k .

        Returns:
            top k of texts mostly close query.

        """
        return embed_with_retry(self, query, texts, k)

    def embed_documents(self, query: str, docs: List[Document], k: int) -> Dict:
        """
        Multi `Document` to rerank

        Args:
            query: query to rerank(base side).
            docs: docs for reranking.
            k: return top k .

        Returns:
            top k of texts mostly close query.
        """
        return embed_with_retry(self, query, [doc.page_content for doc in docs], k)








