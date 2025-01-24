import os
from typing import List

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.loader.unstructured import UnstructuredFileLoader


class WordDocumentLoader(UnstructuredFileLoader):
    """Load `Microsoft Word` file using `Unstructured`.

    Works with both .docx and .doc files.
    You can run the loader in one of two modes: "single" and "elements".
    If you use "single" mode, the document will be returned as a single
    ragfusion Document object. If you use "elements" mode, the unstructured
    library will split the document into elements such as Title and NarrativeText.
    You can pass in additional unstructured kwargs after mode to apply
    different unstructured settings.

    Examples
    --------
    from loaders import WordDocumentLoader

    loader = WordDocumentLoader(
        "example.docx", mode="elements", strategy="fast",
    )
    """

    def _get_elements(self) -> List:
        try:
            from docx import Document as d_doc
        except Exception:
            raise Exception("Package docx is not installed or wrong version imported.")

        document = d_doc(self.file_or_buffer)
        content = [Document(metadata={}, page_content="\n\n".join([para.text for para in document.paragraphs]))]
        return content

        # from unstructured.__version__ import __version__ as __unstructured_version__
        # from unstructured.file_utils.filetype import FileType, detect_filetype
        #
        # unstructured_version = tuple(
        #     [int(x) for x in __unstructured_version__.split(".")]
        # )
        # # NOTE(MthwRobinson) - magic will raise an import error if the libmagic
        # # system dependency isn't installed. If it's not installed, we'll just
        # # check the file extension
        # try:
        #     import magic  # noqa: F401
        #     is_doc = detect_filetype(self.file_or_buffer) == FileType.DOC
        # except ImportError:
        #     _, extension = os.path.splitext(str(self.file_or_buffer))
        #     is_doc = extension == ".doc"
        #
        # if is_doc and unstructured_version < (0, 4, 11):
        #     raise ValueError(
        #         f"You are on unstructured version {__unstructured_version__}. "
        #         "Partitioning .doc files is only supported in unstructured>=0.4.11. "
        #         "Please upgrade the unstructured package and try again."
        #     )
        #
        # if is_doc:
        #     from unstructured.partition.doc import partition_doc
        #     return partition_doc(filename=self.file_or_buffer, **self.unstructured_kwargs)
        # else:
        #     from unstructured.partition.docx import partition_docx
        #     return partition_docx(filename=self.file_or_buffer, **self.unstructured_kwargs)



