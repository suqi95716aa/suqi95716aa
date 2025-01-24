import os
from typing import TypedDict, List, Dict, Any, Union

from langgraph.graph import StateGraph

from router import KBQA_STORAGE_PATH
from logic.kbqa.model.graph import to_graph_text, to_graph_restore
from logic.kbqa.vector import to_vector_text, to_mconn_switch, to_vector_restore
from service.ragfusion.core.document.document import Document
from util.op_thirdparty.common import insert
from util.op_thirdparty.fs_minio import move_file
from util.str import build_col_name, rename, get_fs_path

# 先判断是否需要聚合（目前做到能插入即可，即不更新）
USER_FILE_BUCKET = os.environ["USER_FILE_BUCKET"]


class GraphState(TypedDict):
    """
    Represents the state of an agent in the conversation.

    Attributes:
        keys: A dictionary where each key is a string and the value is expected to be a list or another structure
              that supports addition with `operator.add`. This could be used, for instance, to accumulate messages
              or other pieces of data throughout the graph.

    Args:
        k (Knowledge): Knowledge instance
        texts (List[Document]): text documents
        entities (List[Union[Dict, Document]]): entity documents
        relationships (List[Union[Dict, Document]]): relationship documents

    """
    k: Any
    texts: List[Document]
    entities: List[Union[Dict, Document]]
    relationships: List[Union[Dict, Document]]
    inserted: bool


async def init(
    k: Any,
    texts: List[Document],
    entities: List[Union[Dict, Document]],
    relationships: List[Union[Dict, Document]]
):
    """
    Initial state

    Args:
        k (Knowledge): Knowledge instance
        texts (List[Document]): text documents
        entities (List[Union[Dict, Document]]): entity documents
        relationships (List[Union[Dict, Document]]): relationship documents

    Returns:
        dict: New value to save knowledge chunk state.
    """

    state: Dict[str, Any] = {
        "k": k,
        "texts": texts,
        "entities": entities,
        "relationships": relationships,
        "inserted": False
    }
    return state


async def node_combine_if_exist(state: GraphState) -> GraphState:
    """
    combine every item if exist

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (after combining) saved to state.
    """
    print("---NODE COMBINE IF EXIST---", end="\n\n")


    # Step 1, combine same entities or relationship
    def combine_entity_then_upsert(
            entities: List[Dict],
            **kwargs
    ) -> List[Document]:
        """
        transfer dict format type to document

        :param entities: entity dicts
        :param kwargs: other keys will be updated to metadata

        :return:
            `List[Document]`, result of combine
        """
        _d: Dict[str, Document] = {}
        for entity in entities:
            entity_name = entity["entity_name"]
            description = entity["description"]

            if entity_name not in _d:
                page_content = entity_name
                metadata = {"entity_name": entity_name, "description": description}
                if kwargs: metadata.update(kwargs)
                _d[entity_name] = Document(page_content=page_content, metadata=metadata)
            else:
                desc = _d[entity_name].metadata.get("description")
                desc += "<SEP>" + desc
                _d[entity_name].metadata["description"] = desc

        return list(_d.values())

    def combine_relationship_then_upsert(
            relationships: List[Dict],
            **kwargs
    ) -> List[Document]:
        """
        transfer dict format type to document

        :param relationships: relationship dicts
        :param kwargs: other keys will be updated to metadata

        :return:
            `List[Document]`, result of combine
        """
        _d: Dict[str, Document] = {}
        for relationship in relationships:
            src_entity = relationship["src_entity"]
            dest_entity = relationship["dest_entity"]
            description = relationship["description"]

            if str(src_entity) + str(dest_entity) not in _d:
                page_content = description
                metadata = {"src_entity": src_entity, "dest_entity": dest_entity, "description": description}
                if kwargs: metadata.update(kwargs)
                _d[str(src_entity) + str(dest_entity)] = Document(page_content=page_content, metadata=metadata)
            else:
                desc = _d[str(src_entity) + str(dest_entity)].metadata.get("page_content")
                desc += "<SEP>" + desc
                _d[str(src_entity) + str(dest_entity)].metadata["description"] = desc

        return list(_d.values())

    k = state.get("k")
    entities = state.get("entities")
    relationships = state.get("relationships")
    state["entities"] = combine_entity_then_upsert(entities, kid=k._k.kid, kbid=k._k.kbid)
    state["relationships"] = combine_relationship_then_upsert(relationships, kid=k._k.kid, kbid=k._k.kbid)

    # Step 2, combine with every same entity and relationship in vdb or gdb
    # TODO:
    return state


