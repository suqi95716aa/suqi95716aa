import re
import copy
from typing import Union, List

from models.llm.spark import Spark
from service.ragfusion.core.document.document import Document
from util.str import replace_keyword
from models.llm.deepseek import DeepSeekCode, DeepSeekChat
from prompt.g_kbqa import kbqa_prompt_answer_generator_zh


async def generate_answer(llm: Union[Spark, DeepSeekCode, DeepSeekChat], question: str, chunks: List[Document]) -> str:
    """
    Generate answer after rerank

    :params llm：llm to chat
    :params question：user's query

    :return: Sequence of intent id
    """
    formatted_text = "\n".join(f"知识片段{i + 1}：{chunk.page_content}" for i, chunk in enumerate(chunks))
    _tc_1_input = replace_keyword(
        prompts=copy.deepcopy(kbqa_prompt_answer_generator_zh),
        input_keys=[
            {"keyword": "Chunks", "text": formatted_text},
            {"keyword": "Question", "text": question},
        ]
    )

    _tc_1_ans = await llm._call(prompt=_tc_1_input, temperature=0.2)
    return _tc_1_ans

import re

# 示例字符串
text = "这是一个示例字符串，包含部分1]和部分2]以及部分3]。"

# 正则表达式
pattern = r'\[.*?\]'

# 使用 re.search 提取第一个匹配的部分
match = re.search(pattern, text)

# 输出结果
if match:
    print(match.group())
else:
    print("未找到匹配的部分")

