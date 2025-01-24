import os
import json
import datetime

from pymysql import IntegrityError
from sanic import Blueprint, response

from router import KBQA_STORAGE_TMP_PATH
from util.str import get_fs_path
from util.validate import generate_uid
from util.op_thirdparty.fs_minio import stat_file
from util.common import params_filter, sync_instances
from logic import Code as c
from logic import Message as m
from logic.user.user_kb import UserForKnowledgeBase
from logic.kbqa.flow.flow_query import flow as flow_query
from logic.kbqa.flow.flow_entity_extraction import flow as flow_extract
from logic.kbqa.model.knowledge import Knowledge
from logic.kbqa.model.knowledgebase import KnowledgeBase
from models.database.connect import attach_db_session
from models.database.knowledge import KnowledgeInfo
from models.database.knowledgebase import KnowledgeBaseInfo


kbqa = Blueprint('knowledge_base_question_anwer')

USER_FILE_BUCKET = os.environ["USER_FILE_BUCKET"]
# logger.add("sanic_router_kbqa.log", level="INFO", rotation="1 week", compression="zip")


@kbqa.route("/kb/add", methods=['POST'])
@attach_db_session
async def knowledgebase_add(request):
    """
    create KnowledgeBase in database.

    :param uid: Refer to models/database/KnowledgeBaseInfo
    :param kbName: Refer to models/database/KnowledgeBaseInfo
    :param kbDesc: Refer to models/database/KnowledgeBaseInfo
    :param kbLabel: Refer to models/database/KnowledgeBaseInfo
    :param kbColor: Refer to models/database/KnowledgeBaseInfo
    :param kbBGImg: Refer to models/database/KnowledgeBaseInfo

    :return:
        is that success to create or not (bool).
    """
    try:
        uid = request.form.get("uid")
        kbName = request.form.get("kbName")

        # basic element valid
        kb = KnowledgeBase(session=request.ctx.session)
        if await kb.get(uid, kbName=kbName):
            return response.text(json.dumps({"code": c.ERROR_DB_EXISTS, "message": m.MESSAGE_BASE_EXISTS, "data": {}}, ensure_ascii=False))

        currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kb_params = params_filter(
            request.form,
            KnowledgeBaseInfo,
            kbid=generate_uid(),
            kbCreateTime=currentTime,
            kbUpdateTime=currentTime,
        )
        new_kb_params = KnowledgeBaseInfo(**kb_params)
        new_kb = KnowledgeBase(session=request.ctx.session, _kb=new_kb_params)
        result = await new_kb.insert()
        if not result:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_OP_FAIL, "data": {}}, ensure_ascii=False))

        new_kb_dict = new_kb.format()
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": new_kb_dict}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_BASE_EXISTS}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR}, ensure_ascii=False))


@kbqa.route("/kb/update", methods=['POST'])
@attach_db_session
async def knowledgebase_update(request):
    """
    update KnowledgeBaseInfo in database.

    :param uid: Refer to models/database/KnowledgeBaseInfo
    :param kbid: Refer to models/database/KnowledgeBaseInfo
    :param kbName: Refer to models/database/KnowledgeBaseInfo
    :param kbDesc: Refer to models/database/KnowledgeBaseInfo
    :param kbLabel: Refer to models/database/KnowledgeBaseInfo
    :param kbColor: Refer to models/database/KnowledgeBaseInfo
    :param kbBGImg: Refer to models/database/KnowledgeBaseInfo

    :return:
        is that success to update or not (bool).
    """
    try:
        uid = request.form.get("uid")
        kbid = request.form.get("kbid")

        # query in db
        knowledgebase = KnowledgeBase(session=request.ctx.session)
        if not await knowledgebase.get(uid, kbid=kbid):
            return response.text(json.dumps({"code": c.ERROR_DB_EXISTS, "message": m.MESSAGE_BASE_EXISTS, "data": {}}, ensure_ascii=False))

        # params filter
        kb_params = params_filter(
            request.form,
            KnowledgeBaseInfo,
            kbCreateTime=getattr(knowledgebase, "kbCreateTime"),
            kbUpdateTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        new_kb = KnowledgeBaseInfo(**kb_params)
        sync_instances(new_kb, knowledgebase._kb)
        await knowledgebase.update()
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": new_kb.to_dict()}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_BASE_EXISTS}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": f"{e}."}, ensure_ascii=False))


