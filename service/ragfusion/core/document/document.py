from typing import Literal, List, Any

from service.ragfusion.core.serializable.serializable import Serializable


class Document(Serializable):
    """Class for storing a piece of text and associated metadata."""

    page_content: str
    """String text."""
    metadata: dict
    """Arbitrary metadata about the page content (e.g., source, relationships to other
        documents, etc.).
    """
    type: Literal["Document"] = "Document"

    def __init__(self, page_content: str, metadata: dict, **kwargs: Any) -> None:
        """Pass page_content in as positional or named arg."""
        self.metadata = metadata
        self.page_content = page_content
        super().__init__(page_content=page_content, metadata=metadata, **kwargs)

    @classmethod
    def is_rs_serializable(cls) -> bool:
        """Is this class serializable?"""
        return True

    @classmethod
    def get_rs_namespace(cls) -> List[str]:
        """Get the namespace of the ragfusion object."""
        return ["ragfusion", "core", "documents"]

