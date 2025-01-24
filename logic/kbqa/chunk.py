import os
from typing import Tuple

from urllib3 import BaseHTTPResponse

from logic.kbqa.core.load_and_split import *
from service.ragfusion.loaders.word import WordDocumentLoader
from util.op_thirdparty.kbqa_vector import *
from util.validate import generate_uid
from util.op_thirdparty.fs_minio import download_file_to_memory
from service.ragfusion.core.document.document import Document
from service.ragfusion.splitter.parent import ParentDocumentSplitter
from service.ragfusion.splitter.character import RecursiveCharacterTextSplitter


USER_FILE_BUCKET = os.environ["USER_FILE_BUCKET"]


def read_content_from(
        suffix: str,
        buffer: Union[BaseHTTPResponse, bytes],
        mode: str = "single",
        extract_images: bool = False
) -> List[Document]:
    """read data from buffer from specify suffix

    :param suffix: file path in fs
    :param buffer: file buffer from fs
    :param mode: support `single`、`paged`、`elements`
        - `single`: Only return one Document object, which contains full text
        - `paged`: Return text by page, and can extract images in the metadata
    :param extract_images: extract images in the metadata

    :return:
      `List[Document]`
    """
    try:
        if suffix == "txt" or suffix == "md":
            content = [Document(page_content=buffer.read().decode('utf-8'), metadata={})]

        elif suffix == "pdf":
            from service.ragfusion.loaders.pdf import PyPDFLoader
            buffer = BytesIO(buffer.read()) if isinstance(buffer, BaseHTTPResponse) else BytesIO(buffer)
            loader = PyPDFLoader(
                file_or_buffer=buffer,
                mode=mode,
                strategy="fast",
                extract_img_flag=extract_images
            )
            content = loader.load()

        elif suffix == "docx":
            loader = WordDocumentLoader(BytesIO(buffer.read()))
            content = loader.load()

        else:
            return list()

        return content

    except Exception as e:
        raise RuntimeError(f"Error parse `{suffix}`") from e


@a_retry
async def to_chunks(
        typ: Optional[int],
        file_path: Optional[str],
        split_headers_type: Optional[int] = 0,
        chunk_size: Optional[int] = 1000,
        chunk_overlap: Optional[int] = 100,
        delimiter: Optional[str] = ",",
        buffer: Union[BaseHTTPResponse, BytesIO] = None,
        **kwargs
) -> Optional[List[Document]]:
    """
    To chunk the file by type

    :param file_path: File wait for load and split
    :param typ: QA method e.g.  1 - Character split ; 2 - Traditional title split； 3 - Self-defined split title; 4 - Table QA split; 5 - Commodity QA
    :param chunk_size: chunk size
    :param chunk_overlap: chunk overlap
    :param delimiter: delimiter
    :param split_headers_type: self-defined split with choose type
    :param buffer: file's buffer

    :return: List[Document]
    """
    chunks: Optional[List[Document]] = None
    suffix = os.path.splitext(file_path)[1][1:]
    if not buffer:
        buffer = download_file_to_memory(USER_FILE_BUCKET, file_path)

    # Character split
    if typ == 1:
        docs = read_content_from(suffix, buffer)
        if suffix == "txt":
            chunks = txt_load_and_split(docs, chunk_size, chunk_overlap)
        elif suffix == "md":
            chunks = md_load_and_split(docs, chunk_size, chunk_overlap)
        elif suffix == "docx":
            chunks = await a_word_load_and_split(docs, chunk_size, chunk_overlap)
        elif suffix == "pdf":
            chunks = await a_pdf_load_and_split(docs, chunk_size, chunk_overlap)

    # Traditional title split
    if typ == 2:
        if suffix == "md":
            docs = read_content_from(suffix, buffer)
            chunks = md_load_and_split_header(docs)
        elif suffix == "docx":
            io_buffer = BytesIO(buffer.read())
            chunks = word_load_and_split_header(io_buffer)

    # Self-defined split title
    if typ == 3:
        docs = read_content_from(suffix, buffer)
        chunks = txt_load_and_split_header(docs, split_headers_type)

    # Table QA split
    if typ == 4:
        if suffix == "csv":
            str_buffer = StringIO(BytesIO(buffer.read()).getvalue().decode('utf-8'))
            chunks = await at_csv_loader(str_buffer, delimiter)
        elif suffix == "xlsx":
            io_buffer = BytesIO(buffer.read())
            chunks = await at_xlsx_loader(io_buffer)

    return chunks


