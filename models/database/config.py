import os
import json

import sqlalchemy_jsonfield
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, DATETIME

from models.base.source import SourceNativeConfig
from logic.datahelper.source.excel import ExcelSourceExecutor

Base = declarative_base()


class ConfigInfo(Base):
    """场景信息"""
    __tablename__ = "config_info"
    uid = Column(VARCHAR(7), comment='用户id')
    configId = Column(VARCHAR(10), primary_key=True, comment='配置id')
    label = Column(VARCHAR(10), comment='配置标签')
    config = Column(
        sqlalchemy_jsonfield.JSONField(
            enforce_string=True,
            enforce_unicode=True,
            json=json,
        ), comment='配置信息')
    createTime = Column(DATETIME, comment='创建时间')
    updateTime = Column(DATETIME, comment='更新时间')
    deleteTime = Column(DATETIME, default=None, comment='删除时间')

    def to_dict(self):
        if self.label.lower() == "excel":
            ExcelConfig = ExcelSourceExecutor(SourceNativeConfig(self.label, [self.config.get("Paths")]))

            def transform_data(data_list):
                transformed_data = []
                for item in data_list:
                    cols_info = [{"colName": col, "colType": str(item['data'][col].dtype)} for col in item['data'].columns]
                    transformed_item = {
                        "sheetName": item['table_name'],
                        "colsInfo": cols_info
                    }
                    transformed_data.append(transformed_item)
                return transformed_data

            return {
                "Label": self.label,
                "ConfigId": self.configId,
                "SourceName": os.path.basename(self.config.get("Paths")),
                "Data": transform_data(ExcelConfig.getDFMap()),
                "CreateTime": self.createTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.createTime, str) else self.createTime,
                "UpdateTime": self.updateTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.updateTime, str) else self.updateTime,
            }

    def to_dict_error(self):
        """错误时返回的结构体"""
        return {
            "Label": self.label,
            "ConfigId": self.configId
        }


if __name__ == "__main__":
    import time
    import datetime
    config_info = ConfigInfo(
        Uid="1234567",
        ConfigId="config_001",
        Label="Excel",
        Config={"Paths": r"C:\Users\zqsu3\Desktop\excel表格数据源\AI助手测试数据集-sql汇总.xlsx"},
        CreateTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        UpdateTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        DeleteTime=None
    )

    print(config_info.to_dict_excel())

