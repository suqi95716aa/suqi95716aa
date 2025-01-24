import json
from datetime import timedelta

from sanic import Blueprint, response

from util.str import get_fs_path
from util.op_thirdparty.fs_minio import presigned_url, stat_file
from logic import Code as c
from logic import Message as m
from conf.parser import conf2Dict
from router import (
    DH_STORAGE_DISPATCH,
    KBQA_STORAGE_TMP_PATH,
    KBQA_STORAGE_PATH
)

fs = Blueprint('file_system')

MINIO_CONFIG = conf2Dict()['MINIO_CONFIG']
BUCKET_NAMES = MINIO_CONFIG["BUCKET_NAMES"]
USER_FILE_BUCKET = BUCKET_NAMES.get("USER_FILE_BUCKET")


@fs.route("/fs/link", methods=['POST'])
async def fslink(request):
    """
    get url of file in fs

    :param Uid: user id
    :param KBID: only when `Service` is 2 (now)
    :param Service: 1 - datahelper; 2 - KBQA_temporary_zone; 3 - KBQA_persist_zone
    :param FileName: file name

    :return:
        list of file's names in staging zone
    """

    uid = request.form.get("uid")
    kbid = request.form.get("kbid")
    filename = request.form.get("fileName")
    service = int(request.form.get("service")) if request.form.get("service") else None

    if service == 1:
        arg = (uid, DH_STORAGE_DISPATCH, filename)
    elif service == 2:
        arg = (uid, KBQA_STORAGE_TMP_PATH, filename)
    elif service == 3:
        arg = (uid, KBQA_STORAGE_PATH, kbid, filename)
    else:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL, "data": {}}, ensure_ascii=False))

    # check file stat
    remote_path = get_fs_path(*arg)
    metadata = stat_file(USER_FILE_BUCKET, remote_path)
    if not metadata:
        return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_FILE_NOT_FOUND_EXISTS, "data": {}}, ensure_ascii=False))

    # do
    url = presigned_url(USER_FILE_BUCKET, remote_path, timedelta(hours=1))
    return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"url": url}}, ensure_ascii=False))


