from dataclasses import dataclass, field


class CollectionBaseMeta:
    pass


@dataclass
class IVFFLATIndexMeta:
    """记录向量数据库相关索引信息"""
    index_type: str = "IVF_FLAT"    # 基于量化的索引，场景召回率和速度要求高
    metric_type: str = "IP"     # 采用余弦相似度创建索引
    params: dict = field(default_factory=lambda: {"nlist": 20})
    field_name: str = ""


@dataclass
class FieldsMeta:
    consistency_level: str = "Eventually"   # 一致性等级，这里采用最终一致性
    fields: list = field(default_factory=lambda: [])
    description: str = ""


@dataclass
class ConnectionMeta:
    host: str = ""
    port: str = ""
    account: str = ""
    password: str = ""
    collection_name: str = ""
    alias: str = ""


@dataclass
class CollectionsMeta(CollectionBaseMeta):
    index_meta: IVFFLATIndexMeta = field(default=IVFFLATIndexMeta())
    fields_meta: FieldsMeta = field(default=FieldsMeta())
    conn_meta: ConnectionMeta = field(default=ConnectionMeta())







