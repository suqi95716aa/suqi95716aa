import re
import copy
from typing import Union

from models.llm.spark import Spark
from util.str import replace_keyword
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
from prompt.g_kbqa import kbqa_prompt_intent_generator_zh


async def generate_intent(llm: Union[Spark, DeepSeekCode, DeepSeekChat], question: str) -> int:
    """
    Intent to judge the query belongs to

    id of intent type:
    1. Single jump Q&A
    2. Multi jump Q&A
    3. Paragraph Q&A

    :params llm：llm to chat
    :params question：user's query

    :return: Sequence of intent id
    """
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(kbqa_prompt_intent_generator_zh),
        input_keys=[
            {"keyword": "Question", "text": question},
        ]
    )
    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    match = re.search(r'\b([1-3])\b', _tc_1_ans)
    return match.group(1) if match else 2

