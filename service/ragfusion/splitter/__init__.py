"""**Text Splitters** are classes for splitting text.


**Class hierarchy:**

.. code-block::

    BaseDocumentTransformer --> TextSplitter --> <name>TextSplitter  # Example: CharacterTextSplitter
                                                 RecursiveCharacterTextSplitter -->  <name>TextSplitter

Note: **MarkdownHeaderTextSplitter** and **HTMLHeaderTextSplitter do not derive from TextSplitter.


**Main helpers:**

.. code-block::

    Document, Tokenizer, Language, LineType, HeaderType

"""  # noqa: E501

import importlib
from typing import Any

_module_lookup = {
    "TokenTextSplitter": "service.ragfusion.splitter.base",
    "TextSplitter": "service.ragfusion.splitter.base",
    "Tokenizer": "service.ragfusion.splitter.base",
    "Language": "service.ragfusion.splitter.base",
    "split_text_on_tokens": "service.ragfusion.splitter.base",
    "MarkdownTextSplitter": "service.ragfusion.splitter.character",
    "CharacterTextSplitter": "service.ragfusion.splitter.character",
    "RecursiveCharacterTextSplitter": "service.ragfusion.splitter.character",
    "MarkdownHeaderTextSplitter": "service.ragfusion.splitter.header",
    "WordHeaderTextSplitter": "service.ragfusion.splitter.header",
    "TextHeaderSplitter": "service.ragfusion.splitter.header",
    "ParentDocumentSplitter": "service.ragfusion.splitter.parent",
    "NLTKTextSplitter": "service.ragfusion.splitter.nltk",
}


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = list(_module_lookup.keys())