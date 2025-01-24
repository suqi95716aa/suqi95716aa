import json
import aiohttp
from typing import List

from conf.parser import conf2Dict

KIMI = conf2Dict()['KIMI']


async def gen_params_with_files(files: List, question: str):
    """
    通过appid和用户的提问来生成请参数
    """
    KIMI_URL = KIMI.get("KIMI_API")
    KIMI_ACCESS_TOKEN = KIMI.get("KIMI_ACCESS_TOKEN")

    headers = {
        'Authorization': f'Bearer {KIMI_ACCESS_TOKEN}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }
    files_params = [{"type": "file", "file_url": {"url": file}} for file in files]
    payload = {
        "model": "kimi",
        "messages": [
            {
                "role": "user",
                "content": [
                    *files_params,
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ],
        "use_search": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(KIMI_URL, headers=headers, data=json.dumps(payload)) as response:
            content = json.loads(await response.text())
            if content.get("code"):
                raise Exception(content.get("message"))
            else:
                return content["choices"][0]["message"]["content"]


class KimiChat:
    async def _call(self, files: List, question: str) -> str:
        content = await gen_params_with_files(files, question)
        return content

if __name__ == "__main__":

    import asyncio

    asyncio.run(KimiChat()._call({}))


