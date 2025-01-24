from abc import ABC
from typing import List, Any, Literal, Optional, TypedDict, Dict

from typing_extensions import NotRequired


class Serializable(ABC):
    """Serializable document object base class."""

    def __init__(self, page_content: str, metadata: dict, **kwargs: Any) -> None:
        self._rs_metadata = metadata
        self._rs_page_content = page_content

    @classmethod
    def is_rs_serializable(cls) -> bool:
        """Is this class serializable?"""
        return False

    @classmethod
    def get_rs_namespace(cls) -> List[str]:
        """Get the namespace of the ragfusion object.

        For example, if the class is `ragfusion.core.serializable.Serializable`, then the
        namespace is ["ragfusion", "core", "documents"]
        """
        return cls.__module__.split(".")

    def to_json(self):
        """transfer this object to json"""
        pass

    def __str__(self):
        if self.is_rs_serializable():
            return f"{self.__class__.__name__}(page_content={self._rs_page_content}, metadata={self._rs_metadata})"

        import warnings
        warnings.warn(f"Cant't serialize this document")
        return f'<{self.__class__.__name__} object at {hex(id(self))}>'



class BaseSerialized(TypedDict):
    """Base class for serialized objects."""

    lc: int
    id: List[str]
    name: NotRequired[str]
    graph: NotRequired[Dict[str, Any]]


class SerializedNotImplemented(BaseSerialized):
    """Serialized not implemented."""

    type: Literal["not_implemented"]
    repr: Optional[str]


def to_json_not_implemented(obj: object) -> SerializedNotImplemented:
    """Serialize a "not implemented" object.

    Args:
        obj: object to serialize

    Returns:
        SerializedNotImplemented
    """
    _id: List[str] = []
    try:
        if hasattr(obj, "__name__"):
            _id = [*obj.__module__.split("."), obj.__name__]
        elif hasattr(obj, "__class__"):
            _id = [*obj.__class__.__module__.split("."), obj.__class__.__name__]
    except Exception:
        pass

    result: SerializedNotImplemented = {
        "lc": 1,
        "type": "not_implemented",
        "id": _id,
        "repr": None,
    }
    try:
        result["repr"] = repr(obj)
    except Exception:
        pass
    return result

