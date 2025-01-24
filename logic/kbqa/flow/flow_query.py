import re
import copy
import json
from typing import Dict, TypedDict
from collections import OrderedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import sessionmaker

from logic.kbqa.core.recall import *
from logic.kbqa.model.graph import to_get_entity_pairs_by_kid, to_get_edge_by_kid
from logic.kbqa.model.knowledge import Knowledge
from logic.kbqa.model.knowledgebase import KnowledgeBase
from logic.screen.screen import Screen
from logic.user.user_kb import UserForKnowledgeBase
from models.graph.connect import create_g_conn
from prompt.g_kbqa import *
from util.str import replace_keyword, build_col_name
from models.llm import *


MAX_HINTS = 3


class GraphState(TypedDict):
    """
    Represents the state of an agent in the conversation.

    Attributes:
        keys: A dictionary where each key is a string and the value is expected to be a list or another structure
              that supports addition with `operator.add`. This could be used, for instance, to accumulate messages
              or other pieces of data throughout the graph.

    Means when it is first created, it needs to be passed in
    1. query: str
    2. uid: str
    3. sid: str

    Memory now contain keys:
    1. ind: int    # autoregression state
    2. uid: str    # user id
    3. sid: str    # screen id

    Hidden Structure Description:
    1. subquery(Dict)：{ind(int): {subquery(str), retrievers(List), answser(str)}}

    """
    # instance
    screen: Screen
    query: str
    subqueries: OrderedDict
    kbsmap: Dict[KnowledgeBase, List[Knowledge]]
    # state
    memory: Dict


async def init(
        conn: sessionmaker,
        uid: str,
        sid: str,
        query: str
) -> Dict:
    """
    Initial state

    Args:
        conn (sessionmaker): database connetion
        uid (str): user id
        sid (str): screen id
        query (str): user query

    Returns:c
        dict: New value saved to question.
    """

    # get screen item
    screen = Screen(conn)
    screeninfo = await screen.get(uid=uid, screenid=sid)
    if not screeninfo: return {}

    # get kb items
    kbids = screeninfo.screenQAConfig["KBIDS"]
    user = UserForKnowledgeBase(conn)
    await user.get(uid=uid)
    kbs = await user.flush(kbids)
    if not kbs: return {}

    # get k for every kb
    kbsmap = {kb: await kb.flush() for kb in kbs}
    if not sum([len(ks) for kb, ks in kbsmap.items()]): return {}

    state: Dict[str, Any] = {
        "query": query,
        "kbsmap": kbsmap,
        "screen": screen,
        "memory": {"uid": uid, "sid": sid, "ind": 0}
    }
    return state


# Node
async def node_subquery(state: GraphState) -> GraphState:
    """
    Complexity problem analysis.
    Split the problem into a sequence of sub problems.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value saved to question.
    """
    print("---NODE TRANSFORM QUERY INTO SUB---", end="\n\n")
    query = state["query"]

    # generate answer
    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_sub_prompt_generator_zh),
        input_keys=[
            {"keyword": "query", "text": query},
        ]
    )
    # ans = await spark._call(prompt=input, temperature=0.2)
    # ans = '["不使用检索的基线和使用检索的基线有什么区别", "不使用检索的基线是什么", "不使用检索的基线和使用检索的基线在实际应用中有何区别"]'
    ans = '["费用是按什么方式进行的?"]'

    # extract answer to json
    pattern = r'\[.*?\]'
    match = re.search(pattern, ans)
    sub_lst = json.loads(match.group()) if match else [query]
    state["subqueries"] = OrderedDict((ind, {"subquery": item, "retrievers": None, "entities": None, "edges": None, "generation": None}) for ind, item in enumerate(sub_lst))
    return state


