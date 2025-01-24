from openai import AsyncOpenAI
from typing import Optional, List, Union

from conf.parser import conf2Dict

DEEPSEEK = conf2Dict()['DEEPSEEK_OFFICIAL']


async def gen_params_code(question: Union[List, str], temperature=0):
    """
    通过appid和用户的提问来生成请参数
    """
    DEEPSEEK_URL = DEEPSEEK.get("DEEPSEEK_URL")
    DEEPSEEK_API_KEY = DEEPSEEK.get("DEEPSEEK_API_KEY")
    DEEPSEEK_CODE_MODEL_NAME = DEEPSEEK.get("DEEPSEEK_CODE_MODEL_NAME")

    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_URL)
    response = await client.chat.completions.create(
        model=DEEPSEEK_CODE_MODEL_NAME,
        messages=question,
        max_tokens=4096,
        temperature=temperature,
        stream=False
    )
    return response.choices[0].message.content


async def gen_params_chat(question: Union[List, str], temperature=0):
    """
    通过appid和用户的提问来生成请参数
    """
    DEEPSEEK_URL = DEEPSEEK.get("DEEPSEEK_URL")
    DEEPSEEK_API_KEY = DEEPSEEK.get("DEEPSEEK_API_KEY")
    DEEPSEEK_CHAT_MODEL_NAME = DEEPSEEK.get("DEEPSEEK_CHAT_MODEL_NAME")

    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_URL)
    response = await client.chat.completions.create(
        model=DEEPSEEK_CHAT_MODEL_NAME,
        messages=question,
        max_tokens=4096,
        temperature=temperature,
        stream=False
    )
    return response.choices[0].message.content


class DeepSeekCode:
    async def _call(self, prompt: List, stop: Optional[List[str]] = None, temperature: Union[int, float] = 0.2) -> str:
        # 启动关键的函数
        content = await gen_params_code(prompt, temperature)
        return content


class DeepSeekChat:
    async def _call(self, prompt: List, temperature: Union[int, float] = 0.2) -> str:
        # 启动关键的函数
        content = await gen_params_code(prompt, temperature)
        return content
