import asyncio
import hmac
import json
import base64
import hashlib
import datetime
import os

import websocket
import _thread as thread
from typing import Optional, List, Mapping, Any, Union
from time import mktime
from datetime import datetime
from urllib.parse import urlparse
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time



class Ws_Param(object):
    # 初始化
    def __init__(self):
        pass

    # 生成url
    def create_url(self, request_url, method, api_key, api_secret):
        u = urlparse(request_url)
        host = u.hostname
        path = u.path
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        # date = "Thu, 12 Dec 2019 01:57:27 GMT"
        signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
        signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        values = {
            "host": host,
            "date": date,
            "authorization": authorization
        }

        return request_url + "?" + urlencode(values)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    ws.content = ""
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, question=ws.question, temperature=ws.temperature))
    ws.send(data)


# 收到websocket消息的处理
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        if code == 10013:   # ForbidRequest
            ws.content = "已为您找到对应的知识片段，但非常抱歉，由于相关法律法规，无法为您生成答案，请修改您的问题或对相关的文档知识片段进行脱敏，感谢理解。"
        else:
            raise Exception

        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        ws.content += content
        if status == 2:
            ws.close()


def gen_params(appid, question: Union[List, str], temperature: Union[int, float]):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": "generalv3",
                "random_threshold": temperature,
                "max_tokens": 2048,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


class Spark():
    '''
    根据源码解析在通过LLMS包装的时候主要重构两个部分的代码
    _call 模型调用主要逻辑,输入问题，输出模型相应结果
    _identifying_params 返回模型描述信息，通常返回一个字典，字典中包括模型的主要参数
    '''
    SPARK_APPID = os.environ["SPARK_APPID"]
    SPARK_API_KEY = os.environ["SPARK_API_KEY"]
    SPARK_API_SECRET = os.environ["SPARK_API_SECRET"]
    SPARK_URL = os.environ["SPARK_URL"]     # spark官方模型提供api接口
    host = urlparse(SPARK_URL).netloc  # host目标机器解析
    path = urlparse(SPARK_URL).path  # 路径目标解析
    max_tokens = 1024
    temperature = 0

    @property
    def _llm_type(self) -> str:
        # 模型简介
        return "Spark"

    async def _post(self, prompt, temperature):
        # 模型请求响应
        wsParam = Ws_Param()
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url(self.SPARK_URL, "GET", self.SPARK_API_KEY, self.SPARK_API_SECRET)
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_open=on_open)
        ws.appid = self.SPARK_APPID
        ws.question = prompt
        ws.temperature = temperature
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ws.run_forever)
        return ws.content if hasattr(ws, "content") else ""

    async def _call(self, prompt: List, stop: Optional[List[str]] = None, temperature: Union[int, float] = 0.3) -> str:
        # 启动关键的函数
        content = await self._post(prompt, temperature)
        return content

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """
        Get the identifying parameters.
        """
        _param_dict = {
            "url": self.SPARK_URL
        }
        return _param_dict


