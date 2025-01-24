"""Abstract interface for document loader implementations."""
from __future__ import annotations

from abc import ABC
from typing import Iterator, List, AsyncIterator

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.runnables.sync import run_in_executor


class BaseLoader(ABC):
    """Interface for Document Loader.

    Implementations should implement the lazy-loading method using generators
    to avoid loading all Documents into memory at once.

    `load` is provided just for user convenience and should not be overridden.
    """

    # Sub-classes should not implement this method directly. Instead, they
    # should implement the lazy load method.
    def load(self) -> List[Document]:
        """Load data into Document objects."""
        return list(self.lazy_load())

    async def aload(self) -> List[Document]:
        """Load data into Document objects."""
        return [document async for document in self.alazy_load()]


    # Attention: This method will be upgraded into an abstractmethod once it's
    #            implemented in all the existing subclasses.
    def lazy_load(self) -> Iterator[Document]:
        """A lazy loader for Documents."""
        if type(self).load != BaseLoader.load:
            return iter(self.load())
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement lazy_load()"
        )

    async def alazy_load(self) -> AsyncIterator[Document]:
        """A lazy loader for Documents."""
        iterator = await run_in_executor(None, self.lazy_load)
        done = object()
        while True:
            doc = await run_in_executor(None, next, iterator, done)  # type: ignore[call-arg, arg-type]
            if doc is done:
                break
            yield doc  # type: ignore[misc]
