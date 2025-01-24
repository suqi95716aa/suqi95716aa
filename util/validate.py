import random
import re
import uuid


def validate_account(account: str, password: str, phone_number: str) -> bool:
    """

    validate account while register

    :param account:
    :param password:
    :param phone_number:
    :return:
    """
    # 账号规则：6-8位字母和数字组合
    # 密码规则：6-12位，包含大小写字母、数字和特殊字符
    # 手机号规则：1开头，第二位为3、4、5、6、7、8、9，总共11位数字

    if not re.match("^[a-zA-Z0-9]{6,8}$", account) or \
       not re.match("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=])[a-zA-Z0-9@#$%^&+=]{6,12}$", password) or \
       not re.match("^1[3456789]\d{9}$", phone_number):
        return False

    return True


def generate_uid(k: int = 7) -> str:
    """
    generate k uuid code with random

    :param k: random uuid code

    :return:
        `str` code
    """
    return ''.join(random.sample(str(uuid.uuid4()).replace('-', ''), k))


def generate_code(k: int = 4) -> int:
    """
    generate k int code with random

    :return:
        `int` code
    """
    return random.randint(10 ** (k-1), (10 ** k) - 1)




