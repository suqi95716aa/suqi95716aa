import copy
from typing import Union

from models.llm.spark import Spark
from util.str import replace_keyword
from prompt.g_dh_c3 import c1_prompt_generator_zh

from langchain.llms.base import LLM


def explain(llm: Union[LLM, Spark], question: str = None, indicator: str = None) -> str:
    """
    自定义指标清洗

    :param llm： 用于通信的模型
    :param question: 原始的问题（清洗之后 ）
    :param indicator：生成错误的sql

    :return: 清洗过后的问题
    """
    # 提示词清洗
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(c1_prompt_generator_zh),
        input_keys=[
            {"keyword": "question", "text": question},
            {"keyword": "indicators", "text": indicator},
        ]
    )
    _tc_1_ans = llm._call(prompt=_tc_1_input, temperature=0)
    return _tc_1_ans


if __name__ == "__main__":
    llm = Spark()
    # for _ in range(10):
    print(explain(
        llm=llm,
        question="本月枭龙MAX在北京市的总销量？",
        indicator="总销量等于某个阶段的销量总和"
    ))
