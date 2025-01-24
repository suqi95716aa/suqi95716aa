import json

import sqlalchemy_jsonfield
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, DATETIME, SMALLINT

Base = declarative_base()


class ScreenInfo(Base):
    """Object to screen"""
    __tablename__ = "screen_info"
    uid = Column(VARCHAR(15), comment='user id')
    screenId = Column(VARCHAR(10), primary_key=True, comment='screen id')
    screenName = Column(VARCHAR(10), comment='screen name')
    screenDesc = Column(VARCHAR(100), comment='screen description')
    screenType = Column(SMALLINT, comment='flag to screen。 1 - datahelper； 2 - knowledge base')
    screenQAConfig = Column(
        sqlalchemy_jsonfield.JSONField(
            enforce_string=True,
            enforce_unicode=True,
            json=json,
        ), comment='QA config'
    )
    createTime = Column(DATETIME, comment='create time')
    updateTime = Column(DATETIME, default=None, comment='update time')
    deleteTime = Column(DATETIME, default=None, comment='delete time')

    def to_dict(self):
        return {
            "Uid": self.uid,
            "ScreenId": self.screenId,
            "ScreenType": self.screenType,
            "settings": {
                "ScreenBasicConfig": {"ScreenName": self.screenName, "ScreenDesc": self.screenDesc},
                "ScreenQAConfig": self.screenQAConfig,
            },
            "CreateTime": self.createTime.strftime("%Y-%m-%d %H:%M:%S") if self.createTime and not isinstance(self.createTime, str) else self.createTime,
            "UpdateTime": self.updateTime.strftime("%Y-%m-%d %H:%M:%S") if self.updateTime and not isinstance(self.updateTime, str) else self.updateTime,
        }


