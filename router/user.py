import hashlib
import datetime

from api.sms import a_send_sms
from util.common import *
from util.encryption import *
from util.cache import sms_key_buildup
from util.validate import validate_account, generate_code
from util.op_thirdparty.common import insert
from util.op_thirdparty.cache import hset, hgetall, getttl, setttl
from models.cache.connect import rins_sms
from models.database.user import UserInfo
from models.database.advise import FeedbackInfo
from models.database.connect import attach_db_session
from logic import Code as c
from logic import Message as m
from logic.user.base import UserBaseModel

from sanic import Blueprint, response
from sqlalchemy.exc import IntegrityError, DataError

user = Blueprint('user')

ENABLE = 0
DISABLE = 1
EXPIRE_TIME = 5
CODE_EXPIRE_TIME = 300
CODE_RESENT_TIME = 120


@user.route("/user/add", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def user_add(request):
    """
    user add

    :param username: 参考models/database/userinfo的对应字段
    :param password: 参考models/database/userinfo的对应字段
    :param phone: 参考models/database/userinfo的对应字段

    :return:
    """

    try:
        username = request.form.get("username")
        password = decryption(request.form.get("password"))
        phone = request.form.get("phone")
        code = int(request.form.get("code")) if request.form.get("code") else None
        if not username or not password or not phone:
            return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS, "data": {}}, ensure_ascii=False))

        # Validate relative user is exist
        is_pass = validate_account(username, password, phone)
        if not is_pass:
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_FORMAT_ERROR, "data": {}}, ensure_ascii=False))

        user = UserBaseModel(request.ctx.session)
        userinfo = await user.user_exist_by_uname_or_phone(username=username, phone=phone)
        if userinfo and userinfo.username == username:
            code = c.ERROR_USER_EXISTS
            message = m.MESSAGE_USERNAME_EXISTS
            return response.text(json.dumps({"code": code, "message": message, "data": {}}, ensure_ascii=False))
        elif userinfo and userinfo.phone == phone:
            code = c.ERROR_PHONE_EXISTS
            message = m.MESSAGE_PHONE_EXISTS
            return response.text(json.dumps({"code": code, "message": message, "data": {}}, ensure_ascii=False))

        # Validate code and reset flag
        code_pair = await hgetall(rins_sms, sms_key_buildup(1, phone))
        if not code_pair:
            return response.text(json.dumps({"code": c.ERROR_CODE_NOT_FOUND, "message": m.MESSAGE_CODE_NOT_FOUND_ERROR, "data": {}}, ensure_ascii=False))
        if not int(code_pair.get("code")) == code or int(code_pair.get("enable")) == DISABLE:
            return response.text(json.dumps({"code": c.ERROR_CODE_INVALID, "message": m.MESSAGE_CODE_INVALID_ERROR, "data": {}}, ensure_ascii=False))

        # Add user
        req = params_filter(request.form, UserInfo, password=password)
        uid = hashlib.sha256(str(datetime.datetime.now()).encode('utf-8')).hexdigest()[-7:]
        userinfo = UserInfo(
            **req,
            uid=uid,
            createTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            lastLoginTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        user = UserBaseModel(request.ctx.session, _user=userinfo)
        flag = await user.insert()
        await hset(rins_sms, sms_key_buildup(1, phone), key="enable", value=DISABLE)

        if flag:
            code = c.SUCCESS_REQUEST_CODE
            message = m.MESSAGE_REGISTER_SUCCESS
        else:
            code = c.ERROR_INTERNAL_SERVICE
            message = m.MESSAGE_REGISTER_ERROR
        return response.text(json.dumps({"code": code, "message": message, "data": {}}, ensure_ascii=False))

    except IntegrityError as e:
        return response.text(json.dumps({"code": c.ERROR_USER_EXISTS, "message": m.MESSAGE_USERNAME_EXISTS, "data": {}}, ensure_ascii=False))
    except DataError as e:
        return response.text(json.dumps({"code": c.ERROR_USER_DATA_LENGTH, "message": m.MESSAGE_DATA_LONG_ERROR, "data": {}}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": str(e), "data": {}}, ensure_ascii=False))


@user.route("/user/login", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def user_login(request):
    """
    user login

    :param loginType: 登陆方式, 0 - 账号密码， 1 - 手机号密码
    :param username: 参考models/database/userinfo的对应字段
    :param password: 参考models/database/userinfo的对应字段
    :param phone: 参考models/database/userinfo的对应字段

    :return:
    """
    try:
        loginType = request.form.get("loginType")

        # Verify username and password
        if loginType and int(loginType) == 0:
            uname = request.form.get("username")
            pwd = decryption(request.form.get("password"))
            user = UserBaseModel(session=request.ctx.session)
            userinfo = await user.get(username=uname)
            if not userinfo or userinfo.password != pwd:
                return response.text(json.dumps({"code": c.ERROR_USER_NOT_EXISTS, "message": m.MESSAGE_USERNAME_NOT_EXISTS, "data": {}}, ensure_ascii=False))

        # Verify phone and code
        elif loginType and int(loginType) == 1:
            phone = request.form.get("phone")
            code = int(request.form.get("code"))
            user = UserBaseModel(session=request.ctx.session)
            userinfo = await user.get(phone=phone)
            if not userinfo or userinfo.phone != phone:
                return response.text(json.dumps({"code": c.ERROR_PHONE_NOT_EXISTS, "message": m.MESSAGE_PHONE_NOT_EXISTS, "data": {}}, ensure_ascii=False))

            # Verify the correctness of code, but when the way of login with username and password, not need this step
            if loginType and int(loginType) == 1:
                code_pair = await hgetall(rins_sms, sms_key_buildup(2, phone))
                if not code_pair:
                    return response.text(json.dumps({"code": c.ERROR_CODE_NOT_FOUND, "message": m.MESSAGE_CODE_NOT_FOUND_ERROR, "data": {}}, ensure_ascii=False))
                if not int(code_pair.get("code")) == code or int(code_pair.get("enable")) == DISABLE:
                    return response.text(json.dumps({"code": c.ERROR_CODE_INVALID, "message": m.MESSAGE_CODE_INVALID_ERROR, "data": {}}, ensure_ascii=False))
                await hset(rins_sms, sms_key_buildup(2, phone), key="enable", value=DISABLE)

        else:
            return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS, "data": {}}, ensure_ascii=False))

        # Generate access token
        payload = {
            "uid": userinfo.uid,
            "username": userinfo.username,
            "userphone": userinfo.phone,
            "expire": time.mktime((datetime.datetime.now() + datetime.timedelta(hours=EXPIRE_TIME)).timetuple())
        }
        token = mid_encryption(payload)
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {"access_token": str(token)}}, ensure_ascii=False))

    except Exception as error:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR, "data": {}}, ensure_ascii=False))


