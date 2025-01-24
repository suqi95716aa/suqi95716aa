import json

from util.str import recovery

import sqlalchemy_jsonfield
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, DATETIME, Integer

Base = declarative_base()


class KnowledgeInfo(Base):
    """知识存储信息"""
    __tablename__ = "knowledge_info"
    uid = Column(VARCHAR(7), comment='用户id')
    kbid = Column(VARCHAR(7), comment='知识库id')
    kid = Column(VARCHAR(7), primary_key=True, comment='知识id')
    kName = Column(VARCHAR(30), comment='知识名称（文件名称）')
    ktype = Column(Integer, comment='知识类型, e.g. 0 文章问答 1 QA问答 2 表格问答 3 URL')
    kPath = Column(VARCHAR(90), comment='文件路径')
    kconfig = Column(
        sqlalchemy_jsonfield.JSONField(
            enforce_string=True,
            enforce_unicode=True,
            json=json,
        ), comment='存储不同类型的相关配置，根据不同文章后缀和类型，如csv存储分隔符，pdf、txt等文本存储chunk size、overlap')
    kCreateTime = Column(DATETIME, comment='创建时间')
    kUpdateTime = Column(DATETIME, comment='更新时间')
    kDeleteTime = Column(DATETIME, default=None, comment='删除时间')

    def to_dict(self):
        return {
            "KID": self.kid,
            "KName": recovery(self.kName),
            "FakeKName": self.kName,
            "KType": self.ktype,
            "KConfig": self.kconfig,
            "KCreateTime": self.kCreateTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.kCreateTime, str) else self.kCreateTime,
            "KUpdateTime": self.kUpdateTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.kUpdateTime, str) else self.kUpdateTime,
        }

    def __repr__(self):
        return f"KnowledgeInfo({dir(self)})"


if __name__ == "__main__":
    from conf.parser import conf2Dict
    from sqlalchemy import create_engine

    DB_CONF = conf2Dict()['DB_CONFIG']
    engine = create_engine(f"mysql+pymysql://{DB_CONF.get('MYSQL_USERNAME')}:{DB_CONF.get('MYSQL_PASSWORD')}@{DB_CONF.get('MYSQL_HOST')}:{DB_CONF.get('MYSQL_PORT')}/{DB_CONF.get('MYSQL_DATABASE')}?charset=utf8mb4")
    Base.metadata.create_all(engine)

    engine = create_engine('mysql+pymysql://user:password@localhost/dbname')

