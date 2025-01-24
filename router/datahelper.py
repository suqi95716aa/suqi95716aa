import json
import os.path
from io import BytesIO

import aiofiles
import openpyxl
import pandas as pd
from sanic import Blueprint, response

from conf.parser import conf2Dict
from router import *
from util.op_thirdparty.fs_minio import (
    stat_file,
    upload_file_with_stream,
    delete_file,
    download_file_to_memory
)
from util.df import detect_dtype
from util.str import get_fs_path
from util.common import params_filter
from util.validate import generate_uid
from util.decorator.dec_recorder import log_recorder
from util.op_thirdparty.dh_db import *
from logic import Code as c
from logic import Message as m
from logic.datahelper.query import executeNativeQA
from logic.datahelper.source.mysql import MySQLSourceParser
from logic.datahelper.source.excel import ExcelSourceExecutor
from models.database.connect import attach_db_session
from models.database.config import ConfigInfo
from models.base.source import SourceNativeConfig, SourceDatabaseConfig

dh = Blueprint('datahelper')

DH_ALLOW_FILE_TYPE = [".xlsx"]
ALLOW_LABEL = ["mysql", "excel"]

MINIO_CONFIG = conf2Dict()['MINIO_CONFIG']
BUCKET_NAMES = MINIO_CONFIG["BUCKET_NAMES"]
USER_FILE_BUCKET = BUCKET_NAMES.get("USER_FILE_BUCKET")


@dh.route("/config/add", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def sourceAdd(request):
    """
    Upload file to fs (now only support xlsx), config to database

    :param Label: Enum (mysql、excel)
    :param FileName: file instance
    :param Host: Refer to SourceDatabaseConfig
    :param Port: Refer to SourceDatabaseConfig
    :param User: Refer to SourceDatabaseConfig
    :param Password: Refer to SourceDatabaseConfig
    :param Database: Refer to SourceDatabaseConfig
    :param Charset: Refer to SourceDatabaseConfig
    :return:
    """
    uid = request.form.get("uid")
    label = request.form.get("label").lower()
    filepath = None
    if label not in ALLOW_LABEL:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))
    if not uid:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_PARAM_MISSING}, ensure_ascii=False))

    try:
        if label == "mysql":
            # test connect to database, will return fail when disconnected
            dbParams = params_filter(request.form, SourceDatabaseConfig)
            mysqlConfig = SourceDatabaseConfig(**dbParams)
            isConnected = MySQLSourceParser.testConnectOutter(mysqlConfig)
            if not isConnected:
                return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL}, ensure_ascii=False))
        elif label == "excel":
            # spilt prefix
            file = request.files.get('file')
            if os.path.splitext(file.name)[1] not in DH_ALLOW_FILE_TYPE:
                return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))
            # if file already exists will return fail
            filepath = get_fs_path("/", uid, DH_STORAGE_DISPATCH, file.name)
            file_metadata = stat_file(USER_FILE_BUCKET, filepath)
            if file_metadata:
                return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_FILE_EXISTS}, ensure_ascii=False))
            # storage in fs
            is_uploaded = upload_file_with_stream(
                bucket_name=USER_FILE_BUCKET,
                remote_file_path=filepath,
                file_body=BytesIO(file.body),
                file_length=len(file.body)
            )
            dbParams = params_filter(request.form, SourceNativeConfig, Paths=filepath)

        ConfigId = generate_uid()
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        configParams = params_filter(
            request.form,
            ConfigInfo,
            configId=ConfigId,
            config=dbParams,
            createTime=nowTime,
            updateTime=nowTime
        )
        await dh_insert_if_not_exist_configinfo(request.ctx.session, configParams)
        return response.text(json.dumps({
            "code": c.SUCCESS_REQUEST_CODE,
            "message": m.MESSAGE_OP_SUCCESS,
            "data": ConfigInfo(**configParams).to_dict()
        }, ensure_ascii=False))

    except Exception as error:
        logger.error(f"Error happended：{error}")
        if stat_file(USER_FILE_BUCKET, filepath): delete_file(bucket_name=USER_FILE_BUCKET, remote_file_path=filepath)
        # TODO：要删除对应的MYSQL记录
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL}, ensure_ascii=False))


@dh.route("/config/del", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def sourceDel(request):
    """
    删除对应对应配置信息
    :param Uid: 用户ID
    :param ConfigId: 配置ID
    :return:
    """
    try:
        uid = request.form.get("uid")
        configId = request.form.get("configId")
        if not uid or not configId:
            return response.text(json.dumps({
                "code": c.ERROR_PARAMS,
                "message": m.MESSAGE_INVALID_PARAMS},
                ensure_ascii=False)
            )

        row = await dh_config_exist_configinfo(request.ctx.session, uid, configId)
        if not row: return response.text(
            json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_CONFIG_NOT_FOUND_EXISTS}, ensure_ascii=False))

        await dh_del(request.ctx.session, row[0])
        label = row[0].label.lower()
        if label == "excel":
            storagePath = row[0].config["Paths"]
            delete_file(USER_FILE_BUCKET, storagePath[1:])

        return response.text(
            json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"ConfigId": configId}},
                       ensure_ascii=False))
    except Exception as error:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL}, ensure_ascii=False))