@user.route("/user/recovery", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def user_recovery(request):
    """
     user password recovery

    :param phone: User phone number
    :param password: the newest password
    :param code: Verification code

    :return:
    """

    phone = request.form.get("phone")
    password = decryption(request.form.get("password"))
    code = request.form.get("code")
    if not validate_account(password=password):
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_FORMAT_ERROR, "data": {}}, ensure_ascii=False))

    user = None
    origin_pwd = None
    try:
        user = UserBaseModel(session=request.ctx.session)
        userinfo = await user.get(phone=phone)
        if not userinfo: return response.text(json.dumps({"code": c.ERROR_PHONE_NOT_EXISTS, "message": m.MESSAGE_PHONE_NOT_EXISTS, "data": {}}, ensure_ascii=False))

        # Verify code correctness
        code_pair = await hgetall(rins_sms, sms_key_buildup(3, phone))
        if not code_pair:
            return response.text(json.dumps({
                "code": c.ERROR_CODE_NOT_FOUND,
                "message": m.MESSAGE_CODE_NOT_FOUND_ERROR, "data": {}},
                ensure_ascii=False)
            )
        if not int(code_pair.get("code")) == int(code) or int(code_pair.get("enable")) == DISABLE:
            return response.text(json.dumps({
                "code": c.ERROR_CODE_INVALID,
                "message": m.MESSAGE_CODE_VALID, "data": {}},
                ensure_ascii=False)
            )

        # update user attr
        origin_pwd = userinfo.password
        user._user.password = password
        await user.update()
        await hset(rins_sms, sms_key_buildup(3, phone), key="enable", value=DISABLE)

        return response.text(json.dumps({
            "code": c.SUCCESS_REQUEST_CODE,
            "message": m.MESSAGE_OP_SUCCESS,
            "data": {}},
            ensure_ascii=False)
        )

    except Exception as error:
        if user and origin_pwd:
            user._user.password = origin_pwd
            await user.update()

        return response.text(json.dumps({
            "code": c.ERROR_INTERNAL_SERVICE,
            "message": m.MESSAGE_SERVER_ERROR,
            "data": {}},
            ensure_ascii=False)
        )


