"""
The open source commercial Chinese and English semantic vector model BGE (BAAI General Embedding)
surpasses all similar models in the community in terms of both Chinese and English semantic retrieval accuracy
and overall semantic representation ability, such as OpenAI's text embedding 002. In addition,
BGE maintains the minimum vector dimension in models of the same parameter level, resulting in lower usage costs.

FlagEmbedding: https://github.com/FlagOpen/FlagEmbedding
BGE model link: https://huggingface.co/BAAI/
BGE Code Warehouse: https://github.com/FlagOpen/FlagEmbedding
C-MTEB evaluation benchmark link: https://github.com/FlagOpen/FlagEmbedding/tree/master/benchmark
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

from service.ragfusion.core.embeddings import Embeddings

# FIX: Serialize file replace direct write
TOKEN: str = "b8d1e618e3e973b4d7b67fe3467ef43c"
BGE_URL: str = "http://116.204.124.212:32222/api/model/bge_call_service/emb_query"


def _create_retry_decorator(embeddings: BGEEmbedding) -> Callable[[Any], Any]:
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


def embed_with_retry(embeddings: BGEEmbedding, text: Optional[Union[str, List[str]]]) -> Union[List[str], List[List[str]]]:
    """Use tenacity to retry the embedding call."""
    retry_decorator = _create_retry_decorator(embeddings)

    @retry_decorator
    def _embed_with_retry(texts: Optional[Union[str, List[str]]]) -> Any:
        try:
            if isinstance(texts, str):
                texts = [texts]

            texts_vector = list()
            for group_text in [texts[i:i + 100] for i in range(0, len(texts), 100)]:
                response = requests.post(
                    url=BGE_URL,
                    headers={
                        "Content-Type": "application/json",
                        "token": embeddings.token
                    },
                    data=json.dumps({"query": group_text}),
                )
                if response.status_code == 200:
                    texts_vector.extend(json.loads(response.content)["emb"])
                elif response.status_code in [400, 401]:
                    # Unreachable Code
                    raise ValueError(f"HTTP error occurred: status_code: {response.status_code} \n ")
                else:
                    raise HTTPError(
                        f"HTTP error occurred: status_code: {response.status_code} \n "
                    )
            return texts_vector
        except Exception as e:
            # Log the exception or handle it as needed
            raise ValueError(f"Error occurred: {str(e)}")

    return _embed_with_retry(text)


# NOTE!! Without Public URL to use, just build yourself
class BGEEmbedding(Embeddings, BaseModel):

    """
    Using BGE model to embed text.

    Exeample Code:

        from embeddings import BGETextEmbedding
        data = {
            "token": ""
            "max_retries": 5
        }
        emb = BGEEmbedding(**data)
        vec = emb.embed_query("ragfusion")
    """

    """Initial header in the embedding"""
    token: Optional[str] = TOKEN
    """Set max retry nums, default 2"""
    max_retries: Optional[int] = 2

    def embed_query(self, text: str) -> List[float]:
        """
        Multi text callable method

        Args:
            texts: The texts to embed.

        Returns:
            Embedding for the texts.

        """
        vectors = embed_with_retry(self, text)
        return vectors[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Single text callable method

        Args:
            texts: The texts to embed.

        Returns:
            Embedding for the text.
        """
        # return [embed_with_retry(self, text) for text in texts]
        return embed_with_retry(self, texts)