@kbqa.route("/kb/get", methods=['POST'])
@attach_db_session
async def knowledgebase_list(request):
    """
        get knowledgebase list

        :param uid: Refer to models/database/KnowledgeBaseInfo

        :return:
            list. contains knowledgebase and knowledge info.
    """
    uid = request.form.get("uid")

    user = UserForKnowledgeBase(session=request.ctx.session)
    if not await user.get(uid=uid): return response.text(json.dumps({"code": c.ERROR_USER_NOT_EXISTS, "message": m.MESSAGE_USER_NOT_EXISTS, "data": {}}, ensure_ascii=False))

    try:
        user = UserForKnowledgeBase(session=request.ctx.session)
        await user.get(uid=uid)
        ret = await user.format()
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": ret}, ensure_ascii=False))

    except Exception as error:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": f"{error}"}, ensure_ascii=False))


@kbqa.route("/kb/delete", methods=['POST'])
@attach_db_session
async def knowledgebase_delete(request):
    """
        delete knowledgebase

        :param uid: Refer to models/database/KnowledgeBaseInfo
        :param kbid: Refer to models/database/KnowledgeBaseInfo

        :return:
            is that success to delete or not (bool).
    """
    try:
        uid = request.form.get("uid")
        kbid = request.form.get('kbid')

        kb = KnowledgeBase(request.ctx.session)
        await kb.get(uid=uid, kbid=kbid)
        deleted = await kb.delete()
        if deleted:
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS}, ensure_ascii=False))
        else:
            return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR}, ensure_ascii=False))

    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": f"{e}"}, ensure_ascii=False))


@kbqa.route("/k/previews/upload", methods=['POST'])
@attach_db_session
async def knowledge_previews_upload(request):
    """
    对应知识存储在用户临时目录
    storage user file in template zone.

    :param uid: Refer to models/database/KnowledgeBaseInfo
    :param file: File instance

    :return:
        is that success to upload or not (bool).
    """
    uid = request.form.get("uid")
    file = request.files.get('file')
    if not (uid and file):
        return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

    user = UserForKnowledgeBase(request.ctx.session)
    await user.get(uid=uid)
    uploaded = user.upload_temporary_zone(file)
    if uploaded:
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"file_name": file.name}}, ensure_ascii=False))
    else:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_OP_FAIL, "data": {}}, ensure_ascii=False))


@kbqa.route("/k/previews/rm", methods=['POST'])
async def knowledge_previews_remove(request):
    """
    remove file from template zone.

    :param uid: Refer to models/database/KnowledgeBaseInfo
    :param filename: filename in template zone.

    :return:
        is that success to remove or not (bool).
    """
    uid = request.form.get("uid")
    filename = request.form.get('fileName')
    if not (uid and filename):
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

    # remove file in fs
    user = UserForKnowledgeBase(request.ctx.session)
    await user.get(uid=uid)
    deleted = user.delete_temporary_zone(filename)

    if deleted:
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS}, ensure_ascii=False))
    else:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR}, ensure_ascii=False))


