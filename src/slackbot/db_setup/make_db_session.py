import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from slackbot.db_setup.sql_declarations import engine


def make_session():

    DBSession = sessionmaker(bind=engine)

    session = DBSession()

    return session