@user.route("/user/exist", methods=['GET'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def user_exist(request):
    """
    judge user exists

    :param uid: 参考models/database/userinfo的对应字段
    :return:
    """
    try:
        uid = request.form.get("uid")
        if not uid: return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        user = UserBaseModel(session=request.ctx.session)
        userinfo = await user.get(uid=uid)
        if userinfo:
            code = c.SUCCESS_REQUEST_CODE
            message = m.MESSAGE_USER_EXISTS
        else:
            code = c.ERROR_USER_NOT_EXISTS
            message = m.MESSAGE_USER_NOT_EXISTS
        return response.text(json.dumps({"code": code, "message": message, "data": {}}, ensure_ascii=False))

    except Exception as error:
        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR, "data": {}}, ensure_ascii=False))


@user.route("/user/advise", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def user_advise(request):
    """
    storage user advise

    :param uid: 参考models/database/adviseInfo的对应字段
    :param advise: 参考models/database/adviseInfo的对应字段

    :return:
    """
    try:
        uid = request.form.get("uid")
        feedback = request.form.get("feedback", "")
        score = request.form.get("score")

        if not (uid and score) or len(feedback) > 200 or int(score) not in list(range(1, 6)):
            return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        req = params_filter(request.form, FeedbackInfo)
        feedbackObj = FeedbackInfo(
            **req,
            status=0,
            createTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        is_inserted = await insert(request.ctx.session, feedbackObj)
        return response.text(
            json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_SUCCESS, "data": {}}, ensure_ascii=False)) if is_inserted else \
            response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_OP_FAIL}, ensure_ascii=False))

    except DataError as e:
        return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_DATA_LONG_ERROR}, ensure_ascii=False))
    except Exception as e:
        return response.text(
            json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_SERVER_ERROR}, ensure_ascii=False))


@user.route("/sms", methods=['POST'])
# @rate_limiter(seconds=120, limit=5)
@attach_db_session
async def sms(request):
    """
    sms server not need access token

    :param phone: phone to send sms
    :param type: 1 - register, 2 - login, 3 - password recovery, 4 - phone update

    :return:
    """
    try:
        phone = request.form.get("phone")
        typ = int(request.form.get("type", "")) if request.form.get("type") else None
        if not phone or not typ:
            return response.text(json.dumps({"code": c.ERROR_PARAMS_NOT_FOUND, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))

        # status of user exist
        user = UserBaseModel(request.ctx.session)
        userinfo = user.get(phone=phone)
        if not userinfo: return response.text(json.dumps({"code": c.ERROR_PHONE_NOT_EXISTS, "message": m.MESSAGE_PHONE_NOT_EXISTS, "data": {}}, ensure_ascii=False))

        # judge resent or cooling
        key = sms_key_buildup(typ, phone)
        code_pair = await hgetall(rins_sms, key)
        ttl = await getttl(rins_sms, key) if code_pair else False
        if CODE_EXPIRE_TIME - ttl <= CODE_RESENT_TIME:
            return response.text(json.dumps(
                {
                "code": c.ERROR_CODE_INVALID,
                "message": m.MESSAGE_CODE_COOLING,
                "data": {"resent": CODE_RESENT_TIME - (CODE_EXPIRE_TIME - ttl)}
                },
                ensure_ascii=False
            ))

        code = generate_code()
        is_send_success = await a_send_sms(phone, code)
        if not is_send_success: raise
        await hset(rins_sms, key, mapping={"code": code, "enable": ENABLE}, expired=CODE_EXPIRE_TIME)
        await setttl(rins_sms, key, CODE_EXPIRE_TIME)
        return response.text(json.dumps({"code": c.SUCCESS_REQUEST_CODE, "message": m.MESSAGE_CODE_VALID, "data": {}}, ensure_ascii=False))

    except Exception as error:

        return response.text(json.dumps({"code": c.ERROR_INTERNAL_SERVICE, "message": m.MESSAGE_SERVER_ERROR, "data": {}}, ensure_ascii=False))




