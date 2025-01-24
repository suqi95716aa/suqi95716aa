import os
from io import BytesIO
from datetime import timedelta
from typing import Optional, List, Any

from minio.error import S3Error
from minio.commonconfig import CopySource
from urllib3 import BaseHTTPResponse

from util.retry import retry
from models.fs.connect import minio_client


@retry
def is_bucket_exists(bucket_name: str) -> bool:
    """
    check exists of the bucket.

    :param bucket_name: bucket's name

    :return
        True if bucket exists
    """
    try:
        return minio_client.bucket_exists(bucket_name=bucket_name)
    except S3Error as e:
        print(f"Error occurred while connect server: {e}")
        return False


@retry
def create_bucket(bucket_name: str) -> bool:
    """
    create the bucket if not exists(error happen while bucket exists)

    :param bucket_name: bucket's name

    :return
        True if bucket created
    """
    try:
        minio_client.make_bucket(bucket_name=bucket_name)
        return True
    except S3Error as e:
        print(f"Error occurred while create bucket: {e}")
        return False


@retry
def delete_bucket(bucket_name: str) -> bool:
    """
    delete the bucket if exists(error happen while bucket not exists)

    :param bucket_name: bucket's name

    :return
        True if bucket deleted, false if error or not exists
    """
    try:
        minio_client.remove_bucket(bucket_name=bucket_name)
        return True
    except S3Error as e:
        print(f"Error occurred while uploading file: {e}")
        return False


@retry
def upload_file(
        bucket_name: str,
        local_file_path: Optional[str],
        remote_file_path: Optional[str]
) -> bool:
    """
    upload file to minio server(the dir will be created if not exists)

    :param bucket_name: bucket's name
    :param local_file_path: local real file path
    :param remote_file_path: the path in minio specify bucket

    :return
        True if bucket upload success, false otherwise
    """
    try:
        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=local_file_path,
            file_path=remote_file_path
        )
        return True
    except S3Error as e:
        print(f"Error occurred while uploading file: {e}")
        return False


@retry
def upload_file_with_stream(
        bucket_name: str,
        remote_file_path: str,
        file_body: BytesIO,
        file_length: Optional[int]
) -> bool:
    """
    upload file of binary stream to minio server(the dir will be created if not exists)

    :param bucket_name: bucket's name
    :param remote_file_path: the path in minio specify bucket
    :param file_body: file body, type bytes
    :param file_length: file body's length

    :return
        True if bucket upload success, false otherwise
    """
    try:

        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=remote_file_path,
            data=file_body, length=file_length
        )
        return True
    except S3Error as e:
        print(f"Error occurred while uploading file: {e}")
        return False


@retry
def download_file_to_local(bucket_name: str, remote_file_path: str, local_file_path: str) -> bool:
    """
    download file to local

    :param bucket_name: bucket's name
    :param remote_file_path: the path in minio specify bucket
    :param local_file_path: local real file path

    :return
        True if download success, false otherwise
    """
    try:
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=remote_file_path,
            file_path=local_file_path
        )
        return True
    except S3Error as e:
        print(f"Error occurred while downloading file: {e}")
        return False


@retry
def download_file_to_memory(bucket_name: str, remote_file_path: str) -> Optional[BaseHTTPResponse]:
    """
    download file to memory

    :param bucket_name: bucket's name
    :param remote_file_path: the path in minio specify bucket

    :return
        class:`urllib3.response.BaseHTTPResponse` object.
    """

    try:
        stream_rsp = minio_client.get_object(bucket_name=bucket_name, object_name=remote_file_path)
        return stream_rsp
    except Exception as e:
        print(f"Error occurred while downloading file: {e}")
        return None


@retry
def delete_file(bucket_name: str, remote_file_path: str) -> bool:
    """
    delete file in minio server

    :param bucket_name: bucket's name
    :param remote_file_path: the path in minio specify bucket

    :return
        True if deleted, false otherwise
    """
    try:
        minio_client.remove_object(bucket_name=bucket_name, object_name=remote_file_path)
        return True
    except S3Error as e:
        print(f"Error occurred while deleting file: {e}")
        return False


@retry
def stat_file(bucket_name: str, remote_file_path: str) -> Any:
    """
    try to read file's metadata to judge whether the file exists

    :param bucket_name: source bucket's name
    :param remote_file_path: file position

    :return
        metadata if file exists, None otherwise
    """
    try:
        metadata = minio_client.stat_object(bucket_name, remote_file_path)
        return metadata
    except S3Error as e:
        return None


@retry
def copy_file(
        source_bucket_name: str,
        source_file_path: str,
        dest_bucket_name: str,
        dest_file_path: str
) -> bool:
    """
    copy file from specify position in bucket

    :param source_bucket_name: source bucket's name
    :param source_file_path: copied of file
    :param dest_bucket_name: destination bucket's name
    :param dest_file_path: destination of file (need to carry bucket name in path)

    :return
        True if copied success, false otherwise
    """
    try:
        minio_client.copy_object(
            bucket_name=dest_bucket_name,
            object_name=dest_file_path,
            source=CopySource(source_bucket_name, source_file_path)
        )
        return True
    except S3Error as e:
        print(f"Could not copy file: {e}")
        return False


