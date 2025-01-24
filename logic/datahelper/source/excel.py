import copy
import os.path
import random
from io import BytesIO
from typing import List, Union, Dict

from conf.parser import conf2Dict
from api.embedding import embeddingDistance
from util.op_thirdparty.fs_minio import download_file_to_memory
from models.base.source import DataSourceBaseModel, SourceNativeConfig

import pandasql
import pandas as pd

MINIO_CONFIG = conf2Dict()['MINIO_CONFIG']
BUCKET_NAMES = MINIO_CONFIG["BUCKET_NAMES"]
USER_FILE_BUCKET = BUCKET_NAMES.get("USER_FILE_BUCKET")


class ExcelSourceParser(DataSourceBaseModel):
    def __init__(self, sourceConfig: SourceNativeConfig):
        super().__init__(sourceConfig)
        self.mapping = self.format()

    def format(self) -> Union[Dict, List]:
        """
        将所有源转换成统一的结构

        :Analysis

        {
            "ConfigId": "4dca195",
            "ConfigName": "层次结构数据.xlsx",
            "GroupList": [
                {
                    "id": "sdN-EQ2j4oUwOKQY8yjwF",
                    "checked": 1,
                    "children": [
                        {
                            "tableName": "数字乡村指数数据",
                            "fieldName": "数字金融基础设施指数"
                        },
                        {
                            "tableName": "中国行政区划",
                            "fieldName": "上级区划代码"
                        }
                    ]
                },
                {
                    "id": "i7celkzhQfwO2tAIeyWjm",
                    "checked": 1,
                    "children": [
                        {
                            "tableName": "数字乡村指数数据",
                            "fieldName": "数字基础设施指数"
                        },
                        {
                            "tableName": "中国行政区划",
                            "fieldName": "上级区划代码"
                        }
                    ]
                },
                {
                    "id": "J8Uqzf1QGRT7fpRgSbjYl",
                    "checked": 0,
                    "children": [
                        {
                            "tableName": "中国行政区划",
                            "fieldName": "上级区划代码"
                        },
                        {
                            "tableName": "数字乡村指数数据",
                            "fieldName": "乡村生活数字化指数"
                        }
                    ]
                }
            ]
        }

        :return
        [
          {                                                                 # db_schema
            "db_id": "car_1",
            "db_schema": [
              {                                                             # table_schema
                "table_name": "continents",
                "data": dataframe,
                "data_name": "df1",
                "column_map": [
                  {
                    "column_name": "id",
                    "column_type": "number",
                    "column_contents": ["1", "2", "3"]
                  },
                  {
                    "column_name": "contents",
                    "column_type": "text",
                    "column_contents": ["test1", "test2", "test3"]
                  }
                ]
              }]
          }
        ]
        """

        # url = S3Bucket().generate_presign_url(path)
        # fileHandler = pd.ExcelFile(url)
        # df = fileHandler.parse(sheet_name)  # TODO: 此处若要存储在云端，则需要该参数

        def get_column_type(column):
            if pd.api.types.is_numeric_dtype(column):
                return "number"
            elif pd.api.types.is_string_dtype(column):
                return "string"
            elif pd.api.types.is_datetime64_any_dtype(column):
                return "datetime"
            else:
                return "unknown"

        filePath = self.Config.Paths
        groupList = self.Config.GroupList
        count = 0
        formatList = list()

        # Checked 0-不勾选 1-勾选
        if not groupList or all(int(item['checked']) == 0 for item in groupList):
            # 处理文件
            for ind, path in enumerate(filePath):
                response = download_file_to_memory(USER_FILE_BUCKET, path)
                excel_file = BytesIO(response.read())
                schema = {"db_id": os.path.basename(path), "db_schema": list(), "fk": list(), "pk": list()}
                all_sheets = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
                # 处理表
                for sheet_name, df in all_sheets.items():
                    _tmpMap = {"table_name": sheet_name, "data": df, "data_name": f"df{count}", "column_map": list()}
                    count += 1
                    for column_name in df.columns:
                        _tmpMap["column_map"].append({
                                "column_name": column_name,
                                "column_type": get_column_type(df[column_name]),
                                "column_contents": df[column_name].drop_duplicates().tolist()
                            })
                    schema["db_schema"].append(_tmpMap)
                formatList.append(schema)
            return formatList
        else:
            for ind, path in enumerate(filePath):
                response = download_file_to_memory(USER_FILE_BUCKET, path)
                excel_file = BytesIO(response.read())
                schema = {"db_id": os.path.basename(path), "db_schema": list(), "fk": list(), "pk": list()}
                all_sheets = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
                for groupInd, groupItem in enumerate([item for item in groupList if item['checked'] == 1]):
                    # 确保tableName都在打开的sheet中
                    children = groupItem["children"]
                    sheet_name = children[0]["sheetName"]
                    if len(children) == 1:
                        df = all_sheets["sheet_name"]
                    else:
                        df = all_sheets[children[0]["sheetName"]]
                        firstName = children[0]["fieldName"]
                        # 将组拼接成完整df
                        for i, item in enumerate(children[1:]):
                            fieldName = item['fieldName']
                            df_rest_item = all_sheets[item['sheetName']]
                            df = pd.merge(df, df_rest_item, on=firstName, how='outer') if firstName == fieldName else \
                                pd.merge(df, df_rest_item, left_on=firstName, right_on=fieldName, how='outer')
                            sheet_name += "_" + item['sheetName']
                        sheet_name += "_" + str(random.randint(0, 5))

                    _tmpMap = {"table_name": sheet_name, "data": df, "data_name": f"df{count}", "column_map": list()}
                    count += 1
                    for column_name in df.columns:
                        _tmpMap["column_map"].append({
                            "column_name": column_name,
                            "column_type": get_column_type(df[column_name]),
                            "column_contents": df[column_name].drop_duplicates().tolist()
                        })
                    schema["db_schema"].append(_tmpMap)
                formatList.append(schema)

        return formatList


