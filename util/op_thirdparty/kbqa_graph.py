from typing import List, Tuple, Dict, Union

from util.retry import a_retry
from service.ragfusion.core.document.document import Document
from service.ragfusion.graphstore.neo4j_store import Neo4JStorage


@a_retry
async def kbqa_upsert_node(
    gconn: Neo4JStorage,
    entity: Document
) -> bool:
    """
    sync function to insert node.

    :param gconn: Neo4j connection
    :param entity: document entity item

    :return:
        `bool`
    """
    return await gconn.upsert_node(
        entity.page_content,
        entity.metadata
    )


@a_retry
async def kbqa_get_node_by_kid(
    gconn: Neo4JStorage,
    entity: Document
) -> List[Tuple[str, str]]:
    """
    sync function to get entity across kid.

    :param gconn: Neo4j connection
    :param entity: document entity item

    :return:
        `bool`
    """

    return await gconn.iter_node_edges(
        entity.page_content,
        entity.metadata.get("kid")
    )


@a_retry
async def kbqa_get_node_by_kid(
    gconn: Neo4JStorage,
    entity: Document,
    metadata_keys: List = None
) -> List[Tuple[Dict, Dict]]:
    """
    sync function to get entity across kid.

    :param gconn: Neo4j connection
    :param entity: document entity item
    :param metadata_keys: extract key

    :return:
        `List[Tuple[Dict, Dict]]`
    """
    return await gconn.get_node_edges(
        entity.page_content,
        entity.metadata.get("kid"),
        metadata_keys
    )


@a_retry
async def kbqa_get_edge_by_kid(
    gconn: Neo4JStorage,
    src_id: str,
    dest_id: str,
    kid: str
) -> Union[dict, None]:
    """
    sync function to get entity across kid.

    :param gconn: Neo4j connection
    :param src_id: `str`, src entity id
    :param dest_id: `str`, dest entity id
    :param kid: extract key

    :return:
        `List[Tuple[Dict, Dict]]`
    """
    return await gconn.get_edge(src_id, dest_id, kid)


@a_retry
async def kbqa_upsert_edge(
    gconn: Neo4JStorage,
    relationship: Document,
    src_key_name: str = "src_entity",
    dest_key_name: str = "dest_entity",
) -> bool:
    """
    sync function to insert edge.

    :param gconn: Neo4j connection
    :param relationship: document relationship item
    :param src_key_name: extract src id from Document
    :param dest_key_name: extract dest id from Document

    :return:
        `bool`
    """

    src_id = relationship.metadata.get(src_key_name)
    dest_id = relationship.metadata.get(dest_key_name)
    if not (src_id and dest_id): return False

    return await gconn.upsert_edge(
        src_id,
        dest_id,
        relationship.metadata,
        relationship.metadata.get("kid")
    )


@a_retry
async def kbqa_delete_node(
    gconn: Neo4JStorage,
    entity: Document,
):
    """
    sync function to delete node.

    :param gconn: Neo4j connection
    :param entity: document entity item

    :return:
        `bool`
    """

    try:
        node_id = entity.page_content
        kid = entity.metadata.get("kid")
        await gconn.delete_node(node_id, kid)
        return True
    except Exception as e:
        print(f"Error delete node: {e}")
        return False