async def node_retrieve(state: GraphState) -> Optional[GraphState]:
    """
    Retrieve documents

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New key added to state, documents, that contains documents.
    """
    print("---NODE STARTING TO RETRIEVE---", end="\n\n")
    kbs = state["kbsmap"]
    uid = state["memory"]["uid"]
    ind = state["memory"]["ind"]
    hins = int(getattr(state["screen"], "RelevantHits"))
    sim_threshold = float(getattr(state["screen"], "SimilarityThreshold"))
    kids = [k.kid for kb, ks in kbs.items() for k in ks]
    if not kids: return None

    if ind == 0:
        subquery = state["subqueries"][ind]["subquery"]
    else:
        subquery = "\t".join(state["subqueries"][ind]["subquery"] for ind in range(ind-1, -1, -1))

    gconn = create_g_conn()
    mconn = create_v_conn(col_name=build_col_name(["v", uid]))

    # retrieve text vector
    # step 1 - query text vector retrieve
    vec_search = await text_similarity_search_with_score(
        mconn=mconn,
        kids=kids,
        query=subquery,
        k=min(hins, MAX_HINTS),
        param=mconn.search_params,
        SimilarityThreshold=sim_threshold
    )
    # step 2 - bm25 retrieve
    bm_search = await bm25_search(
        mconn=mconn,
        kids=kids,
        query=subquery,
        k=min(hins, MAX_HINTS)
    )
    # step 3 - deduplicate and rerank
    dedocs = {doc.metadata.get("pk"): doc for doc in vec_search + bm_search}
    if not list(dedocs.values()): return None
    rerank_res = await bge_reranker_with_score(subquery, list(dedocs.values()), int(hins))

    # retrieve entity
    entity_pairs = []
    mconn = create_v_conn(col_name=build_col_name(["entities", uid]))
    entity_search = await entity_similarity_search_with_score(
        mconn=mconn,
        kids=kids,
        query=subquery,
        k=5,
        param=mconn.search_params,
        SimilarityThreshold=sim_threshold
    )
    for doc in entity_search:
        doc_entity = await to_get_entity_pairs_by_kid(gconn, doc, ["entity_name", "description"])
        if doc_entity:
            entity_pairs.extend(doc_entity)
    print(entity_pairs)

    # retrieve relationship
    relationship_pairs = []
    mconn = create_v_conn(col_name=build_col_name(["relationships", uid]))
    entity_search = await entity_similarity_search_with_score(
        mconn=mconn,
        kids=kids,
        query=subquery,
        k=5,
        param=mconn.search_params,
        SimilarityThreshold=sim_threshold
    )
    for doc in entity_search:
        doc_entity = await to_get_edge_by_kid(
            gconn,
            doc.metadata.get("src_entity"),
            doc.metadata.get("dest_entity"),
            doc.metadata.get("kid")
        )
        if doc_entity:
            relationship_pairs.append(doc_entity)
    print(relationship_pairs)

    state["subqueries"][ind]["retrievers"] = rerank_res
    state["subqueries"][ind]["entities"] = entity_pairs
    state["subqueries"][ind]["edges"] = relationship_pairs

    return state


