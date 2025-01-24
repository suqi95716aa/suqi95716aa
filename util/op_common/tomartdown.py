import copy
from typing import Union

from models.llm.spark import Spark
from util.str import replace_keyword
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
from prompt.g_common import common_prompt_markdown_zh


spark = Spark()


async def transfer_answer_markdown(llm: Union[Spark, DeepSeekCode, DeepSeekChat], answer: str) -> str:
    """
    Transfer answer with markdown format

    :params llm：llm to chat
    :params ans：user answer

    :return:
        `str`, str for answer after transfer
    """
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(common_prompt_markdown_zh),
        input_keys=[
            {"keyword": "Question", "text": answer},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    return _tc_1_ans




