import json
from typing import Union

from conf.parser import conf2Dict

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


SMS_ACCESS = conf2Dict()['SMS']


def create_sms_client() -> Dysmsapi20170525Client:
    """
    Initial Alibaba SMS service client

    :return: Client
    :throws Exception
    """

    # Project code leak will lead to AccessKey leak, and truly thread everything resource of account.
    # We suggest you use the way of STS which will more safety, and more auth way please refer to: https://help.aliyun.com/document_detail/378659.html。
    config = open_api_models.Config(
        access_key_id=SMS_ACCESS.get("ACCESS_KEY_ID"),
        access_key_secret=SMS_ACCESS.get("ACCESS_KEY_SECRET")
    )
    # Endpoint refer to: https://api.aliyun.com/product/Dysmsapi
    config.endpoint = SMS_ACCESS.get("END_POINT")
    return Dysmsapi20170525Client(config)


sms_client = create_sms_client()


async def a_send_sms(phone: str, code: Union[str, int]) -> bool:
    """
    send SMS code to phone

    :param phone: user phone
    :param code: verify code

    :return
        `bool` send code status
    """
    send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
        phone_numbers=phone,
        sign_name=SMS_ACCESS.get("SIGN_NAME"),
        template_code=SMS_ACCESS.get("TEMPLATE_CODE"),
        template_param=json.dumps({"code": str(code)})
    )
    try:
        res = await sms_client.send_sms_with_options_async(send_sms_request, util_models.RuntimeOptions())
        if res.status_code == 200 and res.body.code == "OK":
            return True
        return False

    except Exception as error:
        UtilClient.assert_as_string(error.message)
        return False



