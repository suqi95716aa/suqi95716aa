
import json
import requests

from conf.parser import conf2Dict

THREE_PARTY_API = conf2Dict()['EMBEDDING']
TOKEN = "b8d1e618e3e973b4d7b67fe3467ef43c"


def embeddingQuery(query: str) -> list:
    """将问题向量化
    :param query: 待匹配的问题
    """

    response = requests.request(
        method="POST",
        url=THREE_PARTY_API["BGE-EMBEDDING"],
        headers={
            "Content-Type": "application/json",
            "token": TOKEN
        },
        data=json.dumps({"query": query})
    )
    return json.loads(response.content)["emb"]


def embeddingDistance(query: str, similarity: list) -> list:
    """给定问题和列表，查询topk
    :param query: 待匹配的问题
    :param similarity: 相似的问题组
    """
    response = requests.request(
        method="POST",
        url=THREE_PARTY_API["BGE-DISTANCE"],
        headers={
            "Content-Type": "application/json",
            "token": TOKEN
        },
        data=json.dumps({"query": query, "cols": similarity})
    )
    return json.loads(response.content)

if __name__ == "__main__":
    print(embeddingQuery("123"))






