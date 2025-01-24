import re
import copy
import json
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import sessionmaker

from models.llm import gpt
from util.str import replace_keyword
# from logic.kbqa.model.knowledge import Knowledge
from service.ragfusion.core.document.document import Document
from prompt.g_kbqa import kbqa_key_categories, kbqa_categories_v_doc, kbqa_entity_abstract
from prompt.p_kbqa_flow_extract_zh import (
    TEMPLATE_DEFAULT_TUPLE_DELIMITER,
    TEMPLATE_DEFAULT_RECORD_DELIMITER,
    TEMPLATE_DEFAULT_COMPLETION_DELIMITER,
    TEMPLATE_DEFAULT_ENTITY_TYPES
)


class GraphState(TypedDict):
    """
    Represents the state of an agent in the conversation.

    Attributes:
        keys: A dictionary where each key is a string and the value is expected to be a list or another structure
              that supports addition with `operator.add`. This could be used, for instance, to accumulate messages
              or other pieces of data throughout the graph.

    :param k: Knowledge instance
    :param k_contents: knowledge content extracted by page (image using ocr)
    :param k_categories: key categories extract from contents

    """
    k: Any
    k_contents: List[Document]
    k_categories: Dict
    # state
    memory: Dict


async def init(
    k: Any
):
    """
    Initial state

    Args:
        k (Knowledge): Knowledge instance

    Returns:
        dict: New value to save knowledge chunk state.
    """
    state: Dict[str, Any] = {
        "k": k,
        "memory": {"uid": k._k.uid, "kid": k._k.kid}
    }
    return state


# Node
async def node_content(state: GraphState) -> GraphState:
    """
    parse knowledge

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (content by page, and its image by ocr) saved to state.
    """
    print("---NODE EXTRACT CONTENT---", end="\n\n")

    k = state["k"]
    state["k_contents"] = await k.query_content_by_page()
    return state


async def node_key_categories(state: GraphState) -> GraphState:
    """
    recognize knowledge categories

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (recognize key categories of file) saved to state.
    """
    print("---NODE EXTRACT KEY CATEGORIES---", end="\n\n")

    # concat page content
    contents = state["k_contents"]
    fcontent = "\n\n".join([f"<page num：{d.metadata['page_num']}> \n {d.page_content}" for d in contents])

    # generate key categories
    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_key_categories),
        input_keys=[
            {"keyword": "text", "text": fcontent},
        ]
    )

    # generate categories
    # state["k_categories"] = {
    #     "合同": "1-8",
    #     "电子回单": "9",
    #     "公众聚集文化经营场所公示": "10",
    #     "微信聊天记录": "11-36",
    #     "解除商铺租赁合同通知": "37-38",
    #     "中国邮政 EMS 快递单": "39-40",
    #     "微信电脑版聊天记录": "41-45"
    # }
    #
#     state["k_categories"] = {
#         "商铺租赁合同": "1-8",
#         "电子回单": "9",
#         "公众聚集文化经营场所公示": "10",
#         "微信聊天记录": "11-36",
#         "解除商铺租赁合同通知": "37-38",
#         "邮寄快递单": "39-40",
#         "律师函": "41-44",
#         "房开给的方案": "45"
# }

    categories = gpt._call(prompt=input, temperature=0.2)
    categories = categories.replace("```json", "")
    categories = categories.replace("```", "")
    state["k_categories"] = json.loads(categories.strip())
    return state


