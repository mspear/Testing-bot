# THIS IS A DEVELOPER ONLY FILE
# THE FUNCTIONS IN HERE ARE ONLY TO BE USED
# IF YOU KNOW WHAT YOU'RE DOING
# CHANGES TO THE DATABASE ARE IRREVERSIBLE


from sql_declarations import Issue, User, engine
#from slackbot.db_setup.make_db_session import make_session
from sqlalchemy import func 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def add_user(slack_id, slack_name, jira_name, is_intern):
    
    session = sessionmaker(bind=engine)()
    at, = session.query(func.min(User.assigned_tests)).first()
    user = User(slack_id=slack_id,
                slack_name=slack_name,
                jira_name=jira_name,
                is_intern=is_intern,
                assigned_tests=int(at)-1
                )

    session.add(user)

    session.commit()
    session.close()

def delete_user(slack_name):
    session = sessionmaker(bind=engine)()
    try:
        sid, = session.query(User.slack_id).filter(User.slack_name == slack_name).one()
        print(sid)
        rows = session.query(Issue).filter(Issue.tester == sid).delete()
        print(rows, 'issues deleted')
        rows = session.query(User).filter(User.slack_name == slack_name).delete()
        print(rows, 'user deleted')
        session.commit()
    finally:
        session.close()