@dh.route("/config/get", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def SourceGet(request):
    """
    获取用户下的所有数据源配置信息，返回所有数据源和对应数据源的表格、类型

    :param request:
    :return:
    """
    uid = request.form.get("uid")
    if not uid:
        return response.text(
            json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

    try:
        configs = await dh_config_all_configinfo(request.ctx.session, uid)
        data = list()
        for config in configs:
            config = config[0]
            try:
                data.append({
                    **config.to_dict(),
                    "Status": c.SUCCESS_REQUEST_CODE
                })
            except Exception as error:
                data.append({
                    **config.to_dict_error(),
                    "Status": c.ERROR_PARAMS,
                    "Error": m.MESSAGE_OP_FAIL
                })

        return response.text(
            json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"configInfo": data}},
                       ensure_ascii=False))

    except Exception as error:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL}, ensure_ascii=False))


@dh.route("/config/update", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def sourceUpdate(request):
    """
    更新数据源
    :param Uid: 用户ID
    :param ConfigId: 配置ID
    :param Label: 只能傳Excel\Mysql
    :param FileName: 上传的文件

    :return:
    """
    uid = request.form.get("uid")
    configId = request.form.get("configId")

    row = await dh_config_exist_configinfo(request.ctx.session, uid, configId)
    if not row: return response.text(
        json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_CONFIG_NOT_FOUND_EXISTS}, ensure_ascii=False))

    label = row[0].label.lower()
    if label == "mysql":
        pass
    elif label == "excel":
        file = request.files.get('FileName')
        oldFilePath = row[0].config["Paths"]

        # 更新数据库
        newFilePath = os.path.join(os.path.dirname(oldFilePath), file.name)
        row[0].config["Paths"] = newFilePath
        row[0].updateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        isUpdate = await dh_config_update_configinfo(request.ctx.session, row[0])
        if not isUpdate:
            return response.text(json.dumps({
                "code": c.ERROR_INTERNAL_SERVICE,
                "message": m.MESSAGE_SERVER_ERROR},
                ensure_ascii=False))

        # 删除旧文件，插入新文件
        if os.path.exists(oldFilePath): os.remove(oldFilePath)
        async with aiofiles.open(newFilePath, 'wb') as f:
            await f.write(file.body)

        # 必须要重新查，在相同数据库连接修改对象后，会触发惰性加载，在同步情况下会报错
        row = await dh_config_exist_configinfo(request.ctx.session, uid, configId)

        return response.text(json.dumps({
            "code": c.SUCCESS_REQUEST_CODE,
            "message": "Saved",
            "data": row[0].to_dict(),
        }, ensure_ascii=False))


@dh.route("/config/data", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def sourcePage(request):
    """
    通过分页获取数据
    :param Uid: 用户ID
    :param ConfigId: 配置ID
    :param Label: 只能傳Excel\Mysql
    :param Offset: 偏移量
    :param Limit: 获取数量
    :param SheetName: 待打开的表名

    :return:
    """
    uid = request.form.get("uid")
    configId = request.form.get("configId")
    sheetName = request.form.get("sheetName")
    offset = int(request.form.get("offset")) if request.form.get("offset") else None
    limit = int(request.form.get("limit")) if request.form.get("limit") else None

    if not uid or not configId or not sheetName:
        return response.text(
            json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

    row = await dh_config_exist_configinfo(request.ctx.session, uid, configId)
    if not row: return response.text(
        json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_CONFIG_NOT_FOUND_EXISTS}, ensure_ascii=False))

    label = row[0].label.lower()
    if label == "excel":
        row = await dh_config_exist_configinfo(request.ctx.session, uid, configId)
        if not row:
            return response.text(
                json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_FILE_NOT_FOUND_EXISTS}, ensure_ascii=False))

        storagePath = row[0].config["Paths"]
        if not stat_file(USER_FILE_BUCKET, storagePath):
            return response.text(
                json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_FILE_NOT_FOUND_EXISTS, "data": {"ConfigId": configId}},
                           ensure_ascii=False))
        buffer = download_file_to_memory(USER_FILE_BUCKET, storagePath)
        excel_file = BytesIO(buffer.read())
        if sheetName not in pd.ExcelFile(excel_file).sheet_names:
            return response.text(
                json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SHEET_NOT_FOUND_EXISTS, "data": {}}, ensure_ascii=False))

        # 获取相应的数据行数
        queryData = pd.read_excel(
            excel_file,
            skiprows=list(range(1, offset + 1)),
            nrows=limit, header=0, sheet_name=sheetName
        ).astype("str").to_dict("records")
        workbook = openpyxl.load_workbook(excel_file, read_only=True)
        sheet = workbook[sheetName]
        rowCount = sheet.max_row - 1
        workbook.close()

    elif label == "mysql":
        pass

    return response.text(
        json.dumps({
            "code": c.SUCCESS_REQUEST_CODE,
            "message": m.MESSAGE_OP_SUCCESS,
            "data": {
                "records": queryData,
                "total": rowCount,
                "limit": limit,
                "offset": offset
            }}, ensure_ascii=False)
    )