async def node_page_concat(state: GraphState) -> GraphState:
    """
    extract and concat page by categories

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (concat range of page number) saved to state.
    """
    print("---NODE PAGE CONCAT---", end="\n\n")

    def multi_range_process(ranges: str) -> List:
        """
        Process multiple page range

        :param ranges `str`: page ranges

        :return:
            `List`, page number
        """
        matches = re.findall(r'(\d+)-(\d+)', ranges)

        result = []
        for start, end in matches:
            result.extend(range(int(start), int(end) + 1))

        return result

    # concat page content
    contents = state["k_contents"]

    for category, page_range in state["k_categories"].items():
        # if only single page number
        if page_range.isdigit():
            filtered_contents = list(filter(lambda doc: doc.metadata.get("page_num") == int(page_range), contents))
        # if multi page scale
        elif "-" in page_range:
            range_numbers = multi_range_process(page_range)
            filtered_contents = list(filter(lambda doc: int(doc.metadata.get("page_num")) in range_numbers, contents))
        # if error range can not be parse
        else:
            import warnings
            warnings.warn(f'Knowledge <{state["k"]._k.kid}> has error range type {page_range}')
            continue

        # if page over range
        if not filtered_contents:
            import warnings
            warnings.warn(f'Knowledge <{state["k"]._k.kid} - {state["k"]._k.kName}> without page number {page_range}')
            continue

        # concat full relevant document
        fcontent = "\n\n".join([f"<page num：{d.metadata['page_num']}> \n {d.page_content}" for d in filtered_contents])
        state["k_categories"][category] = {
            "kc_fcontent": fcontent,
            "kc_contents": filtered_contents,
            "kc_pages_range": page_range
        }

    return state


async def node_page_entity_abstract(state: GraphState) -> GraphState:
    """
    page entity abstract content (str)

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (page entity abstract content of page number) saved to state.
    """
    print("---NODE ENTITY ABSTRACT---", end="\n\n")

    for category, category_info in state["k_categories"].items():
        # generate key categories
        input = replace_keyword(
            prompts=copy.deepcopy(kbqa_entity_abstract),
            input_keys=[
                {"keyword": "tuple_delimiter", "text": TEMPLATE_DEFAULT_TUPLE_DELIMITER},
                {"keyword": "record_delimiter", "text": TEMPLATE_DEFAULT_RECORD_DELIMITER},
                {"keyword": "completion_definer", "text": TEMPLATE_DEFAULT_COMPLETION_DELIMITER},
                {"keyword": "entity_type", "text": TEMPLATE_DEFAULT_ENTITY_TYPES},
                {"keyword": "title", "text": category},
                {"keyword": "text", "text": category_info["kc_fcontent"]},
            ]
        )
        abstract = gpt._call(prompt=input, temperature=0.2)
        state["k_categories"][category]["kc_entity_abstract"] = abstract

    return state


async def node_page_entity_extract(state: GraphState) -> GraphState:
    """
    page entity extract content (List)

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (page entity extract content of page number) saved to state.
    """
    print("---NODE ENTITY EXTRACT---", end="\n\n")

    def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
        """Split a string by multiple markers"""
        if not markers:
            return [content]
        results = re.split("|".join(re.escape(marker) for marker in markers), content)
        return [r.strip() for r in results if r.strip()]

    def _eliminate_string_by_re_bracket(contents: List[str]) -> List[str]:
        """Split string by re quote"""
        return [
            re.search(r"\((.*)\)", line).group(1)
            for line in contents
            if re.search(r"\((.*)\)", line)
        ]

    def _handle_single_entity_extraction(entity_lines_to_params: List[List]) -> List:
        """
        handle single entity extraction

        :param entity_lines_to_params: every element is entity with type of list
            - example:
            {'src_entity': '"启迪亮张总"', 'dest_entity': '"晨星托育中心糯米姐姐"', 'description': '"双方就合同事宜进行沟通。"'}

        :return:
            `List`, dict of entity
         """

        return [
            {
                "entity_name": entity_list[1],
                "entity_type": entity_list[2],
                "description": entity_list[3],
            }
            for entity_list in entity_lines_to_params
            if len(entity_list) == 4 and entity_list[0] == '"entity"'
        ]

    def _handle_single_relationship_extraction(entity_lines_to_params: List[List]) -> List:
        """
        handle single relationship extraction

        :param entity_lines_to_params: every element is entity with type of list
            - example:
            [['"relationship"', '"卫健委"', '"托育备案"', '"卫健委负责托育备案。"']]

        :return:
            `List`, dict of entity
         """

        return [
            {
                "src_entity": entity_list[1],
                "dest_entity": entity_list[2],
                "description": entity_list[3],
            }
            for entity_list in entity_lines_to_params
            if len(entity_list) == 4 and entity_list[0] == '"relationship"'
        ]

    for category, category_info in state["k_categories"].items():
        abstract = state["k_categories"][category]["kc_entity_abstract"]

        # format entity
        entity_lines_with_bracket = split_string_by_multi_markers(abstract,[TEMPLATE_DEFAULT_RECORD_DELIMITER, TEMPLATE_DEFAULT_COMPLETION_DELIMITER])          # every line with bracket
        entity_lines_without_bracket = _eliminate_string_by_re_bracket(entity_lines_with_bracket)   # every line without bracket (eliminate bracket)
        entity_lines_to_params = [split_string_by_multi_markers(line, [TEMPLATE_DEFAULT_TUPLE_DELIMITER])for line in entity_lines_without_bracket]  # every line to entity params

        # every line to entity and relationship dict
        if_entity = _handle_single_entity_extraction(entity_lines_to_params)
        if_relationship = _handle_single_relationship_extraction(entity_lines_to_params)

        state["k_categories"][category]["entities"] = if_entity
        state["k_categories"][category]["relationship"] = if_relationship

    return state