async def node_grade_documents(state: GraphState) -> GraphState:
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New key added to state, filtered_documents, that contains relevant documents.
    """
    print("---NODE GRADE DOCMENTS---", end="\n\n")
    ind = state["memory"]["ind"]
    subqueries = state["subqueries"].get(ind)

    filtered_docs = []
    subquery = subqueries["subquery"]
    for doc in subqueries["retrievers"]:
        input = replace_keyword(
            prompts=copy.deepcopy(kbqa_grade_doc_zh),
            input_keys=[
                {"keyword": "query", "text": subquery},
                {"keyword": "context", "text": doc.page_content}
            ]
        )

        ans = await spark._call(prompt=input, temperature=0.2)
        if ans == "yes":
            filtered_docs.append(doc)
        else:
            continue

    state["subqueries"][ind]["retrievers"] = filtered_docs
    return state


async def node_generate(state: GraphState) -> GraphState:
    """
    Generate answer

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New key added to state, generation, that contains generation.
    """
    print("--- NODE GENERATE---", end="\n\n")
    ind = state["memory"]["ind"]
    docs = state["subqueries"][ind]["retrievers"]
    entity_pairs = state["subqueries"][ind]["entities"]
    relationship_pairs = state["subqueries"][ind]["edges"]
    subquery = state["subqueries"][ind]["subquery"]
    context = "\n\n".join([doc.page_content for doc in docs])

    # concat pre context
    if ind == 0:
        pre_context = ""
    else:
        pre_context = "\n\n".join([state["subqueries"][ind]["generation"] for ind in range(ind-1, -1, -1)])

    # generate answer
    entities = [entity for entity_pair in entity_pairs for entity in entity_pair]
    entities_input = ""
    for entity in entities:
        entities_input += f'Entity name: {entity.get("entity_name")}, which description is {entity.get("description")} \n'

    relationship_input = ""
    for relationship in relationship_pairs:
        relationship_input += f'Source entity name: {relationship.get("src_entity")}, dest entity name: {relationship.get("dest_entity")}, which description between them is {relationship.get("description")}'

    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_generate_zh),
        input_keys=[
            {"keyword": "pre_context", "text": pre_context},
            {"keyword": "query", "text": subquery},
            {"keyword": "entities", "text": entities_input},
            {"keyword": "relationships", "text": relationship_input},
            {"keyword": "context", "text": context}
        ]
    )
    print(f"IM input：{input}")
    ans = await spark._call(prompt=input, temperature=0.2)
    print(f"IM ans：{ans}")
    state["subqueries"][ind]["generation"] = ans
    return state


def node_prepare_for_final_grade(state: GraphState) -> GraphState:
    """
    Stage for final grade, passthrough state.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        state (dict): The current state of the agent, including all keys.
    """

    print("---NODE FINAL GRADE---", end="\n\n")
    return state


def node_prepare_for_end_query(state: GraphState) -> GraphState:
    """
    Stage for end query, passthrough state.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        state (dict): The current state of the agent, including all keys.
    """

    print("---NODE END QUERY---", end="\n\n")
    return state


async def node_transform_query(state: GraphState) -> GraphState:
    """
     Transform the query to produce a better question. (Hyde)

     Args:
         state (dict): The current state of the agent, including all keys.

     Returns:
         dict: New value saved to question.
     """
    print("---TRANSFORM QUERY---", end="\n\n")
    kbs = state["kbsmap"]
    uid = state["memory"]["uid"]
    ind = state["memory"]["ind"]
    hins = int(getattr(state["screen"], "RelevantHits"))
    sim_threshold = float(getattr(state["screen"], "SimilarityThreshold"))
    gconn = create_g_conn()
    mconn = create_v_conn(col_name=build_col_name(["v", uid]))
    kids = [k.kid for kb, ks in kbs.items() for k in ks]
    if not kids: return None

    if ind == 0:
        subquery = state["subqueries"][ind]["subquery"]
    else:
        subquery = "\t".join(state["subqueries"][ind]["subquery"] for ind in range(ind - 1, -1, -1))

    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_hyde),
        input_keys=[
            {"keyword": "query", "text": subquery}
        ]
    )
    hypothesis_passage = await spark._call(prompt=input, temperature=0.2)
    print(f"Im hypothesis passage：{hypothesis_passage}")

    # query vector and bm25
    vec_search = await text_similarity_search_with_score(
        mconn=mconn,
        kids=kids,
        query=hypothesis_passage,
        k=min(hins, MAX_HINTS),
        param=mconn.search_params,
        SimilarityThreshold=sim_threshold
    )
    bm_search = await bm25_search(
        kids=kids,
        query=hypothesis_passage,
        k=min(hins, MAX_HINTS)
    )

    # deduplicate and rerank
    dedocs = {doc.metadata.get("pk"): doc for doc in vec_search + bm_search}
    rerank_res = await bge_reranker_with_score(subquery, list(dedocs.values()), int(hins))

    # retrieve entity
    entity_pairs = []
    mconn = create_v_conn(col_name=build_col_name(["entities", uid]))
    entity_search = await entity_similarity_search_with_score(
        mconn=mconn,
        kids=kids,
        query=subquery,
        k=5,
        param=mconn.search_params,
        SimilarityThreshold=sim_threshold
    )
    for doc in entity_search:
        doc_entity = await to_get_entity_pairs_by_kid(gconn, doc, ["entity_name", "description"])
        if doc_entity:
            entity_pairs.extend(doc_entity)

    # retrieve relationship
    relationship_pairs = []
    mconn = create_v_conn(col_name=build_col_name(["relationships", uid]))
    entity_search = await entity_similarity_search_with_score(
        mconn=mconn,
        kids=kids,
        query=subquery,
        k=5,
        param=mconn.search_params,
        SimilarityThreshold=sim_threshold
    )
    for doc in entity_search:
        doc_entity = await to_get_edge_by_kid(
            gconn,
            doc.metadata.get("src_entity"),
            doc.metadata.get("dest_entity"),
            doc.metadata.get("kid")
        )
        if doc_entity:
            relationship_pairs.append(doc_entity)

    state["subqueries"][ind]["retrievers"] = rerank_res
    state["subqueries"][ind]["entities"] = entity_pairs
    state["subqueries"][ind]["edges"] = relationship_pairs

    return state


# Edge
def edge_decide_to_generate(state: GraphState) -> str:
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New key added to state, filtered_documents, that contains relevant documents.
    """

    print("---EDGE DECIDE TO GENERATE---", end="\n\n")
    ind = state["memory"]["ind"]
    filtered_docs = state["subqueries"][ind]["retrievers"]
    if not filtered_docs:
        print("---DECISION: TRANSFORM QUERY---")
        return "node_transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "node_generate"