async def node_upsert(state: GraphState) -> GraphState:
    """
    upsert into vdb

    Args:
        state (dict): The current state of the agent, including all keys.

    Returns:
        dict: New value (upsert into vdb) saved to state.
    """
    print("---NODE UPSERT---", end="\n\n")
    TEXT_METADATA_NAMES = ["parent_id", "child_id", "sequence", "kbid", "kid"]
    ENTITY_METADATA_NAMES = ["kbid", "kid", "description"]
    RELATIONSHIP_METADATA_NAMES = ["src_entity", "dest_entity", "kbid", "kid"]

    k = state.get("k")
    texts = state.get("texts")
    entities = state.get("entities")
    relationships = state.get("relationships")

    inserted = False
    pks_t = pks_e = pks_r = None
    permanent_file_path = ""
    temporary_file_path = ""
    try:
        # text insert to vdb
        pks_t = await to_vector_text(
            mconn=k.mconn,
            docs=texts,
            partition_name=k._k.kid,
            meta_col_name=TEXT_METADATA_NAMES
        )

        # switch entity conn
        to_mconn_switch(
            mconn=k.mconn,
            docs=entities,
            col_name=build_col_name(["entities", k._k.uid])
        )

        # entity insert to vdb
        pks_e = await to_vector_text(
            mconn=k.mconn,
            docs=entities,
            partition_name=k._k.kid,
            meta_col_name=ENTITY_METADATA_NAMES
        )

        # switch relationship conn
        to_mconn_switch(
            mconn=k.mconn,
            docs=relationships,
            col_name=build_col_name(["relationships", k._k.uid])
        )

        # relationship insert to vdb
        pks_r = await to_vector_text(
            mconn=k.mconn,
            docs=relationships,
            partition_name=k._k.kid,
            meta_col_name=RELATIONSHIP_METADATA_NAMES
        )

        # entity insert to gdb
        await to_graph_text(k.gconn, entities, relationships)

        # do move file from temp dir to the permanent user fs space
        fake_filename = rename(k._k.kName)
        temporary_file_path = k._k.kPath
        permanent_file_path = get_fs_path(k._k.uid, k._k.kbid, KBQA_STORAGE_PATH, fake_filename)
        if not move_file(
            source_bucket_name=USER_FILE_BUCKET,
            source_file_path=temporary_file_path,
            dest_bucket_name=USER_FILE_BUCKET,
            dest_file_path=permanent_file_path,
        ):
            raise Exception("Move file failed")

        k._k.kName = fake_filename
        k._k.kPath = permanent_file_path
        inserted = await insert(k.session, k._k)
        if not inserted: raise Exception("Database insertion failed")
        state["inserted"] = inserted

    except Exception:
        # restore text
        if pks_t and texts:
            to_mconn_switch(
                mconn=k.mconn,
                docs=texts,
                col_name=build_col_name(["v", k._k.uid])
            )
            await to_vector_restore(k.mconn, [int(pk) for pk in pks_t], partition_name=k._k.kid)
        # restore entities
        if pks_e and entities:
            to_mconn_switch(
                mconn=k.mconn,
                docs=entities,
                col_name=build_col_name(["entities", k._k.uid])
            )
            await to_vector_restore(k._k.mconn, [int(pk) for pk in pks_e], partition_name=k._k.kid)
        # restore relationships
        if pks_r and relationships:
            to_mconn_switch(
                mconn=k.mconn,
                docs=relationships,
                col_name=build_col_name(["relationships", k._k.uid])
            )
            await to_vector_restore(k.mconn, [int(pk) for pk in pks_r], partition_name=k._k.kid)
        # restore graph
        if entities:
            await to_graph_restore(k.gconn, entities)

        if inserted:
            move_file(
                source_bucket_name=USER_FILE_BUCKET,
                source_file_path=permanent_file_path,
                dest_bucket_name=USER_FILE_BUCKET,
                dest_file_path=temporary_file_path,
            )

    return state


async def flow(
    k: Any,
    texts: List[Document],
    entities: List[Document],
    relationships: List[Document]
):
    """
    build node and edge

    Args:
        k (Knowledge): Knowledge instance
        texts (List[Document]): text documents
        entities (List[Document]): entity documents
        relationships (List[Document]): relationship documents

    :return:
    """
    d = await init(k, texts, entities, relationships)
    if not d: return {}

    workflow = StateGraph(GraphState)

    # add node
    workflow.add_node("node_combine_if_exist", node_combine_if_exist)
    workflow.add_node("node_upsert", node_upsert)

    # add edge
    workflow.set_entry_point("node_combine_if_exist")
    workflow.add_edge("node_combine_if_exist", "node_upsert")

    app = workflow.compile()
    async for output in app.astream(d): pass
    return list(output.values())[0]

