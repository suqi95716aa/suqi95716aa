# import time
# import uuid
# from elasticsearch import Elasticsearch
#
# from conf.parser import conf2Dict
#
# DB_CONF = conf2Dict()['ES_CONFIG']
# es = Elasticsearch(hosts=[f"{DB_CONF.get('ES_HOST')}:{DB_CONF.get('ES_PORT')}"])
#
# print(DB_CONF)
# print(es)
# # 查看有哪些索引
# es_indexes = es.indices.get_alias().keys()
# for ind_name in es_indexes:
#     if "online-ins" not in ind_name:
#         print(ind_name)
# # 查看某个索引map
# response = es.indices.get_mapping(index="tableinfo")
# print(response)
# print(response["tableinfo"]['mappings'])
# 插入数据
# doc = {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': 'your_tablename',
#     'tablecols': ['class', 'name']
# }
# res = es.index(index='tableinfo', id=doc['id'], body=doc)
# print(res)

# 批量写入数据
# 国内零售目标('品牌', '车型', '战区', '省份', '城市', '计划月份', '销量目标')
# 国际批售目标('品牌', '车型', '市场', '国家', '计划月份', '销量目标')
# 国内零售('品牌', '车型', '车款', '战区', '省份', '城市', '专营店', '销售时间', '销量')
# 国际批售('品牌', '车型', '市场', '国家', '销售时间', '销量')
# 市场数据('车企', '品牌', '车型', '市场分类', '能源类型', '省份', '销售日期', '销售周', '上险量')
# 订单数据('品牌', '车型', '省份', '城市', '专营店', '订单类型', '订单日期', '留存时长', '订单量')
# 生产数据('品牌', '车型', '基地', '工厂', '生产日期', '产量', '工厂区域', '工厂国家')
# 生产计划('品牌', '车型', '基地', '工厂', '计划日期', '产量计划')
# 终端库存数据('品牌', '车型', '省份', '城市', '库存日期', '库存量')
# t_info = [
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '国内零售目标',
#     'tablecols': ['品牌', '车型', '战区', '省份', '城市', '计划月份', '销量目标']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '国际批售目标',
#     'tablecols': ['品牌', '车型', '市场', '国家', '计划月份', '销量目标']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '国内零售',
#     'tablecols': ['品牌', '车型', '车款', '战区', '省份', '城市', '专营店', '销售时间', '销量']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '国际批售',
#     'tablecols': ['品牌', '车型', '市场', '国家', '销售时间', '销量']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '市场数据',
#     'tablecols': ['车企', '品牌', '车型', '市场分类', '能源类型', '省份', '销售日期', '销售周', '上险量']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '订单数据',
#     'tablecols': ['品牌', '车型', '省份', '城市', '专营店', '订单类型', '订单日期', '留存时长', '订单量']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '生产数据',
#     'tablecols': ['品牌', '车型', '基地', '工厂', '生产日期', '产量', '工厂区域', '工厂国家']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '生产计划',
#     'tablecols': ['品牌', '车型', '基地', '工厂', '计划日期', '产量计划']
# },
# {
#     'id': str(uuid.uuid4())[5:10],
#     'tablename': '终端库存数据',
#     'tablecols': ['品牌', '车型', '省份', '城市', '库存日期', '库存量']
# }
# ]
# from elasticsearch import helpers
# helpers.bulk(es, t_info, index="tableinfo")

# 按条件删除document
# query = {"query": {"match": {"id": "f33-2"}}}
# es.delete_by_query(index='tableinfo', body=query)

# 查询某索引下全部记录
# results = es.search(index="tableinfo", body={"query": {"match_all": {}}})
# print(results)
# print(results.get("hits").get("hits"))
# res = results.get("hits").get("hits")
# for item in res:
#     source = item.get("_source")
#     print(source.get("id"))
#     print(source.get("tablename"))
#     print(source.get("tablecols"))
#     print(type(source.get("tablecols")))
#

import functools

from util.encryption import decryption, mid_encryption

inds = 1
for ind in range(inds-1, -1, -1):
    print(ind)
