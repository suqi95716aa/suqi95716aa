import os
from typing import List, Any, Union, Dict

import sqlite3
from sqlite3 import OperationalError

from models.base.source import DataSourceBaseModel, SourceDatabaseConfig


class SQLiteSourceParser(DataSourceBaseModel):
    def connect(self, config: SourceDatabaseConfig = None):
        """创建连接"""
        return sqlite3.connect(
            database=SourceDatabaseConfig.Database
        ) if config else sqlite3.connect(
            database=self.Config.Database
        )

    def close(self):
        """销毁链接"""
        self.cursor.close()
        self.conn.close()

    def __enter__(self):
        """创建时检测、创建连接"""
        isConnSuccess = self.testConnect()
        if not isConnSuccess:
            raise Exception("连接失败")

        self.mapping = self.format()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动销毁连接"""
        self.close()

    def getTableInfoMap(self) -> Dict:
        """获取所有表名和列名映射关系"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()

        _tmp_all_map = dict()
        for table in tables:
            self.cursor.execute(f"SHOW COLUMNS FROM {table[0]}")
            columns = self.cursor.fetchall()
            colsname = [column[0] for column in columns]
            _tmp_all_map[table[0]] = colsname

        return {self.Config.Database: _tmp_all_map}

    def getUniqueValues(self, tableName: str, columnName: str, topk: int = 3) -> List[Any]:
        """获取某表某列所有唯一值"""
        self.cursor.execute(f"SELECT DISTINCT {columnName} FROM {tableName} LIMIT {topk}")
        unique_values_tuple = self.cursor.fetchall()
        unique_values = [value[0] for value in unique_values_tuple]
        return unique_values

    def execute(self, sql: str) -> Union[List[Any], None]:
        """执行SQL"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def testConnect(self, config: SourceDatabaseConfig = None) -> bool:
        """测试连接"""
        try:
            self.conn = self.connect(config)
            self.cursor = self.conn.cursor()
            return True
        except OperationalError as error:
            return False

    def format(self) -> Dict:
        """
        将所有源转换成统一的结构

        :return:
        [
          {
            "db_id": "car_1",
            "db_schema": [
              {
                "table_name": "continents",
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
              }],
            "pk": [
              {
                "table_name": "continents",
                "column_name": "contid"
              },
              {
                "table_name": "countries",
                "column_name": "countryid"
              }
            ],
            "fk": [
              {
                "source_table_name": "countries",
                "source_column_name": "continent",
                "target_table_name": "continents",
                "target_column_name": "contid"
              }

            ]
          }
            ]
        """
        schema = {
            "db_id": os.path.basename(self.Config.Database),
            "db_schema": list(),
            "pk": list(),
            "fk": list()
        }

        # get all db schema mappings
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()

        for table in tables:
            tablename = table[0]
            mapping = {"table_name": tablename, "column_map": list()}
            # get all columns relative
            self.cursor.execute(f"PRAGMA table_info({tablename});")
            columns = self.cursor.fetchall()

            for column in columns:
                columnInfo = {"column_name": column[1], "column_type": column[2],
                              "column_contents": self.getUniqueValues(tablename, column[1])}
                mapping["column_map"].append(columnInfo)
            schema["db_schema"].append(mapping)

        # get all primary key relative
        for table in tables:
            table_name = table[0]
            self.cursor.execute(f"PRAGMA index_list({table_name});")
            primary_key = self.cursor.fetchone()

            if primary_key:
                schema["pk"].append({"table_name": table_name, "column_name": primary_key[4]})

        # get all foreign key relative
        for table in tables:
            table_name = table[0]
            self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '{table_name}';")
            ddl = self.cursor.fetchone()[0]

            if "FOREIGN KEY" in ddl:
                fk_definitions = ddl.split("FOREIGN KEY (")[1:]
                for fk_def in fk_definitions:
                    fk_info = {
                        "source_table_name": table_name,
                        "source_column_name": "",
                        "target_table_name": "",
                        "target_column_name": ""
                    }

                    # 提取源列名和目标表名、列名
                    source_column, target = fk_def.split(") REFERENCES ")
                    fk_info["source_column_name"] = source_column.strip("`")
                    target_table, target_column = target.split("(")
                    fk_info["target_table_name"] = target_table.strip("`")
                    fk_info["target_column_name"] = target_column.split(")")[0].strip("`")
                    schema["fk"].append(fk_info)
        return schema


if __name__ == "__main__":
    with SQLiteSourceParser(
            SourceDatabaseConfig(Database=r"C:\Users\zqsu3\Desktop\car_1.sqlite"),
            Label="SQLite"
    ) as e:
        res = e.format()
        print(res)
