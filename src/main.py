import logging
import os
import re
import time
import base64
from jira import JIRA
from sqlalchemy import desc
from slackclient import SlackClient
from slackbot.db_setup.session_context import DBSession
from slackbot.nav_jira import get_issue_status, get_review_issues

from slackbot.absent_handler import alter_absent_set, get_active_users, get_absent_users, INVALID_SLACK_NAME_MESSAGE
from slackbot.db_setup.sql_declarations import User, Issue
from slackbot.get_testers import testing_response, balance_testing, find_next

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SQL_BOT_DB = 'sqlite:///' + os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), 'sql_bot.db'))

ABSENT_SET_RE = re.compile(r'^([+\-]|add|remove) ([a-zA-Z0-9]+)')
JIRA_ISSUE_RE = re.compile(r'(?:NAV|VP|EM|REST)-[0-9]+')

ISSUE_COLORS = {'Open': '4a6785',
                'In Progress': 'f6c342',
                'Review': 'f6c342',
                'Done': '14892c'}

jira = JIRA('http://navegate.atlassian.net',
            basic_auth=('michael.spear', base64.b64decode(b'YjlnM3Q0bXdz').decode())  # When Possible I will get this
            )                                                                         # switched to OAUTH.


class ServerDisconnectException(Exception):
    pass


def get_absent_set():
    """
    Loads up any people in the absent.txt file
    into the absent set
    :return set:
    """
    absent_set = set()

    if os.path.exists(os.path.join(BASE_DIR, 'absent.txt')):
        print('Found file')
        with DBSession() as session:
            user_query = session.query(User)
            with open(os.path.join(BASE_DIR, 'absent.txt'), 'r') as f:
                for person in f:
                    user = user_query.filter(User.slack_name == person.strip()).first()
                    if user:
                        logging.info(user.slack_name + ' is absent')
                        absent_set.add(user.slack_id)

    logging.debug(absent_set)
    return absent_set


def handle(absent_set, data, slack_client):
    """The handler for input read in main loop

    :param absent_set:
    :param data:
    :param slack_client:
    :return:
    """

    attachments = []  # Message Attachments

    for entry in data:
        if entry.get('type', None) == 'hello':
            logging.info('Hello Received')
            print('Hello Received')
            for x in range(2):
                time.sleep(1)
                slack_client.rtm_read()  # Handles anomalous messages

        if entry.get('type', None) == 'message':
            slash_bot_command = re.match(r'\\ibot(.+)?', entry.get('text', ''))
            if slash_bot_command:
                # Handles all \ibot commands
                # Parses them out in a Regex and then case selects to the appropriate one

                slack_client.api_call('chat.delete', channel=entry['channel'], ts=entry['ts'])
                time.sleep(1)
                message = slash_bot_command.group(1)
                if message:
                    message = message.strip()
                elif not message or message == 'help':
                    # Print \ibot help message
                    ibot_helper(user=entry['user'], slack_client=slack_client)
                    return

                absent_set_matches = ABSENT_SET_RE.match(message)
                if absent_set_matches:
                    username = 'Absence Tracker'
                    return_message = alter_absent_set(absent_set=absent_set,
                                                      name=absent_set_matches.group(2),
                                                      operation=absent_set_matches.group(1))

                    if return_message != INVALID_SLACK_NAME_MESSAGE:
                        with DBSession() as session:
                            id = session.query(User.slack_id)\
                                    .filter(absent_set_matches.group(2) == User.slack_name).one()[0]

                            if id != entry['user']:
                                name = session.query(User.slack_name)\
                                    .filter(User.slack_id == entry['user']).one()[0]
                                text = "(Performed by {}) {}".format(name, return_message)
                                slack_client.api_call('chat.postMessage',
                                                      channel="@"+absent_set_matches.group(2),
                                                      text=text,
                                                      username='Absence Tracker')

                elif message == 'active list':
                    username = 'Active List'
                    return_message = get_active_users(absent_set=absent_set)

                elif message == 'absent list':
                    username = 'Absent List'
                    return_message = get_absent_users(absent_set=absent_set)

                elif message == 'count':
                    username = 'Test Counter'
                    return_message = get_issue_count(entry['user'])

                elif message == 'next':
                    username = 'Testing Assigner'
                    return_message = get_next_testers(absent_set)
                elif message.startswith('status'):  # Get issue status
                    username = 'Issue Status'
                    issueid = JIRA_ISSUE_RE.search(entry['text']).group(0)

                    issue_info = get_issue_status(issueid)
                    if 'issue' not in issue_info:
                        return_message = 'No Such Issue'
                    else:
                        i = issue_info['issue']
                        message = '''
Status: {status}
Testers: {testers}
Stakeholders: {stakeholders}
                                            '''.format(name=issueid,
                                                       status=i.fields.status.name,
                                                       stakeholders=i.fields.customfield_10800,
                                                       testers=' and '.join(issue_info['testers']) if issue_info[
                                                           'testers'] else 'No testers assigned'
                                                       )
                        attachment = {'color': ISSUE_COLORS[i.fields.status.name],
                                      'title_link': 'https://navegate.atlassian.net/browse/'+issueid,
                                      'title': issueid + ': ' + i.fields.summary,
                                      'text': message}
                        attachments.append(attachment)
                        return_message = ''

                elif message == 'review':
                    review_issues = get_review_issues()
                    enough_votes = [lv for lv in review_issues if lv.fields.votes.votes >= 2]
                    rest = [lv for lv in review_issues if lv not in enough_votes]
                    username = 'Review'
                    return_message = '*2+ votes:*\n' + '\n'.join([str(i) for i in enough_votes]) + \
                                     '\n*< 2 votes:*\n' + '\n'.join([str(i) for i in rest])

                else:
                    ibot_helper(user=entry['user'], slack_client=slack_client)
                    return

                slack_client.api_call('chat.postMessage',
                                      channel=entry['user'],
                                      text=return_message,
                                      username=username,
                                      attachments=attachments
                                      )
              
            elif entry['channel'] == 'C2ZTR2CE8' or entry['channel'] == 'C5ZMWUJR0':
                if entry.get('bot_id', None) == 'B4ZMVF6HL':
                    testing_response(data=entry, slack_client=slack_client, absent_set=absent_set)


