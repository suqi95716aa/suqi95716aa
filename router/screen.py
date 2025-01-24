import hashlib

from logic.screen.screen import Screen
from logic.user.user_screen import UserForScreen
from util.op_thirdparty.dh_db import *
from util.common import *
from util.encryption import *
from models.database.screen import ScreenInfo
from models.database.connect import attach_db_session

from sanic import Blueprint, response
from sqlalchemy.exc import IntegrityError, DataError


screen = Blueprint('Screen')


@screen.route("/screen/add", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def screen_add(request):
    """
    Add screen

    :param uid: Refer to models/database/userinfo
    :param screenId: Refer to models/database/screeninfo
    :param screenName: Refer to models/database/screeninfo
    :param screenType: Refer to models/database/screeninfo
    :param screenDesc: Refer to models/database/screeninfo
    :param configId: Part of models/database/screeninfo ScreenQAConfig
    :param configName: Part of models/database/screeninfo ScreenQAConfig
    :param groupList: Part of models/database/screeninfo ScreenQAConfig
    :param kbids: Part of models/database/screeninfo ScreenQAConfig
    :param relevantHits: Part of models/database/screeninfo ScreenQAConfig
    :param similarityThreshold: Part of models/database/screeninfo ScreenQAConfig

    :return:
    """
    try:
        uid = request.form.get("uid")
        if not uid: return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        user = UserForScreen(request.ctx.session)
        useritem = await user.get(uid=uid)
        if not useritem: return response.text(json.dumps({"code": c.ERROR_USER_NOT_EXISTS, "message": m.MESSAGE_USER_NOT_EXISTS, "data": {"exist": 0}}, ensure_ascii=False))

        screenType = request.form.get("screenType")
        # Datahelper QA
        if int(screenType) == 1:
            configId = request.form.get("configId")
            configName = request.form.get("configName")
            groupList = json.loads(request.form.get("groupList"))
            request.form["screenQAConfig"] = [{"ConfigId": configId, "ConfigName": configName, "GroupList": groupList}]
        # KnowledgeBase QA
        elif int(screenType) == 2:
            kbids = json.loads(request.form.get("kbids"))
            relevantHits = request.form.get("relevantHits")
            similarityThreshold = request.form.get("similarityThreshold")
            request.form["screenQAConfig"] = [{"SimilarityThreshold": similarityThreshold, "RelevantHits": relevantHits, "KBIDS": kbids}]
        else:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        req = params_filter(request.form, ScreenInfo)
        screeninfo = ScreenInfo(
            **req,
            screenId=hashlib.sha256(str(datetime.datetime.now()).encode('utf-8')).hexdigest()[-7:],
            createTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updateTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        screen = Screen(request.ctx.session, screeninfo)
        inserted = await screen.insert()
        if inserted:
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": screen.to_dict()}, ensure_ascii=False))
        else:
            return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR, "data": screen.to_dict()}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_DUPLICATE_ERROR}, ensure_ascii=False))
    except DataError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SCREEN_FOUND_EXISTS}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": str(e)}, ensure_ascii=False))


@screen.route("/screen/delete", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def screen_delete(request):
    """
    Delete screen

    :param uid: Refer to models/database/userinfo
    :param screenId: Refer to models/database/screeninfo

    :return:
    """
    try:
        uid = request.form.get("uid")
        screenid = request.form.get("screenId")

        screen = Screen(request.ctx.session)
        screeninfo = await screen.get(uid=uid, screenid=screenid)
        if not screeninfo:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SCREEN_NOT_FOUND_EXISTS, "data": screen.to_dict()}, ensure_ascii=False))

        deleted = await screen.delete()
        if deleted:
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"isDel": True}}, ensure_ascii=False))
        else:
            return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR, "data": screen.to_dict()}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_DUPLICATE_ERROR}, ensure_ascii=False))
    except DataError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SCREEN_FOUND_EXISTS}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": str(e)}, ensure_ascii=False))


@screen.route("/screen/update", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def screen_update(request):
    """
    Update screen

    :param uid: Refer to models/database/userinfo
    :param screenId: Refer to models/database/screeninfo
    :param screenName: Refer to models/database/screeninfo
    :param screenType: Refer to models/database/screeninfo
    :param screenDesc: Refer to models/database/screeninfo
    :param configId: Part of models/database/screeninfo ScreenQAConfig
    :param configName: Part of models/database/screeninfo ScreenQAConfig
    :param groupList: Part of models/database/screeninfo ScreenQAConfig
    :param KBIDS: Part of models/database/screeninfo ScreenQAConfig
    :param relevantHits: Part of models/database/screeninfo ScreenQAConfig
    :param similarityThreshold: Part of models/database/screeninfo ScreenQAConfig

    :return:
    """
    try:
        uid = request.form.get("uid")
        screenType = request.form.get("screenType")
        screenid = request.form.get("screenId")
        if not uid or not screenType or not screenid:
            return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        screen = Screen(request.ctx.session)
        screeninfo = await screen.get(uid=uid, screenid=screenid)
        if not screeninfo:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SCREEN_NOT_FOUND_EXISTS, "data": screen.to_dict()}, ensure_ascii=False))

        screenName = request.form.get("screenName")
        screenDesc = request.form.get("screenDesc")
        updateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        config = {
            "Uid": uid,
            "ScreenId": screenid,
            "ScreenName": screenName,
            "ScreenDesc": screenDesc,
            "UpdateTime": updateTime
        }
        # Datahelper QA
        if int(screenType) == 1:
            configId = request.form.get("configId")
            configName = request.form.get("configName")
            groupList = json.loads(request.form.get("groupList"))
            config.update({"ScreenQAConfig": {"ConfigId": configId, "ConfigName": configName, "GroupList": groupList}})
        # KnowledgeBase QA
        elif int(screenType) == 2:
            kbids = json.loads(request.form.get("kbids"))
            relevantHits = request.form.get("relevantHits")
            similarityThreshold = request.form.get("similarityThreshold")
            config.update({"ScreenQAConfig": {"SimilarityThreshold": similarityThreshold, "RelevantHits": relevantHits, "KBIDS": kbids}})
        else:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        new_screen = ScreenInfo(**config)
        sync_instances(new_screen, screen._screen)
        updated = await screen.update()
        if updated:
            return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": screen.format()}, ensure_ascii=False))
        else:
            return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR, "data": {}}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_DUPLICATE_ERROR}, ensure_ascii=False))
    except DataError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SCREEN_FOUND_EXISTS}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": str(e)}, ensure_ascii=False))


@screen.route("/screen/list", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def screen_list(request):
    """
    Get and return complete screen list

    :param Uid: Refer to models/database/userinfo

    :return:
    """
    try:
        uid = request.form.get("uid")
        if not uid: return response.text(
            json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_PARAM_MISSING}, ensure_ascii=False))

        user = UserForScreen(request.ctx.session)
        useritem = await user.get(uid=uid)
        if not useritem: return response.text(json.dumps({"code": c.ERROR_USER_NOT_EXISTS, "message": m.MESSAGE_USER_NOT_EXISTS, "data": {"exist": 0}}, ensure_ascii=False))

        # generate item
        screens_format = await user.format()
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": screens_format}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_DUPLICATE_ERROR}, ensure_ascii=False))
    except DataError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SCREEN_FOUND_EXISTS}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": str(e)}, ensure_ascii=False))
