
from slackbot.db_setup.session_context import DBSession
from slackbot.db_setup.sql_declarations import Issue, User


def get_issue_status(issueid):
    from main import jira
    """
    Takes in an issue id. For example VP-1748
    :param issueid:
    :return:
    """

    return_packet = {}
    # customfield_10800 = stakeholder
    try:
        i = jira.issue(issueid, fields='assignee,customfield_10800,subtasks,status,summary,votes')
        return_packet['issue'] = i
    except Exception:
        return {}

    with DBSession() as session:
        results = session.query(Issue.tester).filter(Issue.issue_id == issueid).all()
        if results:
            results = [x[0] for x in results]
            testers = [x[0] for x in session.query(User.slack_name).filter(User.slack_id.in_(results)).all()]

        return_packet['testers'] = testers if results else []

    return return_packet


def get_review_issues():
    from main import jira
    JQL = 'sprint in openSprints() and status = "Review"'
    issues = jira.search_issues(JQL)
    return issues