class ExcelSourceExecutor:
    def __init__(self, sourceConfig: SourceNativeConfig):
        self.parser = ExcelSourceParser(sourceConfig)
        self.mapping = self.parser.mapping

    def getDFMap(self, mapping: List = None):
        """
        从解析结构中获得df map
        :param mapping: 须符合format()返回结构
        :return df map

        [{'table_name': '终端库存数据', 'data':  df , 'data_name': 'df8'}]
        """
        if not mapping: mapping = self.mapping
        _tmp_schema = list()
        for dbSchema in mapping:
            dbSchema = dbSchema["db_schema"]
            for tableSchema in dbSchema:
                _tmp_schema.append({
                    "table_name": tableSchema["table_name"],
                    "data": tableSchema["data"],
                    "data_name": tableSchema["data_name"],
                })
        return _tmp_schema

    def getTableMap(self, mapping: List = None):
        """
        从解析结构中获得table-col map
        :param mapping: 须符合format()返回结构
        :return table-col map

        [
        {'国内零售': {'df_name': 'df0', 'cols': ['品牌', '车型']}},
        {'国内零售目标': {'df_name': 'df1', 'cols': ['品牌', '车型']}}
        ]
        """
        if not mapping: mapping = self.mapping
        _tmp_schema = list()
        for dbSchema in mapping:
            dbSchema = dbSchema["db_schema"]
            for tableSchema in dbSchema:
                tableName = tableSchema.get("table_name")
                _table_map = {tableName: {"df_name": tableSchema.get("data_name"), "cols": list()}}
                for colMap in tableSchema.get("column_map"):
                    _table_map[tableName]["cols"].append(colMap.get("column_name"))
                _tmp_schema.append(_table_map)

        return _tmp_schema

    def getFewShotTopK(self, topK: Union[int, str] = "all"):
        """
        从解析结构中保留column_contents TopK
        :param topK: 保留的topK
        :return format格式返回结构
        """
        if topK == "all": return self.mapping
        if isinstance(topK, int):
            mapping = copy.deepcopy(self.mapping)
            for source_ind, source_schema in enumerate(mapping):
                db_schema = source_schema["db_schema"]
                for table_schema in db_schema:
                    cols_schema = table_schema["column_map"]
                    for col_schema in cols_schema:
                        col_schema["column_contents"] = col_schema["column_contents"][:topK]
            return mapping
        return self.mapping

    def getRecall(self, query: str) -> List:
        """
        对表、列进行召回，通过embedding的方式
        :params query： 问题
        """
        # 列召回
        tableMap = self.getTableMap()
        cols = [i for item in tableMap for key, value in item.items() for i in value["cols"]]
        colRecall = embeddingDistance(query, list(set(cols)))
        timeRecall = embeddingDistance("时间", cols)
        recall = list(set(colRecall["topk_tags"] if len(colRecall["topk_tags"]) <= 5 else colRecall["topk_tags"][:7] \
                 + timeRecall["topk_tags"] if len(timeRecall["topk_tags"]) <= 5 else timeRecall["topk_tags"][:7]))

        mapping = copy.deepcopy(self.mapping)
        for source_ind, source_schema in enumerate(mapping):
            db_schema = source_schema["db_schema"]
            for table_schema in db_schema:
                cols_schema = table_schema["column_map"]
                del_col_inds = list()
                for col_ind, col_schema in enumerate(cols_schema[1:]):
                    # 如果col_name存在query，将该字段保留
                    if col_schema["column_name"] in query or col_schema["column_name"] in recall:
                        continue
                    # 如果内容字段存在，则保留该字段
                    isColValExist = False
                    for col_val in col_schema["column_contents"]:
                        if str(col_val) in query:
                            isColValExist = True
                            break
                    if not isColValExist:
                        del_col_inds.append(col_ind + 1)

                table_schema["column_map"] = [
                    item for ind, item in enumerate(table_schema["column_map"])
                    if ind not in del_col_inds
                ]
        return mapping

    def testConnect(self):
        """检测表路径是否存在于该路径下/后期可换成检测S3是否存在该桶"""
        pass

    def execute(self):
        """
        在相应数据源类型中执行SQL
        """

        return pandasql.sqldf


if __name__ == "__main__":
    e = ExcelSourceExecutor(
        SourceNativeConfig(
            "excel",
            [r"C:\Users\zqsu3\Desktop\working\aiagent\storage\iflytek\扁平结构数据样例.xlsx"],
        ),
    )
    recall = e.getRecall("帮我统计风险等级是高，计收月份不同的的客户数量，并以基础饼图展示")
    # print(recall)
    # print(e.getTableMap(recall))
    # print(e.getDFMap(recall))
