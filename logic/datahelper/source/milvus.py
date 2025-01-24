import random

from api.embedding import embeddingQuery
from models.vector.template_col_meta import template
from models.base.source_vector import CollectionBaseMeta, CollectionsMeta

from pymilvus import (
    connections,
    utility,
    CollectionSchema,
    Collection,
)
from pymilvus.orm.search import SearchResult

import pandas as pd
import numpy as np
from loguru import logger


class VectorParser:
    def __new__(cls, VectorMetaItem: CollectionsMeta, *args, **kwargs):
        """检查参数是否完整"""
        if not isinstance(VectorMetaItem, CollectionBaseMeta): return None
        try:
            ins = super().__new__(cls)
            ins.connName = str(random.randint(1000, 9999))
            connections.connect(
                host=VectorMetaItem.conn_meta.host,
                port=VectorMetaItem.conn_meta.port,
                account=VectorMetaItem.conn_meta.account,
                password=VectorMetaItem.conn_meta.password,
                alias=ins.connName
            )
            ins.conn = connections
            return ins

        except Exception:
            return None

    def __del__(self):
        if self.isConnActivate():
            self.conn.disconnect(self.connName)

    def __init__(self, VectorMetaItem: CollectionsMeta):
        self.indexMeta = VectorMetaItem.index_meta
        self.fieldsMeta = VectorMetaItem.fields_meta
        self.connMeta = VectorMetaItem.conn_meta

        # 检查集合是否创建
        if not self._getCollection():
            self._createCollection()

        # 检查索引是否创建
        if not self._isIndexExist():
            self._createIndex()
        self.collection.load()

    def isConnActivate(self) -> bool:
        """判断连接是否活跃"""
        return True if \
            any(alias == self.connName for alias, _ in self.conn.list_connections()) \
            else False

    def isCollectionExist(self) -> bool:
        """判断集合是否存在"""
        return utility.has_collection(self.connMeta.collection_name, using=self.connName)

    def _getCollection(self) -> bool:
        """获取集合对象"""
        try:
            if self.isCollectionExist():
                self.collection = Collection(self.connMeta.collection_name, using=self.connName)
                return True
            else:
                return False
        except Exception as e:
            logger.info(f"获取集合对象getCollection错误：{e}")
            return False

    def _createCollection(self) -> bool:
        """创建集合对象"""
        try:
            if not self.isCollectionExist():
                schema = CollectionSchema(
                    fields=self.fieldsMeta.fields,
                    description=self.fieldsMeta.description
                )
                self.collection = Collection(
                    name=self.connMeta.collection_name,
                    schema=schema,
                    consistency_level=self.fieldsMeta.consistency_level,
                    using=self.connName
                )
                return True
            else:
                return False
        except Exception as e:
            logger.info(f"创建集合时createCollection错误：{e}")
            return False

    def _isIndexExist(self) -> bool:
        return self.collection.has_index()

    def _createIndex(self):
        """创建索引"""
        index = {
            "index_type": self.indexMeta.index_type,
            "metric_type": self.indexMeta.metric_type,
            "params": self.indexMeta.params
        }
        self.collection.create_index(
            field_name=self.indexMeta.field_name,
            index_params=index
        )

    def _embeddingQuery(self, query: str) -> list:
        """将问题向量化
        :param query: 待匹配的问题
        """
        return embeddingQuery(query)

    def _normalizeVector(self, vector):
        """归一化"""
        return vector / np.linalg.norm(vector)

    def insert(self, entities: list) -> bool:
        """插入数据
        :param entities: 格式如下

        Exeample:
        2000条样例数据插入
         [
          [i for i in range(2000)],
          [str(i) for i in range(2000)],
          [i for i in range(10000, 12000)],
          [[random.random() for _ in range(2)] for _ in range(2000)],
        ]
        """
        try:
            self.collection.insert(entities)
            self.collection.flush()
            return True
        except Exception as error:
            logger.info(f"insert entities error: {error}")
            return False

    def queryVec(self,
                 query: str,
                 search_params: dict,
                 anns_field: str,
                 outputs: list,
                 limit: int = 10
                 ) -> SearchResult:
        """
        向量查询

        :param query: 查询问题
        :param search_params: 查询参数
        :param anns_field: 查询向量字段
        :param limit: 查询限制个数
        :param outputs: 输出字段
        :return:

        Exeample:
            search_params = {
            "metric_type": "IP",  # Cosine Similar
            "params": {"nprobe": 10}
        }

            # 执行查询
            results = collection.search(
                data=[f.tolist()],
                anns_field="query_vec",
                limit=5,
                param=search_params,
                output_fields=["query"]
            )
        """
        vec = self._embeddingQuery(query)
        nvec = self._normalizeVector(vec)

        results = self.collection.search(
            data=[nvec.tolist()],
            anns_field=anns_field,
            limit=limit,
            param=search_params,
            output_fields=outputs
        )
        return results


# TODO: 获取所有数据