async def node_transform_categories(state: GraphState) -> GraphState:
    """
     Transform the query to produce a better question. (Hyde)

     Args:
         state (dict): The current state of the agent, including all keys.

     Returns:
         dict: New value saved to question.
     """
    print("---TRANSFORM CATEGORIES---", end="\n\n")


# Edge
async def edge_categories_v_document(state: GraphState) -> str:
    """
    Determines whether the categories addresses the document.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        str: Binary decision score.
    """
    print("---EDGE CATEGORIES vs DOCUMENT---", end="\n\n")
    # concat page content and categories
    contents = state["k_contents"]
    fcontent = "\n\n".join([f"<page num：{d.metadata['page_num']}> \n {d.page_content}" for d in contents])
    categories = state["k_categories"]

    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_categories_v_doc),
        input_keys=[
            {"keyword": "text", "text": fcontent},
            {"keyword": "categories", "text": json.dumps(categories)}
        ]
    )
    grade = gpt._call(prompt=input, temperature=0.2)

    if "yes" in grade.lower():
        print("---DECISION: SUPPORTED, MOVE TO FINAL GRADE---")
        return "supported"
    else:
        print("---DECISION: NOT SUPPORTED, GENERATE AGAIN---")
        return "not supported"


async def flow(
    k: Any
):
    """
    build node and edge

    :param k: Knowledge instance

    :return:
    """
    d = await init(k)
    if not d: return {}

    workflow = StateGraph(GraphState)

    # add node
    workflow.add_node("node_content", node_content)
    workflow.add_node("node_key_categories", node_key_categories)
    workflow.add_node("node_page_concat", node_page_concat)
    workflow.add_node("node_page_entity_abstract", node_page_entity_abstract)
    workflow.add_node("node_page_entity_extract", node_page_entity_extract)

    # add edge
    workflow.set_entry_point("node_content")
    workflow.add_edge("node_content", "node_key_categories")
    workflow.add_edge("node_page_concat", "node_page_entity_abstract")
    workflow.add_edge("node_page_entity_abstract", "node_page_entity_extract")
    workflow.add_conditional_edges(
        "node_key_categories",
        edge_categories_v_document,
        {
            "supported": "node_page_concat",
            "not supported": END,
        },
    )
    app = workflow.compile()
    async for output in app.astream(d): pass

    # # test
    # workflow = StateGraph(GraphState)
    #
    #
    # with open(r"F:\编程项目\backend\aiagent_dev\test\neo4j\book.txt", "r", encoding="utf-8") as f:
    #     data = f.read()
    # d = {
    #     "k_categories":
    #         {
    #             "微信聊天记录":{
    #                  "kc_entity_abstract": data
    #             }
    #         }
    # }
    # workflow.add_node("node_page_entity_extract", node_page_entity_extract)
    # workflow.set_entry_point("node_page_entity_extract")
    #
    # app = workflow.compile()
    # async for output in app.astream(d):
    #     print(output)
    return list(output.values())[0]

if __name__ == "__main__":
    import asyncio

    asyncio.run(flow(1))


