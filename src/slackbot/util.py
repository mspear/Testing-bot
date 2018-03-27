from slackbot.db_setup.session_context import DBSession
from slackbot.db_setup.sql_declarations import User


def get_id_from_slackname(slackname):
    """Returns
    
    Arguments:
        slackname {str} -- A users slack_name
    
    Returns:
        str -- The users slack_id
    """

    with DBSession() as session:
        slack_id, = session.query(User.slack_id)\
                            .filter(User.slack_name == slackname)\
                            .first()

    return slack_id
