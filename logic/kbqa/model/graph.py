from typing import List, Tuple, Dict, Optional, Union

from service.ragfusion.core.document.document import Document
from service.ragfusion.graphstore.neo4j_store import Neo4JStorage
from util.op_thirdparty.kbqa_graph import (
    kbqa_upsert_node,
    kbqa_upsert_edge,
    kbqa_delete_node,
    kbqa_get_edge_by_kid,
    kbqa_get_node_by_kid
)


async def to_graph_text(
        gconn: Neo4JStorage,
        entities: List[Document],
        relationships: List[Document],
) -> bool:
    """
    insert to graph

    :param gconn: Neo4j connection
    :param entities: `List[Document]`, entity documents
    :param relationships: `List[Document]`, relationship documents

    :return:
        `bool`, success or not
    """

    try:
        # upsert entity
        for entity in entities:
            await kbqa_upsert_node(gconn, entity)
        # upsert relationship
        for relationship in relationships:
            await kbqa_upsert_edge(gconn, relationship)
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False


async def to_get_edge_by_kid(
        gconn: Neo4JStorage,
        src_id: str,
        dest_id: str,
        kid: str
) -> Union[dict, None]:
    """
    insert to graph

    :param gconn: Neo4j connection
    :param src_id: `str`, src entity id
    :param dest_id: `str`, dest entity id
    :param kid: extract key

    :return:
        `Union[dict, None]`
    """

    try:
        return await kbqa_get_edge_by_kid(gconn, src_id, dest_id, kid)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


async def to_get_entity_pairs_by_kid(
        gconn: Neo4JStorage,
        doc: Document,
        metadata_keys: List = None
) -> Optional[List[Tuple[Dict, Dict]]]:
    """
    insert to graph

    :param gconn: Neo4j connection
    :param doc: `Document`, entity document
    :param metadata_keys: extract key

    :return:
        `List[Tuple[Dict, Dict]]`
    """

    try:
        return await kbqa_get_node_by_kid(gconn, doc, metadata_keys)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


async def to_graph_restore(
        gconn: Neo4JStorage,
        entities: List[Document],
) -> bool:
    """
    delete graph

    :param gconn: Neo4j connection
    :param entities: `List[Document]`, entity documents

    :return:
        `bool`, success or not
    """

    try:
        for entity in entities:
            await kbqa_delete_node(gconn, entity)
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False