def get_next_testers(absent_set):
    """Returns the next to people to be assigned to a fresh issue then
    rolls back the database to before the calculations were made
    
    Arguments:
        absent_set {set} -- Set of slack_names to be excluded from the pick
    
    Returns:
        str -- description
    """
    with DBSession() as session:
        try:
            t_list = find_next(session, absent_set)
            for lv in session.query(User).filter(User.slack_id.in_(t_list)):
                lv.assigned_tests += 1
            t_list2 = find_next(session, absent_set)
            name_list = [r[0] for id in t_list + t_list2 for r in session.query(User.slack_name).filter(User.slack_id == id)]
        finally:
            session.rollback()
    return_message = "Next: {t[0]}, {t[1]}\nAfter: {t[2]}, {t[3]}".format(t=name_list)
    return return_message


def get_issue_count(slack_id):
    """Returns a message containing the number of issues tested by a
    user as well as the last 10 that they tested
    
    Arguments:
        entry {dict} -- entry packet
    
    Returns:
        str -- return message to be sent to the user
    """
    with DBSession() as session:

        tests = [r[0] for r in session.query(Issue.issue_id).filter(Issue.tester == slack_id)\
                                                        .order_by(desc(Issue.last_posted)).limit(10).all()]

        tests_num = session.query(Issue).filter(Issue.tester == slack_id).count()
        return_message = '\n'.join(
            ["You have tested {0} issues.".format(tests_num)] + tests
            )
        if tests_num > 10:
            return_message += '\n...'
    return return_message


def ibot_helper(slack_client, user):

    message = r'''
    Hello, it's ibot!
    
Commands:

*Adding and removing testers*
\ibot (-/remove) _slackname_  ---- Will remove a user from the active testers
\ibot (+/add) _slackname_     ---- Will add a user to the active testers

*User statuses*
\ibot absent list    ---- PMs you a list of all absent users.
\ibot active list    ---- PMs you a list of all active testers

*Utility Commands*
\ibot count          ---- PMs you with the number of issues you've been assigned
\ibot next           ---- PMs you with an idea of who is next to be assigned an issue
\ibot review         ---- PMs you a list of issues in the review column
\ibot status         ---- PMs you with the status of an issue

*Help Commands*
\ibot, \ibot help    ---- PMs you this help message and exits
    
    
Hope this helped!
    '''
    slack_client.api_call('chat.postMessage', channel=user, text=message, username='ibot')


def main():
    '''
    main loop for the program,
    uses the SlackClient library to fetch the client,
    connects to the real time messaging service,
    and pings the server once a minute to ensure continued
    connectivity

    :return:
    '''
    slack_client = SlackClient(os.environ['SLACK_API_TOKEN'])

    absent_set = get_absent_set()
    with DBSession() as session:
        balance_testing(absent_set, session)

    if slack_client.rtm_connect():
        try:
            while True:
                for _ in range(60):

                    data = slack_client.rtm_read()
                    if data:
                        handle(data=data, slack_client=slack_client, absent_set=absent_set)
                    time.sleep(1)

                try:
                    ping_data = ping_pong(slack_client=slack_client)
                    handle(data=ping_data, slack_client=slack_client, absent_set=absent_set)
                except ServerDisconnectException:
                    logging.info('Reconnecting to WebSocket')
                    if not slack_client.rtm_connect():
                        logging.info('Reconnect Failed')
                        break
                    logging.info('Reconnect Succeeded')

        except KeyboardInterrupt:
            logging.info('Interrupt received, shutting down')

        except Exception:
            logging.exception('Exception throw')

        finally:
            # Shutdown for Testing bot
            logging.info('Shutting Down TestListener')
            if absent_set:
                with DBSession() as session:
                    with open(os.path.join(BASE_DIR, 'absent.txt'), 'w') as f:
                        for item in session.query(User.slack_name).filter(User.slack_id.in_(absent_set)).all():
                            f.write(item[0] + '\n')
            else:
                logging.info('No one is absent. Attempting to remove file.')
                try:
                    os.remove(os.path.join(BASE_DIR, 'absent.txt'))
                except OSError:
                    logging.debug('file does not exist')

            BACKUPS_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'BackupDBs'))
            if os.path.exists(BACKUPS_PATH):
                import datetime, sqlite3
                backup = sqlite3.connect(os.path.join(BACKUPS_PATH, '{0:%Y}{0:%m}{0:%d}{0:%H}{0:%M}sql_bot.db'.format(datetime.datetime.now())))
                current = sqlite3.connect(os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), 'sql_bot.db')))

                query = ''.join(line for line in current.iterdump())

                backup.executescript(query)
                backup.commit()
                backup.close(); current.close()


def ping_pong(slack_client):
    '''
    pings the web socket,
    throws and error if no pong is received
    :param slack_client:
    :return list:
    '''
    slack_client.server.ping()
    data = []
    for _ in range(5):
        time.sleep(1)
        buff = slack_client.rtm_read()
        for entry in buff:
            if entry.get('type', None) == 'pong':
                return data + buff
        data += buff

    logging.debug('No pong received')
    raise ServerDisconnectException


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.path.dirname(BASE_DIR), "logs\\main.log"),
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    main()
