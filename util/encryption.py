import json
import time
import base64
from typing import Dict, Any

from conf.parser import conf2Dict
from logic import Code as c
from logic import Message as m

from sanic import response
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


aes = conf2Dict()['AES']

skip_routers = [
    "/user/add",
    "/user/login",
    "/user/recovery"
]


def mid_encryption(payload: Dict) -> str:
    """middleware to encrypt payload"""
    key = base64.b64decode(aes.get("SECRET_KEY"))
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(json.dumps(payload).encode("utf-8"), AES.block_size))
    return base64.b64encode(iv + encrypted).decode("utf-8")


def mid_decryption(request):
    """middleware to validate user account"""
    if request.path in skip_routers:
        return
    # sms server
    elif request.path == "/sms":
        typ = request.form.get("type")
        if not str(typ).isdigit():
            return response.text(json.dumps({"code": c.ERROR_PARAMS, "message": m.MESSAGE_INVALID_PARAMS}, ensure_ascii=False))
        if int(typ) in list(range(1, 4)):
            return

    token = request.headers.get('access_token', None)
    try:
        decrypt_text = decryption(token)
        expire = decrypt_text.get("expire")
        if expire < time.time():
            return response.text(json.dumps({"code": c.ERROR_LOGIN_EXPIRED, "message": m.MESSAGE_TOKEN_EXPIRED_ERROR}, ensure_ascii=False))
    except Exception as e:
        return response.text(json.dumps({"code": c.ERROR_ACCESS_ERROR, "message": m.MESSAGE_TOKEN_INVALID_ERROR}, ensure_ascii=False))


def decryption(token: str) -> Any:
    """to decrypt token"""
    if not str: return

    key = base64.b64decode(aes.get("SECRET_KEY"))
    data = base64.b64decode(token)
    iv = data[:16]
    encrypted = data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypt_text = json.loads(unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8"))
    return decrypt_text


