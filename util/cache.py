def sms_key_buildup(typ: int, phone: str) -> str:
    """
    build sms key depend on business

    :param typ: 1 - register, 2 - login, 3 - password recovery, 4 - phone update
    :param phone: user phone
    :return:
    """
    SMS_TYP_MAPS = {1: "reg", 2: "login", 3: "passRec"}
    return f"sms_{SMS_TYP_MAPS[typ]}_{phone}"
