from sqlalchemy.orm.exc import NoResultFound

from slackbot.db_setup.session_context import DBSession
from slackbot.db_setup.sql_declarations import User
from slackbot.get_testers import balance_testing

INVALID_SLACK_NAME_MESSAGE = 'No user with that slack name found'

ABSENT_MESSAGE = 'No one is absent'


def alter_absent_set(absent_set, name, operation):
    '''
    takes an takes a command and a name and alters the
    absent set accordingly
    returns the message to be printed by the slack client
    :param absent_set:
    :param name:
    :param operation:
    :return string:
    '''

    message = ''
    with DBSession() as session:
        try:
            id = session.query(User.slack_id).filter(name == User.slack_name).one()[0]

            if operation == '-' or operation == 'remove':
                if id not in absent_set:
                    absent_set.add(id)
                    message = '{} has been registered absent'.format(name)
                else:
                    message = '{} is already registered as absent'.format(name)

            else:
                if id in absent_set:
                    absent_set.remove(id)
                    balance_testing(session=session, absent_set=absent_set)
                    message = '{} has been registered as present'.format(name)

                else:
                    message = '{} is not registered as absent'.format(name)

        except NoResultFound:
            message = INVALID_SLACK_NAME_MESSAGE

    return message

def get_absent_users(absent_set):
    '''
    returns absent users separated by new line
    :param absent_set:
    :return string:
    '''
    if absent_set:
        with DBSession() as session:
            absent_users = \
                [name for result in session.query(User.slack_name).filter(User.slack_id.in_(absent_set)) for name in result]
            message = '\n'.join(absent_users)

    else:
        message = ABSENT_MESSAGE

    return message

def get_active_users(absent_set):
    '''
    returns list of active users
    :param absent_set:
    :return string:
    '''
    with DBSession() as session:
        if absent_set:
            active_users = \
                [name for result in session.query(User.slack_name).filter(User.slack_id.notin_(absent_set)) for name in result]
        else:
            active_users = \
                [name for result in session.query(User.slack_name) for name in result]
        message = '\n'.join(active_users)

    return message