@kbqa.route("/k/previews", methods=['POST'])
async def knowledge_previews(request):
    """
    knowledge to chunks, and move file from template zone to the user kb path

    :param uid: Refer to models/database/KnowledgeBaseInfo
    :param type: QA method e.g.  1 - Character split ; 2 - Traditional title split； 3 - Self-defined split title; 4 - Table QA split; 5 - Commodity QA
    :param fileName: filename in template zone
    :param kconfig: config about file, like:
            Split text：chunk_size、chunk_overlap，
            Split word：word - split_headers_re , default word official header
            Split csv：delimiter

            Set other types to null except for the current type that needs the parameters.

    :return:
        result of chunks
    """
    uid = request.form.get("uid")
    typ = int(request.form.get('type')) if request.form.get('type') else None
    filename = request.form.get('fileName')
    kconfig = json.loads(request.form.get('kconfig')) if request.form.get('kconfig') else {}

    # file existed in staging zone
    user = UserForKnowledgeBase(request.ctx.session)
    existed = user.judge_temporary_zone(filename)
    if existed:
        return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_FILE_NOT_FOUND_EXISTS, "data": {}}, ensure_ascii=False))

    # split doc content to chunk
    empty_k = Knowledge(request.ctx.session)
    chunks = await empty_k.split_chunk(uid, filename, typ, kconfig, "temporary")

    # preview 5k token
    if typ == 4:
        new_chunks = chunks[:10]
    else:
        new_chunks = []
        total_len = 0
        for chunk in chunks:
            new_chunks.append(chunk)
            total_len += len(chunk.page_content)
            if total_len > 5000:
                break

    # parse chunks format
    if typ == 2 or typ == 3:
        chunk_info = [
            {
                "chunk_num": f"#{ind + 1}",
                "text": chunk.page_content,
                "title": (' - '.join(chunk.metadata.values()) if len(chunk.metadata.keys()) > 1 else list(chunk.metadata.values())[0]) if chunk.metadata else "",
            }
            for ind, chunk in enumerate(new_chunks)
        ]
    else:
        chunk_info = [
            {"chunk_num": f"#{ind + 1}", "text": chunk.page_content}
            for ind, chunk in enumerate(new_chunks)
        ]

    ret = {
        "type": typ,
        "file_name": filename,
        "chunk_num": len(new_chunks),
        "total_chunk_num": len(chunks)
    }
    ret.update({"chunk_info": chunk_info})
    return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": ret}, ensure_ascii=False))


@kbqa.route("/k/previews/get", methods=['POST'])
async def knowledge_previews_list(request):
    """
    Get list of staging zone

    :param uid: user id

    :return:
        list of file's names in staging zone
    """
    uid = request.form.get("uid")

    user = UserForKnowledgeBase(request.ctx.session)
    await user.get(uid=uid)
    list_filenames = user.get_temporary_zone()
    return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": list_filenames}, ensure_ascii=False))


@kbqa.route("/k/add", methods=['POST'])
@attach_db_session
async def knowledge_add(request):
    """
    deal the file to minio and its vector in milvus

    :param uid: Refer to models/database/KnowledgeInfo
    :param kbid: Refer to models/database/KnowledgeInfo
    :param type: Refer to models/database/KnowledgeInfo
    :param filename: file in tmp zone
    :param kconfig: knowledge relative config, like `chunk_size`、`chunk_overlap`、`chunk_overlap`

    :return:
        bool. is that success or not.
    """
    uid = request.form.get("uid")
    typ = request.form.get('type')
    filename = request.form.get('fileName')
    kconfig = json.loads(request.form.get('kconfig')) if request.form.get('kconfig') else {}
    if not (uid and filename and typ):
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

    try:
        remote_tmp_path = get_fs_path(uid, KBQA_STORAGE_TMP_PATH, filename)
        file_metadata = stat_file(USER_FILE_BUCKET, remote_tmp_path)
        if not file_metadata:
            return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_FILE_NOT_FOUND_EXISTS, "data": {}}, ensure_ascii=False))

        # create KnowledgeInfo object
        currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kinfo = KnowledgeInfo(**params_filter(
            request.form,
            KnowledgeInfo,
            kid=generate_uid(),
            kconfig=kconfig,
            kName=filename,
            ktype=typ,
            kPath=remote_tmp_path,
            kCreateTime=currentTime,
            kUpdateTime=currentTime
        ))

        k = Knowledge(session=request.ctx.session, _k=kinfo)
        inserted = await k.insert()
        if inserted:
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": k.format()}, ensure_ascii=False))
        else:
            return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR}, ensure_ascii=False))

    except Exception as error:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": f"{error}"}, ensure_ascii=False))


@kbqa.route("/k/delete", methods=['POST'])
@attach_db_session
async def knowledge_delete(request):
    """
        delete file and file vector chunks

        :param uid: Refer to models/database/KnowledgeInfo
        :param kbid: Refer to models/database/KnowledgeInfo
        :param kid: Refer to models/database/KnowledgeInfo

        :return:
            bool. is that remove success or not.
    """
    try:
        uid = request.form.get("uid")
        kid = request.form.get('kid')

        k = Knowledge(request.ctx.session)
        if not await k.get(uid=uid, kid=kid):
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_KNOWLEDGE_NOT_FOUND_EXISTS}, ensure_ascii=False))

        deleted = await k.delete()
        if deleted:
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS}, ensure_ascii=False))
        else:
            return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR}, ensure_ascii=False))

    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": f"{e}"}, ensure_ascii=False))