@retry
def move_file(
        source_bucket_name: str,
        source_file_path: str,
        dest_bucket_name: str,
        dest_file_path: str
) -> bool:
    """
    move file from specify position in bucket then delete it

    :param source_bucket_name: source bucket's name
    :param source_file_path: copied of file, like `1111/KBQA/storage_tmp/kbqa.txt`
    :param dest_bucket_name: destination bucket's name
    :param dest_file_path: destination of file (need to carry bucket name in path), like `1111/KBQA/storage/224e350/kbqa_745.txt`

    :return
        True if moved success, false otherwise
    """
    try:
        copied = copy_file(
            source_bucket_name=source_bucket_name,
            source_file_path=source_file_path,
            dest_bucket_name=dest_bucket_name,
            dest_file_path=dest_file_path
        )
        if not copied:
            return False

        deleted = delete_file(source_bucket_name, source_file_path)
        if not deleted:
            delete_file(dest_bucket_name, dest_file_path)
            return False

        return True

    except S3Error as e:
        print(f"Could not copy file: {e}")
        return False


@retry
def presigned_url(
        bucket_name: str,
        remote_file_path,
        expires: timedelta
) -> Optional[str]:
    """
        presigned url

        :param bucket_name: bucket's name
        :param remote_file_path: the path in minio specify bucket
        :param expires[`timedelta`]: expires time of the generated url

        :return
            url if generated, else None
    """
    try:
        presigned_url = minio_client.presigned_get_object(
            bucket_name,
            remote_file_path,
            expires=expires
        )
        return presigned_url
    except S3Error as e:
        print(f"Error occurred while presign: {e}")
        return None
    except Exception as e:
        return None


@retry
def list_directory(
        bucket_name: str,
        remote_path_prefix: str,
        recursive: bool = False
) -> Optional[List[str]]:
    """
    get list of files in the specify dir in minio server

    :param bucket_name: bucket's name
    :param remote_path_prefix: the path's prefix in minio server, like `1111/KBQA/storage_tmp/`
    :param recursive: go recursive to dir of the path

    :return
        `Optional[List[str]]`, list of filenames
    """
    try:
        list_objects = minio_client.list_objects(
            bucket_name=bucket_name,
            prefix=remote_path_prefix,
            recursive=recursive
        )
        return [os.path.basename(item.object_name) for item in list_objects]
    except S3Error as e:
        print(f"Error occurred while deleting file: {e}")
        return list()


@retry
def create_directory(bucket_name: str, remote_path_prefix: str) -> bool:
    """
    create dir in the specify dir in minio server

    :param bucket_name: bucket's name
    :param remote_path_prefix: the path's prefix in minio server

    :return
        True if created, false otherwise
    """
    try:
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=remote_path_prefix,
            data=b"",
            length=0
        )
        print(f"Directory '{remote_path_prefix}' created successfully in '{bucket_name}'.")
        return True
    except S3Error as e:
        print(f"Error occurred while creating directory: {e}")
        return False


if __name__ == "__main__":
    bucket_name = r"user-file-space"

    txt = r"1111/KBQA/storage_tmp/新建文本文档.txt"
    md = r"1111/KBQA/storage_tmp/test.md"
    pdf = r"苏宗琦-19350046077-后端研发.pdf"
    csv = r"2023-09-19.csv"
    xlsx = r"生产报表AI处理表.xlsx"
    word_docx = r"1111/KBQA/storage_tmp/测试word.docx"
    word_doc = r"测试doc.doc"

    # get prefix
    # stat = stat_file("user-file-space", txt)
    # print(dir(stat))
    # print(stat.metadata)
    # print(os.path.basename(stat.object_name))

    # # TXT
    # res = download_file_to_memory(bucket_name, txt)
    # print(res.read().decode('utf-8'))

    # # MD
    # res = download_file_to_memory(bucket_name, md)
    # print(res.read().decode('utf-8'))

    # PDF
    # import pypdf
    # stream_rsp = download_file_to_memory(bucket_name, pdf)
    # pdf_file = BytesIO(stream_rsp.read())
    # reader = pypdf.PdfReader(pdf_file)
    # ret = dict()
    # for ind, page in enumerate(reader.pages):
    #     ret[ind] = page.extract_text()
    # print(ret)

    # # csv
    # response = download_file_to_memory(bucket_name, csv)
    # csv_file = BytesIO(response.read())
    # df = pd.read_csv(csv_file, encoding="utf-8")
    # print(df)

    # excel
    # response = download_file_to_memory(bucket_name, xlsx)
    # excel_file = BytesIO(response.read())
    # df = pd.read_excel(excel_file)
    # print(df)

    # # docx
    from docx import Document
    response = download_file_to_memory(bucket_name, word_docx)
    word_file = BytesIO(response.read())
    document = Document(word_file)
    print(document)
    for para in document.paragraphs:
        print(para.text)