# @dh.route("/config/download", methods=['POST'])
# # @rate_limiter(seconds=120, limit=5)
# @attach_db_session
# async def sourceDownload(request):
#     """
#     通过分页获取数据
#     :param Uid: 用户ID
#     :param ConfigId: 配置ID
#
#     :return:
#     """
#     uid = request.form.get("Uid")
#     configId = request.form.get("ConfigId")
#
#     row = await dh_config_exist_configinfo(request.ctx.session, uid, configId)
#     if not row: return response.json({"code": c.ERROR_PARAMS, "message": f"Never found this config..."})
#
#     Path = row[0].Config["Paths"]
#     label = row[0].Label.lower()
#     try:
#         if label == "excel" and os.path.exists(Path):
#             file = await response.file(Path)
#             file.headers['Content-Type'] = CONTENT_TYPE["file"]
#             file.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(os.path.basename(Path))}"
#             return file
#         raise Exception
#     except Exception:
#         return response.HTTPResponse(
#             body=json.dumps({
#                 "code": c.ERROR_PARAMS_NOT_FOUND,
#                 "message": "Found file error or nothing",
#             }, ensure_ascii=False),
#             headers={'Content-Type': CONTENT_TYPE["json"]}
#         )


@dh.route("/dh/query", methods=['POST'])
# @rate_limiter(seconds=3000, limit=20)
@log_recorder
@attach_db_session
async def query(request):
    """
    QA（Now only support Excel chat）

    :param Query: question
    :param UserId: 参考models/database/screeninfo的对应字段
    :param screenId: 参考models/database/screeninfo的对应字段
    :param ScreenType: 参考models/database/screeninfo的对应字段

    :return:
    """
    userId = request.form.get("userId")
    screenId = request.form.get("screenId")
    query = request.form.get("query")
    screenType = request.form.get("screenType")

    ScreenItem = await dh_screen_exist_screeninfo(request.ctx.session, userId, screenId, screenType)
    if not ScreenItem: return response.text(json.dumps({
        "code": c.ERROR_PARAMS,
        "message": m.MESSAGE_SCREEN_NOT_FOUND_EXISTS},
        ensure_ascii=False)
    )
    ConfigItem = await dh_config_exist_configinfo(request.ctx.session, userId, ScreenItem[0].screenQAConfig.get("ConfigId"))
    if not ConfigItem: return response.text(json.dumps({
        "code": c.ERROR_PARAMS,
        "message": m.MESSAGE_CONFIG_NOT_FOUND_EXISTS},
        ensure_ascii=False)
    )

    try:
        label = ConfigItem[0].label.lower()
        if label.lower() == "excel":
            excelConfig = SourceNativeConfig(
                label,
                [ConfigItem[0].config.get("Paths")],
                ScreenItem[0].screenQAConfig.get("GroupList")
            )
            sourceExecutor = ExcelSourceExecutor(excelConfig)
            res, sql, spss_reasoning = await executeNativeQA(request.ctx.session, query, sourceExecutor)
            logger.info(json.dumps(res.to_dict('records'), ensure_ascii=False)[:100])

            return response.HTTPResponse(
                body=json.dumps({
                    "code": c.SUCCESS_REQUEST_CODE,
                    "message": m.MESSAGE_OP_SUCCESS,
                    "data": {
                        "sourceData": res.to_dict('records'),
                        "sourceType": detect_dtype(res),
                        "sql": sql,
                        "spss_reasoning": spss_reasoning
                    }
                }, ensure_ascii=False),
                headers={'Content-Type': "application/json"}
            )

        elif label.lower() == "mysql":
            pass

        return response.text(
            json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL}, ensure_ascii=False))

    except ValueError as e:
        return response.text(json.dumps({
            "code": c.ERROR_WRONG_TYPE_CONCAT,
            "message": m.MESSAGE_WRONG_TYPE_CONCAT_ERROR},
            ensure_ascii=False)
        )
