import json

import sqlalchemy_jsonfield
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, DATETIME

Base = declarative_base()


class KnowledgeBaseInfo(Base):
    """知识库存储信息"""
    __tablename__ = "knowledge_base_info"
    uid = Column(VARCHAR(7), comment='用户id')
    kbid = Column(VARCHAR(7), primary_key=True, comment='知识库id')
    kbName = Column(VARCHAR(20), comment='知识库名称')
    kbDesc = Column(VARCHAR(200), comment='知识库描述')
    kbLabel = Column(
        sqlalchemy_jsonfield.JSONField(
            enforce_string=True,
            enforce_unicode=True,
            json=json,
        ), comment='知识库相关行业标签')
    kbColor = Column(VARCHAR(12), comment='知识库卡片颜色')
    kbBGImg = Column(VARCHAR(20), comment='知识库卡片背景图案')
    kbCreateTime = Column(DATETIME, comment='创建时间')
    kbUpdateTime = Column(DATETIME, comment='更新时间')
    kbDeleteTime = Column(DATETIME, default=None, comment='删除时间')

    def to_dict(self):
        return {
            "KBID": self.kbid,
            "KBName": self.kbName,
            "KBDesc": self.kbDesc,
            "KBLabel": self.kbLabel,
            "KBColor": self.kbColor,
            "KBBGImg": self.kbBGImg,
            "KBCreateTime": self.kbCreateTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.kbCreateTime, str) else self.kbCreateTime,
            "KBUpdateTime": self.kbUpdateTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.kbUpdateTime, str) else self.kbUpdateTime,
        }


if __name__ == "__main__":
    from conf.parser import conf2Dict
    from sqlalchemy import create_engine

    DB_CONF = conf2Dict()['DB_CONFIG']
    engine = create_engine(f"mysql+pymysql://{DB_CONF.get('MYSQL_USERNAME')}:{DB_CONF.get('MYSQL_PASSWORD')}@{DB_CONF.get('MYSQL_HOST')}:{DB_CONF.get('MYSQL_PORT')}/{DB_CONF.get('MYSQL_DATABASE')}?charset=utf8mb4")
    Base.metadata.create_all(engine)

    engine = create_engine('mysql+pymysql://user:password@localhost/dbname')

