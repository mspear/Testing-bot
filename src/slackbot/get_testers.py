import logging
import re
from datetime import datetime
from sqlalchemy import and_, not_
from slackbot.db_setup.session_context import DBSession

from slackbot.db_setup.sql_declarations import User, Issue

JIRA_ISSUE_RE = re.compile(r'(?:NAV|VP|EM|REST)-[0-9]+')


def balance_testing(absent_set, session):
    '''
    To be called when someone absent returns to being an active tester.
    This function their scores up to the lowest number of everyone who is here
    :param absent_set:
    :param session:
    :return:
    '''

    if not absent_set: return
    amount = session.query(User.assigned_tests)\
        .filter(User.slack_id.notin_(absent_set))\
        .order_by(User.assigned_tests).first()[0]

    Users = session.query(User)\
        .filter(and_(User.slack_id.in_(absent_set), User.assigned_tests < amount))\
        .all()

    for u in Users:
        print(u.assigned_tests)
        u.assigned_tests = amount


def find_next(session, exception_set):
    '''
    finds the next two valid testers
    restrictions are
    1. Both users must be present
    2. Both users cannot be interns

    :param session:
    :param exception_set:
    :return:
    '''
    logging.debug('Exception set: ' + str(exception_set))
    tester_list = []
    user = session.query(User)\
        .filter(User.slack_id.notin_(exception_set))\
        .order_by(User.assigned_tests)\
        .first()
    tester_list.append(user.slack_id)
    exception_set = exception_set | {user.slack_id}
    if user.is_intern:
        user = session.query(User.slack_id)\
            .filter(and_(User.slack_id.notin_(exception_set), not_(User.is_intern)))\
            .order_by(User.assigned_tests)\
            .first()
    else:
        user = session.query(User.slack_id, User.is_intern)\
            .filter(User.slack_id.notin_(exception_set))\
            .order_by(User.assigned_tests)\
            .first()

    tester_list.append(user[0])
    return tester_list


def testing_response(slack_client, absent_set, data):

    '''
    Responds to the JIRA CLOUD user when it posts an issue
    It will assign testers in a fair fashion and record the number of tests
    each person has done
    :param slack_client:
    :param absent_set:
    :param data:
    :return:
    '''

    with DBSession(commit=False) as session:

        jira_name_re = re.compile(r'\*([\w\s]+)\*$')

        attachments = data['attachments'][0]
        issue_number = JIRA_ISSUE_RE.match(attachments['fallback'])
        if not issue_number:
            return
        else:
            issue_number = issue_number.group(0)

        testers = [t for tup in session.query(Issue.tester).filter(Issue.issue_id == issue_number) for t in tup]

        if len(testers) == 2:
            logging.debug('Issue {} found in issue table'.format(issue_number))
            tester1, tester2 = testers
            session.query(Issue).filter(Issue.issue_id == issue_number).update({"last_posted": datetime.now()})
            session.commit()

        else:
            jira_name = jira_name_re.search(attachments['text']).group(1)

            assignee = session.query(User.slack_id).filter(User.jira_name == jira_name).first()

            logging.debug('Assignee: ' + str(assignee))

            tester1, tester2 = find_next(session, absent_set|{assignee[0]} if assignee else absent_set)

            if data['channel'] != 'C5ZMWUJR0':
                issue = Issue(issue_id=issue_number, tester=tester1, last_posted=datetime.now())
                session.add(issue)
                session.commit()
                if len(testers) == 0:
                    issue = Issue(issue_id=issue_number, tester=tester2, last_posted=datetime.now())
                    session.add(issue)
                    session.commit()
                    for tester in (tester1, tester2):
                        user = session.query(User).get(tester)
                        user.assigned_tests += 1

                else:
                    tester2, = testers
                    user = session.query(User).get(tester1)
                    user.assigned_tests += 1
                
                session.commit()

        logging.debug('Testers: {} {}'.format(tester1, tester2))
        slack_client.api_call(
            'chat.postMessage',
            channel=data['channel'],
            text='<@{}> and <@{}>'.format(tester1, tester2),
            thread_ts=data['ts'],
            username='Testing Assigner'
        )
