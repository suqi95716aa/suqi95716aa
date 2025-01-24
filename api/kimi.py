from typing import Union

from conf.parser import conf2Dict

import aiohttp
from openai import AsyncOpenAI

KIMI = conf2Dict()['KIMI']

client = AsyncOpenAI(
    api_key=KIMI.get("KIMI_ACCESS_KEY"),
    base_url="https://api.moonshot.cn/v1",
)


async def kimi_ocr(id: str) -> Union[None, str]:
    """
    kimi official ocr method

    :param id: file id will be identied

    :return
        `str` result of ocr
    """
    try:
        file_content = (await client.files.content(file_id=id)).text
        return file_content
    except Exception as e:
        return None


async def kimi_upload_file(url: str) -> Union[str, None]:
    """
    kimi official upload file method

    :param path: Path or url

    :return
        `str` uploaded file id,
        `None` upload fail,
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                file_bytes = await response.read()
                file_detail = await client.files.create(file=file_bytes, purpose="file-extract")
                return file_detail.id
    except Exception as e:
        print(e)
        return None


async def kimi_delete_file(id: str) -> bool:
    """
    kimi official delete file method

    :param id: file id will be deleted

    :return
        `bool` delete file success
    """
    try:
        await client.files.delete(file_id=id)
        return True
    except Exception as e:
        return False


async def kimi_file_list():
    file_list = await client.files.list()
    for file in file_list.data:
        print(file.id)  # 查看每个文件的信息
        # await kimi_delete_file(file.id)

    return file_list


if __name__ == "__main__":
    import asyncio

    url = "http://116.205.136.164:9000/a-bucket/%E7%8F%A0%E6%B5%B7%E6%9F%90%E6%9F%90%E7%85%A7%E6%98%8E%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8%E5%86%85%E8%92%99%E5%8F%A4%E6%9F%90%E6%9F%90%E5%BB%BA%E8%AE%BE%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8%E4%BE%B5%E5%AE%B3%E5%A4%96%E8%A7%82%E8%AE%BE%E8%AE%A1%E4%B8%93%E5%88%A9%E6%9D%83%E7%BA%A0%E7%BA%B7%E6%B0%91%E4%BA%8B%E5%86%8D%E5%AE%A1%E6%B0%91%E4%BA%8B%E5%88%A4%E5%86%B3%E4%B9%A6.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=6NDWA93CVVKU17V1T69E%2F20240810%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240810T052207Z&X-Amz-Expires=604800&X-Amz-Security-Token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiI2TkRXQTkzQ1ZWS1UxN1YxVDY5RSIsImV4cCI6MTcyMzMwOTQ5NiwicGFyZW50IjoibWluaW9hZG1pbiJ9.bPq01naxQ5nEyabjVQ8PBPYIxmDD1SD7fMjfgZ4FCJ4taae6kSjyFV7wMiZtSOZRa03epZZczb-nNZGLJfJ6Gg&X-Amz-SignedHeaders=host&versionId=null&X-Amz-Signature=ffcbdbc833551dbd96c4221c1a407001beb4d06ab319ab5bcd70b8208974e947"

    asyncio.run(kimi_upload_file(url))
    #
    # asyncio.run(kimi_file_list())

    # print(asyncio.run(kimi_ocr("cqrf7jilnl95ajqd66fg")))
