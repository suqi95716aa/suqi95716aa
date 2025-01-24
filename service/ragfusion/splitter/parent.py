import uuid
from typing import Iterable, List, Optional, Sequence, Union, Callable, Dict, Tuple

from service.ragfusion.core.document.document import Document
from service.ragfusion.splitter import RecursiveCharacterTextSplitter


class ParentDocumentSplitter:
    """From parent documents split their children documents.

        When you split documents with parent and child, you often desires:
        
        1. Correctly split documents with parent and child, and they are connect
        with some way(e.g. id).
        2. You want to have enough small chunk to retrieve then find its parent document.
        The ParentDocumentSplitter uses mapping relationships such as splitting and adding 
        IDs to chunk. 
        Firstly, the document will be chunk through the parent splitter, and then through 
        the child splitter.
        Finally, IDs mapping will be added their pair of parent and child. 
        
        Examples:

            .. code-block:: python

                from splitter import ParentDocumentSplitter
                from splitter import RecursiveCharacterTextSplitter
                from splitter import TextHeaderSplitter
                splitter = TextHeaderSplitter()
                docs = splitter.split_text([content])
        
                parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0, add_start_index=True)
                child_splitter = RecursiveCharacterTextSplitter(chunk_size=500,  chunk_overlap=0, add_start_index=True)
                p_splitter = ParentDocumentSplitter(
                                    child_splitter=child_splitter,
                                    parent_splitter=parent_splitter,
                                )
                p_splitter.split_documents(docs)
        """  # noqa: E501

    def __init__(self,
                 child_splitter: Optional[RecursiveCharacterTextSplitter],
                 child_metadata_fields: Optional[Dict] = None,
                 parent_splitter: Optional[RecursiveCharacterTextSplitter] = None,
                 ):
        self.child_splitter: Optional[RecursiveCharacterTextSplitter] = child_splitter
        """The text splitter to use to create child documents."""

        """The key to use to track the parent id. This will be stored in the
        metadata of child documents."""
        self.parent_splitter: Optional[RecursiveCharacterTextSplitter] = parent_splitter
        """The text splitter to use to create parent documents.
        If none, then the parent documents will be the raw documents passed in."""

        self.child_metadata_fields: Optional[Dict] = child_metadata_fields
        """Metadata fields to leave in child documents. If `None`, leave all parent document 
            metadata.
        """

    def split_documents(self,
        documents: Iterable[Document],
        ids_generator: Callable = None,
        split_only_child: bool = True
    ) -> Tuple[List[Document], List[Document]]:
        """Split children document from parent document.

       :param documents: List of documents to split
       :param ids_generator: Optional list of ids for documents,
       - Callable:
            Callable to generate chunk's id.
       - Default:
            If not provided, random UUIDs will be used as ids.
       :param split_only_child: Only split to child

       :return: Tuple[List[Document], List[Document]] -> parentList, childList
       """
        if not ids_generator:
            ids_generator = uuid.uuid4
        if not split_only_child:
            documents = self.parent_splitter.split_documents(documents)

        child_documents = []
        for parent_doc in documents:
            parent_doc.metadata.update({"parent_id": str(ids_generator())})
            part_child_documents = self.child_splitter.split_documents([parent_doc])
            for per_child_doc in part_child_documents:
                per_child_doc.metadata.update({"child_id": str(ids_generator())})
                child_documents.append(per_child_doc)

        return documents, child_documents














