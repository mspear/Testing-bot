import pytest
from slackbot.get_testers import balance_testing, find_next
from slackbot.db_setup.sql_declarations import User

from sqlalchemy import desc


def test_balance_tester(session):

    highest_user = session.query(User).order_by(desc(User.assigned_tests)).first()
    highest_user.assigned_tests = 0
    session.commit()
    absent_set = {highest_user.slack_id}

    balance_testing(absent_set=absent_set, session=session)

    session.commit()
    user = session.query(User).order_by(User.assigned_tests).first()

    assert user.slack_id in absent_set
    assert user.assigned_tests > 0


@pytest.mark.filterwarnings('ignore::sqlalchemy.exc.SAWarning')
def test_find_next(session):
    # Test with an empty exception set
    exception_set = set()
    tester_one, tester_two = find_next(session=session, exception_set=exception_set)

    T1, T2 = session.query(User).filter(User.slack_id.in_({tester_one, tester_two})).all()

    assert not (T1.is_intern and T2.is_intern)
    assert not T1.slack_id in exception_set or T2.slack_id in exception_set

    # Test with non empty absent set
    exception_set.add(tester_one)

    tester_one, tester_two = find_next(session=session, exception_set=exception_set)

    T1, T2 = session.query(User).filter(User.slack_id.in_({tester_one, tester_two})).all()

    assert not (T1.is_intern and T2.is_intern)
    assert not T1.slack_id in exception_set or T2.slack_id in exception_set

