from typing import List, Any, Union, Dict

import pymysql

from models.base.source import DataSourceBaseModel, SourceDatabaseConfig


class MySQLSourceParser(DataSourceBaseModel):
    def __init__(self, Config: Union[SourceDatabaseConfig]):
        super().__init__(Config)
        self.testConnectInner()
        # self.mapping = self.format()

    def __del__(self):
        """销毁链接"""
        print("__del__ execute")
        self.cursor.close()
        self.conn.close()

    def testConnectInner(self):
        """创建连接"""
        self.conn = pymysql.connect(
            host=self.Config.Host,
            port=self.Config.Port,
            user=self.Config.User,
            password=self.Config.Password,
            database=self.Config.Database,
            charset=self.Config.Charset
        )
        self.cursor = self.conn.cursor()

    @classmethod
    def testConnectOutter(cls, config: SourceDatabaseConfig) -> bool:
        """供外部直接调用的测试连接方法"""
        try:
            t_conn = pymysql.connect(
                host=config.Host,
                port=config.Port,
                user=config.User,
                password=config.Password,
                database=config.Database,
                charset=config.Charset
            )
            t_conn.close()
            return True
        except Exception as e:
            print(str(e))
            return False

    # def getTableInfoMap(self) -> Dict:
    #     """获取所有表名和列名映射关系"""
    #     self.cursor.execute("SHOW TABLES")
    #     tables = self.cursor.fetchall()
    #
    #     _tmp_all_map = dict()
    #     for table in tables:
    #         self.cursor.execute(f"SHOW COLUMNS FROM {table[0]}")
    #         columns = self.cursor.fetchall()
    #         colsname = [column[0] for column in columns]
    #         _tmp_all_map[table[0]] = colsname
    #
    #     return {self.Config.Database: _tmp_all_map}


class MysqlSourceExecutor:
    def __init__(self, sourceConfig: Union[SourceDatabaseConfig]):
        self.parser = MySQLSourceParser(sourceConfig)
        self.cursor = self.parser.cursor

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
            "db_id": self.parser.Config.Database,
            "db_schema": list(),
            "pk": list(),
            "fk": list()
        }

        # get all db schema mappings
        self.cursor.execute("SHOW TABLES;")
        tables = self.cursor.fetchall()

        for table in tables:
            tablename = table[0]
            mapping = {"table_name": tablename, "column_map": list()}
            # get all columns relative
            self.cursor.execute(f"SHOW COLUMNS FROM {tablename}")
            columns = self.cursor.fetchall()

            for column in columns:
                columnInfo = {"column_name": column[0], "column_type": column[1], "column_contents": []}
                unique = self.getUniqueValues(tablename, column[0])
                columnInfo["column_contents"] = unique
                mapping["column_map"].append(columnInfo)
            schema["db_schema"].append(mapping)

        # get all primary key relative
        for table in tables:
            table_name = table[0]
            self.cursor.execute(f"SHOW KEYS FROM {table_name} WHERE Key_name = 'PRIMARY'")
            primary_key = self.cursor.fetchone()
            if primary_key:
                schema["pk"].append({"table_name": table_name, "column_name": primary_key[4]})

        for table in tables:
            table_name = table[0]
            self.cursor.execute(f"SHOW CREATE TABLE {table_name}")
            ddl = self.cursor.fetchone()[1]

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


if __name__ == "__main__":
    with MySQLSourceParser(
            SourceDatabaseConfig(
                Host="172.30.94.173",
                Port=3306,
                User="root",
                Password="*&T3*1(%imk@VB",
                Database="datahelper",
                Charset="utf8mb4"
            ),
            Label="MySQL"
    ) as e:
        res = e.format()
        print(res)