async def edge_grade_generation_v_documents(state: GraphState) -> str:
    """
    Determines whether the generation is grounded in the document.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        str: Binary decision score.
    """
    print("---EDGE GRADE GENERATION vs DOCUMENTS---", end="\n\n")
    ind = state["memory"]["ind"]
    docs = state["subqueries"][ind]["retrievers"]
    generation = state["subqueries"][ind]["generation"]
    context = "\n\n".join([doc.page_content for doc in docs])

    # generate yes or no
    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_generate_v_docs),
        input_keys=[
            {"keyword": "documents", "text": context},
            {"keyword": "generation", "text": generation}
        ]
    )
    grade = await spark._call(prompt=input, temperature=0.2)

    if "yes" in grade.lower():
        print("---DECISION: SUPPORTED, MOVE TO FINAL GRADE---")
        return "supported"
    else:
        print("---DECISION: NOT SUPPORTED, GENERATE AGAIN---")
        return "not supported"


async def edge_grade_generation_v_question(state):
    """
    Determines whether the generation addresses the question.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        str: Binary decision score.
    """

    print("---EDGE GRADE GENERATION vs QUESTION---", end="\n\n")
    ind = state["memory"]["ind"]
    subquery = state["subqueries"][ind]["subquery"]
    generation = state["subqueries"][ind]["generation"]

    # generate yes or no
    input = replace_keyword(
        prompts=copy.deepcopy(kbqa_generate_v_query),
        input_keys=[
            {"keyword": "query", "text": subquery},
            {"keyword": "generation", "text": generation}
        ]
    )
    grade = await spark._call(prompt=input, temperature=0.2)

    if "yes" in grade.lower():
        print("---DECISION: USEFUL---")
        return "useful"
    else:
        print("---DECISION: NOT USEFUL---")
        return "not useful"


async def edge_decide_to_end(state):
    """
    Determines whether loop is over.

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        str: Binary decision score.
    """
    print("---EDGE DECIDE TO END---", end="\n\n")
    ind = state["memory"]["ind"]
    subqueries = state["subqueries"]

    if ind == len(subqueries) - 1:
        print(f"Current ind：{ind + 1} equal to {len(subqueries)}")
        return "endloop"
    else:
        print(f"Current ind：{ind + 1} not equal to {len(subqueries)}")
        state["memory"]["ind"] += 1
        return "not endloop"


async def flow(
    conn: sessionmaker,
    uid: str,
    sid: str,
    query: str
):
    """
    build node and edge

    :param conn: database connection
    :param uid: user id
    :param sid: screen id
    :param query: user query

    :return:
    """
    d = await init(conn, uid, sid, query)
    if not d: return {}

    workflow = StateGraph(GraphState)

    # add node
    workflow.add_node("node_subquery", node_subquery)
    workflow.add_node("node_retrieve", node_retrieve)
    workflow.add_node("node_grade_documents", node_grade_documents)
    workflow.add_node("node_generate", node_generate)
    workflow.add_node("node_prepare_for_final_grade", node_prepare_for_final_grade)  # passthrough
    workflow.add_node("node_prepare_for_end_query", node_prepare_for_end_query)  # passthrough
    workflow.add_node("node_transform_query", node_transform_query)

    # add edge
    workflow.set_entry_point("node_subquery")
    workflow.add_edge("node_subquery", "node_retrieve")
    workflow.add_edge("node_retrieve", "node_grade_documents")
    workflow.add_edge("node_transform_query", "node_retrieve")
    workflow.add_conditional_edges(
        "node_grade_documents",
        edge_decide_to_generate,
        {
            "node_generate": "node_generate",
            "node_transform_query": "node_transform_query",
            # "node_transform_query": END,
        },
    )
    workflow.add_conditional_edges(
        "node_generate",
        edge_grade_generation_v_documents,
        {
            "supported": "node_prepare_for_final_grade",
            "not supported": "node_generate",
        },
    )
    workflow.add_conditional_edges(
        "node_prepare_for_final_grade",
        edge_grade_generation_v_question,
        {
            "useful": "node_prepare_for_end_query",
            "not useful": "node_transform_query",
            # "not useful": END,
        },
    )
    workflow.add_conditional_edges(
        "node_prepare_for_end_query",
        edge_decide_to_end,
        {
            "endloop": END,
            "not endloop": "node_retrieve",
        },
    )

    app = workflow.compile()
    async for output in app.astream(d):
        print(output)
        # for key, value in output.items():
        #     print(f"Output from node '{key}':")
        #     print("---")
        #     print(value)
        # print("\n---\n")