@a_retry
async def to_generate_parent_docs(
        typ: Optional[int],
        file_path: Optional[str],
        kbid: Optional[str],
        kid: Optional[str],
        split_headers_type: Optional[int] = 0,
        chunk_size: Optional[int] = 1000,
        chunk_overlap: Optional[int] = 100,
        delimiter: Optional[str] = ",",
        buffer: Union[BaseHTTPResponse, BytesIO] = None,
) -> Tuple[Optional[List[Document]], Optional[List[Document]]]:
    """
    To generate parent document

    :param file_path: File wait for load and split
    :param typ: QA method e.g.  1 - character split ; 2 - title split； 3 - Table split; 4 - self-defined separators
    :param kbid: knowledge base id
    :param kid: knowledge id
    :param chunk_size: chunk size
    :param chunk_overlap: chunk overlap
    :param delimiter: delimiter for csv
    :param split_headers_type: to decide split type in self-defined header
    :param buffer: file's buffer

    :return:
    """
    try:
        assert chunk_size > chunk_overlap, f"chunk_size：{chunk_size} must more over chunk_overlap: {chunk_overlap}"

        chunks = await to_chunks(
            typ=int(typ),
            file_path=file_path,
            split_headers_type=split_headers_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            delimiter=delimiter,
            buffer=buffer
        )

        # Generate metadata title
        for d in chunks:
            title_key = [v for k, v in d.metadata.items() if "Head" in k]
            if not title_key: continue
            title = " - ".join(title_key) if len(title_key) > 1 else title_key[0] if d.metadata and title_key else "摘要"
            d.page_content = f"Current paragraph title is：{title} \n\n" + d.page_content

        _ = [chunk.metadata.update({"sequence": ind + 1, "kbid": kbid, "kid": kid, "child_id": "-1"}) for ind, chunk in enumerate(chunks)]
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size // 2, chunk_overlap=0, add_start_index=True)
        parent_splitter = ParentDocumentSplitter(child_splitter=child_splitter)
        parent_document, child_document = parent_splitter.split_documents(chunks, ids_generator=generate_uid)

        return parent_document, child_document

    except Exception as e:
        return None, None


@retry
def to_generate_parent_docs_by_docs(
        parent_document: List[Document],
        kbid: Optional[str],
        kid: Optional[str],
        chunk_size: Optional[int] = 1000,
        chunk_overlap: Optional[int] = 100,
        **kwargs
) -> Tuple[Optional[List[Document]], Optional[List[Document]]]:
    """
    To generate parent document

    :param parent_document: list of parent document
    :param kbid: knowledge base id
    :param kid: knowledge id
    :param chunk_size: chunk size
    :param chunk_overlap: chunk overlap

    :return:
    """
    try:
        assert chunk_size > chunk_overlap, f"chunk_size：{chunk_size} must more over chunk_overlap: {chunk_overlap}"

        _ = [chunk.metadata.update({"sequence": ind + 1, "kbid": kbid, "kid": kid, "child_id": "-1"}) for ind, chunk in enumerate(parent_document)]
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size // 2, chunk_overlap=0, add_start_index=True)
        parent_splitter = ParentDocumentSplitter(child_splitter=child_splitter)
        parent_document, child_document = parent_splitter.split_documents(parent_document, ids_generator=generate_uid)

        return parent_document, child_document

    except Exception as e:
        print(e)
        return None, None



