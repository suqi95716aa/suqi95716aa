from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph

from service.ragfusion.core.document.document import Document


class GraphState(TypedDict):
    """
    Represents the state of an agent in the conversation.

    Attributes:
        keys: A dictionary where each key is a string and the value is expected to be a list or another structure
              that supports addition with `operator.add`. This could be used, for instance, to accumulate messages
              or other pieces of data throughout the graph.

    :param k: Knowledge instance
    :param k_docs: parent and child docx

    """
    k: Any
    k_docs: List[Document]


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
        "k": k
    }
    return state


async def node_parent_child_docs(state: GraphState) -> GraphState:
    """
    parent and child generation

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (parent and child generation) saved to state.
    """
    print("---NODE GENERATING PARENT AND CHILD DOCUMENTS---", end="\n\n")

    k = state["k"]
    docs = await k.query_content_by_page()
    state["k_docs"] = docs
    return state


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
    workflow.add_node("node_parent_child_docs", node_parent_child_docs)

    # add edge
    workflow.set_entry_point("node_parent_child_docs")

    app = workflow.compile()
    async for output in app.astream(d): pass
    return list(output.values())[0]


