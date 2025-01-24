from dataclasses import dataclass
from typing import Union

import numpy as np


@dataclass
class StorageNameSpace:
    namespace: str
    global_config: dict

    async def index_done_callback(self):
        """commit the storage operations after indexing"""
        pass

    async def query_done_callback(self):
        """commit the storage operations after querying"""
        pass


@dataclass
class BaseGraphStorage(StorageNameSpace):
    async def has_node(self, node_id: str, kid: str) -> bool:
        raise NotImplementedError

    async def has_edge(self, source_node_id: str, target_node_id: str, kid: str) -> bool:
        raise NotImplementedError

    async def node_degree(self, node_id: str, kid: str) -> int:
        raise NotImplementedError

    async def edge_degree(self, src_id: str, tgt_id: str, kid: str) -> int:
        raise NotImplementedError

    async def get_node(self, node_id: str, kid: str) -> Union[dict, None]:
        raise NotImplementedError

    async def get_edge(
        self, source_node_id: str, target_node_id: str, kid: str
    ) -> Union[dict, None]:
        raise NotImplementedError

    async def get_node_edges(
        self, source_node_id: str, kid: str
    ) -> Union[list[tuple[str, str]], None]:
        raise NotImplementedError

    async def upsert_node(self, node_id: str, node_data: dict[str, str]):
        raise NotImplementedError

    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ):
        raise NotImplementedError

    async def delete_node(self, node_id: str, kid: str):
        raise NotImplementedError

    async def embed_nodes(self, algorithm: str) -> tuple[np.ndarray, list[str]]:
        raise NotImplementedError("Node embedding is not used in lightrag.")
