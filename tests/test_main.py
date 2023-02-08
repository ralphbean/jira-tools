import unittest.mock

import sprintreport


class MockRawIssue(object):
    def __init__(self, key, summary, rank, epic=None, feature=None):
        self.key = key
        self.summary = summary
        self.rank = rank
        self.epic = epic
        self.feature = feature


def _mock_client(self):
    return None


@unittest.mock.patch('sprintreport.JiraClient._construct_client', _mock_client)
def test_gather_simple():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = sprintreport.JiraClient()
    with unittest.mock.patch('sprintreport.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues("x", "x")

    assert len(issues) == 1
    assert len(epics) == 0
    assert len(features) == 0
    assert issues[0].key == "FOO-123"


@unittest.mock.patch('sprintreport.JiraClient._construct_client', _mock_client)
def test_gather_one_epic():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", "FOO-500"),
        ],
        'key=FOO-500': [
            MockRawIssue("FOO-500", "Simple epic", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = sprintreport.JiraClient()
    with unittest.mock.patch('sprintreport.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues("x", "x")

    assert len(issues) == 0  # No orphan issues
    assert len(epics) == 1
    assert len(features) == 0
    assert epics[0].key == "FOO-500"
    assert len(epics[0].children) == 1
    assert epics[0].children[0].key == "FOO-123"


@unittest.mock.patch('sprintreport.JiraClient._construct_client', _mock_client)
def test_gather_one_feature():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", "FOO-500"),
        ],
        'key=FOO-500': [
            MockRawIssue("FOO-500", "Simple epic", "abcdef", None, "FOO-9000"),
        ],
        'key=FOO-9000': [
            MockRawIssue("FOO-9000", "Simple feature", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = sprintreport.JiraClient()
    with unittest.mock.patch('sprintreport.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues("x", "x")

    assert len(issues) == 0  # No orphan issues
    assert len(epics) == 0  # No orphan epics
    assert len(features) == 1
    assert features[0].key == "FOO-9000"
    assert len(features[0].children) == 1
    assert features[0].children[0].key == "FOO-500"
    assert len(features[0].children[0].children) == 1
    assert features[0].children[0].children[0].key == "FOO-123"


@unittest.mock.patch('sprintreport.JiraClient._construct_client', _mock_client)
def test_gather_one_extra_orphan_issue():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", "FOO-500"),
            MockRawIssue("FOO-124", "Orphan issue", "abcdef"),
        ],
        'key=FOO-500': [
            MockRawIssue("FOO-500", "Simple epic", "abcdef", None, "FOO-9000"),
        ],
        'key=FOO-9000': [
            MockRawIssue("FOO-9000", "Simple feature", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = sprintreport.JiraClient()
    with unittest.mock.patch('sprintreport.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues("x", "x")

    assert len(issues) == 1
    assert issues[0].key == "FOO-124"
    assert len(epics) == 0  # No orphan epics
    assert len(features) == 1
    assert features[0].key == "FOO-9000"
    assert len(features[0].children) == 1
    assert features[0].children[0].key == "FOO-500"
    assert len(features[0].children[0].children) == 1
    assert features[0].children[0].children[0].key == "FOO-123"


@unittest.mock.patch('sprintreport.JiraClient._construct_client', _mock_client)
def test_gather_one_extra_orphan_epic():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", "FOO-500"),
            MockRawIssue("FOO-124", "Kinda orphan issue", "abcdef", "FOO-501"),
        ],
        'key=FOO-500': [
            MockRawIssue("FOO-500", "Simple epic", "abcdef", None, "FOO-9000")
        ],
        'key=FOO-501': [MockRawIssue("FOO-501", "Orphan epic", "abcdef")],
        'key=FOO-9000': [MockRawIssue("FOO-9000", "Simple feature", "abcdef")],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = sprintreport.JiraClient()
    with unittest.mock.patch('sprintreport.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues("x", "x")

    assert len(issues) == 0
    assert len(epics) == 1
    assert len(features) == 1
    assert epics[0].key == "FOO-501"
    assert epics[0].children[0].key == "FOO-124"
    assert features[0].key == "FOO-9000"
    assert len(features[0].children) == 1
    assert features[0].children[0].key == "FOO-500"
    assert len(features[0].children[0].children) == 1
    assert features[0].children[0].children[0].key == "FOO-123"
