from abc import ABC, abstractmethod
from typing import List, Dict

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.runnables.sync import run_in_executor


class EmbeddingsReranker(ABC):
    """Interface for embedding reranker models."""

    @abstractmethod
    def embed_documents(self, query: str, docs: List[Document], k: int) -> Dict:
        """Embed search docs."""

    @abstractmethod
    def embed_query(self, query: str, texts: List[str], k: int) -> Dict:
        """Embed query text."""

    async def aembed_documents(self, query: str, docs: List[Document], k: int) -> Dict:
        """Asynchronous Embed search docs."""
        return await run_in_executor(None, self.embed_documents, query, docs, k)

    async def aembed_query(self, query: str, texts: List[str], k: int) -> Dict:
        """Asynchronous Embed query text."""
        return await run_in_executor(None, self.embed_query, query, texts, k)


