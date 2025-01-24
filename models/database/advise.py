from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, VARCHAR, SmallInteger, INT, DATETIME

Base = declarative_base()


class FeedbackInfo(Base):
    """User feedback model"""
    __tablename__ = "feedback_info"
    id = Column(INT, primary_key=True, comment='record id', autoincrement=True)
    uid = Column(VARCHAR(7), comment='user id')
    feedback = Column(VARCHAR(200), comment='feedback')
    status = Column(SmallInteger, comment='0 - initial; 1 - acceptable; 2 - rejected')
    score = Column(SmallInteger, comment='0 - Bad; 1 - No sense; 2 - Not bad; 3 - Bad; 4 - Good; 5 - Very Good')
    createTime = Column(DATETIME, comment='create time')

    def to_dict(self):
        return {
            "Feedback": self.feedback,
            "Status": self.status
        }


if __name__ == "__main__":
    from conf.parser import conf2Dict
    from sqlalchemy import create_engine

    DB_CONF = conf2Dict()['DB_CONFIG']
    engine = create_engine(f"mysql+pymysql://{DB_CONF.get('MYSQL_USERNAME')}:{DB_CONF.get('MYSQL_PASSWORD')}@{DB_CONF.get('MYSQL_HOST')}:{DB_CONF.get('MYSQL_PORT')}/{DB_CONF.get('MYSQL_DATABASE')}?charset=utf8mb4")
    Base.metadata.create_all(engine)

    engine = create_engine('mysql+pymysql://user:password@localhost/dbname')

