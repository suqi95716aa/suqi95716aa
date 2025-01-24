from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, DATETIME

Base = declarative_base()


class UserInfo(Base):
    """用户信息"""
    __tablename__ = "user_info"
    uid = Column(VARCHAR(7), comment='用户id')
    username = Column(VARCHAR(15), primary_key=True, comment='用户名')
    password = Column(VARCHAR(15), comment='用户密码')
    phone = Column(VARCHAR(11), unique=True, comment='手机号')
    createTime = Column(DATETIME, comment='创建时间')
    lastLoginTime = Column(DATETIME, comment='最后一次登录时间')
    deleteTime = Column(DATETIME, default=None, comment='删除时间')

    def to_dict(self):
        return {
            "Uid": self.uid,
            "UserName": self.username,
            "Password": self.password,
            "Phone": self.phone,
            "CreateTime": self.createTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.createTime, str) else self.createTime,
            "LastLoginTime": self.lastLoginTime.strftime("%Y-%m-%d %H:%M:%S") if not isinstance(self.lastLoginTime, str) else self.lastLoginTime,
        }

    def __repr__(self):
        return f"UserInfo({[f'{attr}: {getattr(self, attr)}' for attr in dir(self) if '_' not in attr]})"

