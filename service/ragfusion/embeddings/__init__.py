"""**Document Embedding**  are classes to embed Documents.

**Document Embedding** are used to embed a lot of Documents to vector.

"""
import importlib
from typing import Any

_module_lookup = {
    "BGETextEmbedding": "embeddings.OwnBGE",
}


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = list(_module_lookup.keys())
