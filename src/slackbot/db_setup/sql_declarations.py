import os
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    slack_id = Column(String(10), primary_key=True)
    slack_name = Column(String(250), nullable=False)
    jira_name = Column(String(250))
    is_intern = Column(Boolean, nullable=False)
    assigned_tests = Column(Integer, nullable=0, default=0)



class Issue(Base):
    __tablename__ = 'issue'
    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(String(15))
    tester = Column(String(10), ForeignKey('user.slack_id'))
    last_posted = Column(DateTime)
    tester_relationship = relationship(User, foreign_keys=[tester], cascade='all, delete-orphan', single_parent=True)


print(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'sql_bot.db')))
engine = create_engine(r'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'sql_bot.db'))
Base.metadata.create_all(engine)
