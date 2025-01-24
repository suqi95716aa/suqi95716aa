# Neo4j is an open-source graph database designed to manage and query complex relationship data.
# It provides a unified solution for various application domains, including social network analysis, recommendation systems, fraud detection, and network management.
# Key features include high performance, scalability, flexibility, and ease of use.
# Neo4j supports ACID transactions and offers a powerful query language, Cypher, which allows developers to express complex graph queries intuitively.
# It can easily integrate with popular data processing frameworks and storage systems, supporting drivers for multiple programming languages.
# Neo4j official documentation: https://neo4j.com/docs/

from service.ragfusion.graphstore.neo4j_store import Neo4JStorage


def create_g_conn() -> Neo4JStorage:
    """
    Guide to difference business by some attrs.

    :return:
        `Neo4JStorage`
    """

    return Neo4JStorage()



