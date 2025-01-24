import os
import tempfile
from typing import Dict, Union, Optional

from docx2pdf import convert
from urllib3 import BaseHTTPResponse


def params_filter(req, model, **kwargs) -> Dict:
    """从reuqest中选择模型所需要的参数"""
    requiredAttrs = [
        attr for attr in dir(model)
        if not callable(getattr(model, attr)) and
           not attr.startswith("__") and attr != 'class'
    ]
    req.update(kwargs)
    req = {
        key: values[0]
        if isinstance(values, list) else values
        for key, values in req.items()
        if key in requiredAttrs
    }
    return req


def sync_instances(source, target):
    """
    实例拷贝

    :param source:
    :param target:
    :return:
    """
    for attr in vars(source):
        if '_' not in attr:
            setattr(target, attr, getattr(source, attr))


def docx_2_pdf(docx_path_or_like: Union[BaseHTTPResponse, os.PathLike, str]) -> Optional[bytes]:
    """
    transfer docx to pdf, and return pdf with bytes

    :param docx_path_or_like: docx object, it can be uploaded with type of HTTPResponse、PathLike、str

    :return:
        `bytes`, pdf's bytes
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
        temp_pdf_path = temp_pdf.name

    # then create temp file objective to save file if HTTPResponse
    if isinstance(docx_path_or_like, BaseHTTPResponse):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
            temp_docx.write(docx_path_or_like.data)
            docx_path_or_like = temp_docx.name

    # do convert
    convert(docx_path_or_like, temp_pdf_path)

    # delete temp file after convertion
    if os.path.exists(docx_path_or_like):
        os.remove(docx_path_or_like)
    if os.path.exists(temp_pdf_path):
        with open(temp_pdf_path, "rb") as f:
            data = f.read()
        os.remove(temp_pdf_path)
        return data
    return None









