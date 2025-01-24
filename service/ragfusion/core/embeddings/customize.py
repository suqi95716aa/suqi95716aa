import hashlib
from typing import List, Optional

from service.ragfusion.core.embeddings.embeddings import Embeddings

from pydantic import BaseModel


class TestEmbedding(Embeddings, BaseModel):
    """Test class for embedding"""

    # vector dims
    dims: Optional[int]

    def _emb(self, seed: int) -> List[float]:
        """Embed method"""
        import numpy as np

        # set seed for same input and output
        np.random.seed(seed)
        return list(np.random.normal(size=self.dims))

    def _get_seed(self, text: str) -> int:
        """
        Get a seed for the random generator,
        using the hash of the text.
        """
        return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % 10 ** 8

    def to_query_vec(self, texts: List[str]) -> List[List[float]]:
        return [self._emb(seed=self._get_seed(_)) for _ in texts]

    def to_docs_vec(self, text: str) -> List[float]:
        return self._emb(seed=self._get_seed(text))