@kbqa.route("/k/data", methods=['POST'])
@attach_db_session
async def knowledge_data(request):
    """
        get the chunks about file

        :param Uid: Refer to models/database/KnowledgeInfo
        :param KBID: Refer to models/database/KnowledgeInfo
        :param KID: Refer to models/database/KnowledgeInfo

        :return:
            chunks of relative file(knowledge).
    """
    try:
        uid = request.form.get("uid")
        kid = request.form.get('kid')
        offset = int(request.form.get('offset')) if request.form.get('offset') else None
        limit = int(request.form.get('limit')) if request.form.get('limit') else None
        if limit < 0:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_PARAM_MISSING}, ensure_ascii=False))

        k = Knowledge(request.ctx.session)
        if not await k.get(uid=uid, kid=kid):
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_KNOWLEDGE_NOT_FOUND_EXISTS}, ensure_ascii=False))

        data = await k.query_vector()
        sorted_data = sorted(data, key=lambda x: x['sequence'], reverse=False)[offset:min(offset + limit, len(data))]
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"total": len(data), "chunks_info": sorted_data}}, ensure_ascii=False))

    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": f"{e}"}, ensure_ascii=False))


# TODO: not finish
# @kbqa.route("/kbqa/query", methods=['POST'])
# # @rate_limiter(seconds=3000, limit=20)
# @log_recorder
# @attach_db_session
# async def query(request):
#     """
#     QA for knowledge base
#
#     :param userId: current user id
#     :param Query: user's query
#     :param screenId: screen unique id
#     :param screenType: screen type to ask
#
#     :return:
#         the answer of question, and some relative similar chunks
#     """
#     userId = request.form.get("userId")
#     screenId = request.form.get("screenId")
#     screenType = request.form.get("screenType")
#     query = request.form.get("query")
#
#     ScreenItem = await dh_screen_exist_screeninfo(request.ctx.session, userId, screenId, screenType)
#     if not ScreenItem: return response.text(
#         json.dumps({"code": ERROR_PARAMS, "message": f"This screen id can not be used or deleted"}, ensure_ascii=False))
#
#     # First, find the classification of question user's mention
#     # Specify please refer to the method inside
#     # intent_num = await to_generate_intent(query=query)
#     intent_num = 1
#     if intent_num == 1:
#         ans, chunks = await query_single_jump(session=request.ctx.session, query=query, uid=userId, **ScreenItem[0].screenQAConfig)
#     elif intent_num == 2:
#         ans, chunks = await query_single_jump(session=request.ctx.session, query=query, uid=userId, **ScreenItem[0].screenQAConfig)
#     elif intent_num == 3:
#         ans, chunks = await query_single_jump(session=request.ctx.session, query=query, uid=userId, **ScreenItem[0].screenQAConfig)
#     else:
#         return response.text(json.dumps({"code": ERROR_PARAMS, "message": "Error params!!!"}, ensure_ascii=False))
#
#     # If not found any knowledge here, return directly
#     if not ans and not chunks:
#         return response.text(json.dumps({"code": ERROR_PARAMS, "message": "Upload relative knowledge before question.", "data": {}}, ensure_ascii=False))
#
#     sorted_chunks = sorted([{"page_content": chunk.page_content, "score": chunk.metadata.get("score")} for chunk in chunks], key=lambda x: x.get('score', 0), reverse=True)
#     return response.text(json.dumps({"code": CODE_SUCCESS_REQUEST, "message": "Success to find answer.", "data": {"answer": ans, "chunks": sorted_chunks}}, ensure_ascii=False))



@kbqa.route("/kbqa/query", methods=['POST'])
# @rate_limiter(seconds=3000, limit=20)
# @log_recorder
@attach_db_session
async def query(request):
    """
    QA for knowledge base

    :param userId: current user id
    :param query: user's query
    :param screenId: screen unique id
    :param screenType: screen type to ask

    :return:
        the answer of question, and some relative similar chunks
    """
    uid = request.form.get("userId")
    sid = request.form.get("screenId")
    # screenType = request.form.get("screenType")
    query = request.form.get("query")

    d = await flow_query(request.ctx.session, uid, sid, query)
    if not d:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS, "data": {}}, ensure_ascii=False))
    return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {}}, ensure_ascii=False))

