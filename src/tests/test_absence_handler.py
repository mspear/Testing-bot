from slackbot.db_setup.sql_declarations import User
from slackbot.absent_handler import alter_absent_set, get_active_users, get_absent_users, \
    ABSENT_MESSAGE, \
    INVALID_SLACK_NAME_MESSAGE


def test_absent_list(session):
    slack_ids = [slack_id for tup in session.query(User.slack_id) for slack_id in tup]
    absent_set = set(slack_ids[:3]) if slack_ids else set()
    return_message = get_absent_users(set(absent_set))
    if not absent_set:
        assert return_message == ABSENT_MESSAGE
    else:
        assert return_message == '\n'.join(
            name for tup in session.query(User.slack_name).filter(User.slack_id.in_(absent_set)) for name in tup
        )

def test_active_list(session):
    slack_ids = [slack_id for tup in session.query(User.slack_id) for slack_id in tup]

    absent_set = set(slack_ids[:3]) if slack_ids else set()

    return_message = get_active_users(absent_set)

    active_users = [slack_name for tup in
                    session.query(User.slack_name).filter(User.slack_id.notin_(absent_set))
                    for slack_name in tup]

    assert len(return_message.split('\n')) == len(slack_ids) - len(list(absent_set))
    assert return_message == '\n'.join(active_users)

def test_alter_absent_set_remove(session):
    id, name = session.query(User.slack_id, User.slack_name).first()

    absent_set = set()
    return_message = alter_absent_set(absent_set=absent_set, name=name, operation='remove')

    return_message2 = alter_absent_set(absent_set=absent_set, name=name, operation='-')

    assert absent_set == {id}


def test_alter_absent_set_add(session):
    id, name = session.query(User.slack_id, User.slack_name).first()
    absent_set = {id}

    return_message = alter_absent_set(absent_set=absent_set, name=name, operation='add')
    return_message2 = alter_absent_set(absent_set=absent_set, name=name, operation='+')

    assert absent_set == set()

def test_alter_absent_set_invalid(session):

    name = 'RANDOM_TEST_NAME'

    return_message = alter_absent_set(absent_set=set(), name=name, operation='+')

    return_message2 = alter_absent_set(absent_set=set(), name=name, operation='-')

    assert INVALID_SLACK_NAME_MESSAGE == return_message == return_message2
