from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, INT

Base = declarative_base()


class TemplateInfo(Base):
    """场景信息"""
    __tablename__ = "template_info"
    Tid = Column(INT, primary_key=True, comment='模板id')
    TableName = Column(VARCHAR(10), comment='表格名称')
    TableCols = Column(VARCHAR(100), comment='表格列')

    def to_dict(self):
        return {
            "Tid": self.Tid,
            "TableName": self.TableName,
            "TableCols": self.TableCols,
        }

