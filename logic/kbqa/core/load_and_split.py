from typing import List, Union
from io import BytesIO, StringIO

from service.ragfusion.core.document.document import Document


def txt_load_and_split_header(
        docs: List[Document],
        split_headers_type: int
) -> List[Document]:
    """
    Article QA e.g. txt

    Synchronous to load and split `txt` file to documents

    :param docs: list of document
    :param split_headers_type: self-defined split with chose type, e.g. 1 - x.x.x.x；2 - (xx)

    :return: List[Document]
    """
    from service.ragfusion.splitter.header import TextHeaderSplitter
    splitter = TextHeaderSplitter(split_headers_type)
    chunks = splitter.split_text(docs)
    return chunks


def txt_load_and_split(
        docs: List[Document],
        chunk_size: int,
        chunk_overlap: int
) -> List[Document]:
    """
        Common QA e.g. txt

        Asynchronous to load and split `txt` file to documents

        :param docs: list of document
        :param chunk_size: chunk size
        :param chunk_overlap: chunk overlap

        :return: List[Document]
    """
    from service.ragfusion.splitter import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        keep_separator=False
    )
    text_chunks = splitter.split_documents(docs)
    return text_chunks


def md_load_and_split(
        docs: List[Document],
        chunk_size: int,
        chunk_overlap: int,
) -> List[Document]:
    """
        Common QA e.g. markdown

        Asynchronous to load and split `markdown` file to documents

        :param docs: list of document
        :param chunk_size: chunk size
        :param chunk_overlap: chunk overlap

        :return: List[Document]
    """
    from service.ragfusion.splitter import MarkdownTextSplitter

    splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    docs_text = splitter.split_documents(docs)
    return docs_text


def md_load_and_split_header(
    docs: List[Document],
) -> List[Document]:
    """
    Article QA e.g. markdown

    Synchronous to load and split `markdown` file to documents

    :param docs: list of document

    :return: List[Document]
    """
    from service.ragfusion.splitter.header import MarkdownHeaderTextSplitter

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
        combine_content_with_header=True
    )
    chunks = splitter.split_text(docs[0].page_content)
    return chunks


async def a_word_load_and_split(
        docs: List[Document],
        chunk_size: int,
        chunk_overlap: int,
) -> List[Document]:
    """
        Common QA e.g. word

        Asynchronous to load and split `word` file to documents

        :param docs: list of document
        :param chunk_size: chunk size
        :param chunk_overlap: chunk overlap

        :return: List[Document]
    """
    from service.ragfusion.splitter import CharacterTextSplitter

    splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        keep_separator=False
    )
    chunks = splitter.split_documents(docs)
    return chunks


def word_load_and_split_header(file_path: Union[str, BytesIO]) -> List[Document]:
    """
        Article QA e.g. docx
        Synchronous to load and split `docx` file to documents

        :param file_path: Wait for load and split

        :return: List[Document]
    """
    from service.ragfusion.splitter.header import WordHeaderTextSplitter
    splitter = WordHeaderTextSplitter(strip_headers=False)
    chunks = splitter.split_text(file_path)
    return chunks


async def a_pdf_load_and_split(
        docs: List[Document],
        chunk_size: int,
        chunk_overlap: int,
) -> List[Document]:
    """
        Common QA e.g. pdf

        Asynchronous to load and split `pdf` file to documents

        :param docs: Wait for load and split
        :param chunk_size: chunk size
        :param chunk_overlap: chunk overlap

        :return: List[Document]
    """
    from service.ragfusion.splitter.character import CharacterTextSplitter

    splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        keep_separator=False,
    )
    chunks = splitter.split_documents(docs)
    return chunks


async def at_csv_loader(file_path: Union[str, StringIO], delimiter: str) -> List[Document]:
    """
        Common QA e.g. csv

        Asynchronous to load and split `csv` file to documents

        :param file_path: Wait for load and split
        :param delimiter: delimiter
        :return: List[Document]
    """
    from service.ragfusion.loaders import CSVLoader

    loader = CSVLoader(
        file_path=file_path,
        csv_args={
            'delimiter': delimiter,
            'quotechar': '"',
        })
    chunks = await loader.aload()
    return chunks


async def at_xlsx_loader(file_path: Union[str, BytesIO]) -> List[Document]:
    """
        Common QA e.g. xlsx

        Asynchronous to load and split `xlsx` file to documents

        :param file_path: Wait for load and split
        :return: List[Document]
    """
    from service.ragfusion.loaders import ExcelLoader

    loader = ExcelLoader(file_path)
    chunks = await loader.aload()
    return chunks


if __name__ == "__main__":

    # csv
    import csv
    from io import BytesIO, StringIO
    from logic.op_thirdparty.fs_minio import stat_file, download_file_to_memory
    USER_FILE_BUCKET = "user-file-space"
    file_path = "1111/KBQA/storage_tmp/2023-09-19.csv"
    # 假设你有一个CSV数据的字节串
    # csv_data = b"A,B,C\n1,2,3\n4,5,6"
    buffer = download_file_to_memory(USER_FILE_BUCKET, file_path)

    # 创建一个BytesIO对象
    csv_buffer = BytesIO(buffer.read())

    # 使用csv.DictReader读取CSV数据
    reader = csv.DictReader(StringIO(csv_buffer.getvalue().decode('utf-8')))

    # 遍历每一行
    for row in reader:
        print(row)



    # pdf
    # from service.ragfusion.loaders.pdf import PyPDFLoader
    # loader = PyPDFLoader(r"C:\Users\zqsu3\Desktop\2309.07864.pdf", mode="single", strategy="fast")
    # content = loader.load()
    # print(content)

    # word
    # from service.ragfusion.loaders import UnstructuredWordDocumentLoader
    # loader = UnstructuredWordDocumentLoader(r"C:\Users\zqsu3\Desktop\excel表格数据源\测试数据\数据助手测试说明.docx", mode="single", strategy="fast")
    # content = loader.load()
    # print(content)
#     import asyncio
#
#     # chunks = a_md_load_and_split_header(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\系统架构.md")
#     # chunks = a_txt_load_and_split_header(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\新建文本文档.txt")
#     # chunks = a_docx_loader(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\附件10 整体服务方案.docx")
#
#     # pdf
#     # loop = asyncio.get_event_loop()
#     # ret = loop.run_until_complete(ac_pdf_load_and_split(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\test.pdf"))
#
#     # markdown
#     # loop = asyncio.get_event_loop()
#     # ret = loop.run_until_complete(ac_md_load_and_split(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\系统架构.md"))
#     # print(len(ret))
#
#     # word
#     loop = asyncio.get_event_loop()
#     ret = loop.run_until_complete(ac_word_load_and_split(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\福州市长乐区百户村智慧乡村项目-可研暨初设方案v3.5 15.40（20200312）(1)1.docx"))
#     print(len(ret))
#
#     # csv
#     # loop = asyncio.get_event_loop()
#     # ret = loop.run_until_complete(at_csv_loader(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\qa-template.csv"))
#     # print(len(ret))
#
#     # xlsx
#     # loop = asyncio.get_event_loop()
#     # ret = loop.run_until_complete(at_xlsx_loader(r"C:\Users\zqsu3\Desktop\working\aiagent\service\ragfusion\doc\qa-template.xlsx"))
#     # print(len(ret))
#
#     for item in ret:
#         print(len(item.page_content))
#         print(">>>>>>>>>>>>")
