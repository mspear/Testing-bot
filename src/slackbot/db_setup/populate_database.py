from pickle import load

from .make_db_session import make_session

from .sql_declarations import Issue, User

session = make_session('sqlite:///../sql_bot.db')
name_id_dict = {'danny': 'U2AL90DML',
                'joemaffei': 'U24611LTF',
                'michael': 'U5PLYSB38',
                'reedanderson': 'U2EBWQ02X',
                'ringoli': 'U5XCPMY3H',
                'sam': 'U2430S37E',
                'stephen': 'U244T9BRA',
                'shroeder': 'U24650STT'}

jira_id_dict = {'Danny Thompson': 'danny',
                'Joe Maffei': 'joemaffei',
                'Luke Wolf': 'shroeder',
                'Michael Spear': 'michael',
                'Reed Anderson': 'reedanderson',
                'Xiyang Li': 'ringoli',
                'Sam Damico': 'sam',
                'sreddy': 'stephen'}

user_id_set = {'U2AL90DML', 'U24611LTF', 'U5PLYSB38', 'U2EBWQ02X', 'U2430S37E', 'U24650STT', 'U244T9BRA', 'U5XCPMY3H'}

intern_set = {'U5GGNSQMT', 'U5PLYSB38', 'U5XCPMY3H'}
F_PATH = 'C:\\Users\\MichaelS\\TestingListener\\issues.p'

person_dict = {}

for person in jira_id_dict:
    jira_name = person
    slack_name = jira_id_dict[person]
    slack_id = name_id_dict[jira_id_dict[person]]
    isIntern = slack_id in intern_set
    p = User(slack_id=slack_id, slack_name=slack_name, jira_name=jira_name, is_intern=isIntern)

    person_dict[slack_id] = p
    session.add(p)

session.commit()
import os
if os.path.exists(F_PATH):

    with open(F_PATH, 'rb')as f:
        issue_dict = load(f)

    for i in issue_dict:
        issue_id = i
        tester_one, tester_two = issue_dict[i]

        issue = Issue(issue_id=issue_id,
                    tester_one=tester_one,
                    tester_two=tester_two,
                    t_one=person_dict[tester_one],
                    t_two=person_dict[tester_two])

        session.add(issue)


    session.commit()
