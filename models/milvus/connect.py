#  Milvus is an open-source vector database designed to manage and search massive vector data.
#  It provides a unified solution for AI applications, including neural network, deep learning, and unstructured data search.
#  Key features include high performance, scalability, compatibility, ease of use, and flexibility.
#  It supports a variety of vector data formats and index types, and can be easily integrated with popular AI frameworks and data storage systems.
#
#  Milvus official documentation: https://milvus.io/
import functools

from conf.parser import BASE, INDEX, CONN, COL
from service.ragfusion.vectorstore.milvus import Milvus
from service.ragfusion.embeddings.bge import BGEEmbedding


def create_v_conn(
        kbid: str = None,
        typ: str = None,
        col_name: str = None,
        priority_alias: str = None
) -> Milvus:
    """
    Guide to difference business by some attrs.

    :param kbid: knowledge base id
    :param typ: support `v`(vector)、`edge`、`entity`
    :param col_name: collection name
    :param priority_alias: if input, use this alias priority

    :return:
        `Milvus`
    """
    if typ and typ not in ['v', 'edge', 'entity']:
        raise Exception("Unknown type, only support `v`, `edge`, `entity`")

    # col params
    col_name = col_name if col_name else "_".join([kbid, typ])
    col_desc = COL.get("col_desc")
    rep_num = COL.get("rep_num")
    col_propers = {"collection.ttl.seconds": COL.get("ttl")}

    # conn params
    conn_args = CONN

    # base params
    auto_id = BASE.get("auto_id")
    drop_old = BASE.get("drop_old")
    text = BASE.get("text_field")
    vector = BASE.get("vector_field")
    primary = BASE.get("primary_field")
    metadata = BASE.get("metadata_field")
    consistency = BASE.get("consistency_level")
    partition_key = BASE.get("partition_key_field")

    # index params
    index = {
        "index_type": INDEX.get("index_type"),
        "metric_type": INDEX.get("metric_type"),
        "params": {"nlist": INDEX.get("nlist")}
    }
    search = {
        "metric_type": INDEX.get("metric_type"),
        "params": {"nlist": INDEX.get("nlist")}
    }

    return Milvus(
        embedding_function=BGEEmbedding(),  # embedding
        collection_name=col_name,   # col
        connection_args=conn_args,
        consistency_level=consistency,
        collection_description=col_desc,
        collection_properties=col_propers,
        index_params=index,     # ind and search
        search_params=search,
        auto_id=auto_id,    # field
        drop_old=drop_old,
        priority_alias=priority_alias,
        text_field=text,
        vector_field=vector,
        primary_field=primary,
        metadata_field=metadata,
        partition_key_field=partition_key,
        # partition_names=replica_number,
        replica_number=rep_num,
        timeout=None,
    )





# 在这里组件不同业务


# from service.ragfusion.vectorstore.milvus import Milvus
# from service.ragfusion.embeddings.bge import BGEEmbedding
#
# from conf.parser import conf2Dict
#
# embedding_function = BGEEmbedding()
#
# milvus_config = conf2Dict().get("MILVUS_CONFIG")
# milvus_base_config = milvus_config["BASE"]
# milvus_index_config = milvus_config["INDEX_PARAMS"]
# milvus_conn_config = milvus_config["CONNECTION"]
# milvus_col_config = milvus_config["COLLECTIONS"]
#
# collection_name = milvus_col_config.get("col_name")
# replica_number = milvus_col_config.get("rep_num")
# collection_description = milvus_col_config.get("col_desc")
# collection_properties = {"collection.ttl.seconds": milvus_col_config.get("collection.ttl.seconds")}
# connection_args = milvus_conn_config
# consistency_level = milvus_base_config.get("consistency_level")
# drop_old = milvus_base_config.get("drop_old")
# auto_id = milvus_base_config.get("auto_id")
# primary_field = milvus_base_config.get("primary_field")
# text_field = milvus_base_config.get("text_field")
# vector_field = milvus_base_config.get("vector_field")
# metadata_field = milvus_base_config.get("metadata_field")
# partition_key_field = milvus_base_config.get("partition_key_field")
# index_params = {
#     "index_type": milvus_index_config.get("index_type"),
#     "metric_type": milvus_index_config.get("metric_type"),
#     "params": {"nlist": milvus_index_config.get("nlist")},
# }
# search_params = {
#         "metric_type": milvus_index_config.get("metric_type"),
#         "params": {"nlist": milvus_index_config.get("nlist")}
# }
#
#
#
#
#
#
# milvus_store = Milvus(
#     embedding_function=embedding_function,
#     collection_name=collection_name,
#     collection_description=collection_description,
#     collection_properties=collection_properties,
#     connection_args=connection_args,
#     consistency_level=consistency_level,
#     index_params=index_params,
#     search_params=search_params,
#     drop_old=drop_old,
#     auto_id=auto_id,
#     primary_field=primary_field,
#     text_field=text_field,
#     vector_field=vector_field,
#     metadata_field=metadata_field,
#     partition_key_field=partition_key_field,
#     # partition_names=replica_number,
#     replica_number=replica_number,
#     timeout=None,
# )


