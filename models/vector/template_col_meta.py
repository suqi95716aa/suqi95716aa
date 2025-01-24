from pymilvus import FieldSchema, DataType

from conf.parser import conf2Dict
from models.base.source_vector import CollectionsMeta, FieldsMeta, IVFFLATIndexMeta, ConnectionMeta

BGE_DIM = 1024
OPENAI_DIM = 1563

DB_CONF = conf2Dict()['MILVUS_CONFIG']


template = CollectionsMeta(
    IVFFLATIndexMeta(
        index_type="IVF_FLAT",
        metric_type="IP",
        params={"nlist": 20},
        field_name="query_vec"
    ),
    FieldsMeta(
        consistency_level="Eventually",
        fields=[
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=5, is_primary=True),
            FieldSchema(name="table_id", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="sql", dtype=DataType.VARCHAR, max_length=400),
            FieldSchema(name="query", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="query_vec", dtype=DataType.FLOAT_VECTOR, dim=BGE_DIM),
        ],
        description="A query-sql template"
    ),
    ConnectionMeta(
        host=DB_CONF.get("host"),
        port=DB_CONF.get("port"),
        account=DB_CONF.get("account"),
        password=DB_CONF.get("password"),
        collection_name=DB_CONF["COLLECTIONS"]["col_name"],
        alias="default"
    )
)

