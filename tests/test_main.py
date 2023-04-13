import unittest.mock

import tools.client


class MockStatus(object):
    def __init__(self, name):
        self.raw = {
            'statusCategory': {
                'name': name,
            },
        }


class MockType(object):
    def __init__(self, name):
        self.name = name


class MockFields(object):
    def __init__(self, summary, rank, assignee, status, epic, feature):
        self.summary = summary
        self.customfield_12311940 = rank
        self.assignee = assignee
        self.status = status
        self.customfield_12311140 = epic
        self.customfield_12313140 = feature
        if epic:
            self.issuetype = MockType("Story")
        elif feature:
            self.issuetype = MockType("Epic")
        else:
            self.issuetype = MockType("Feature")


class MockRawIssue(object):
    def __init__(self, key, summary, rank, assignee='nobody', epic=None, feature=None):
        self.key = key
        self.fields = MockFields(
            summary,
            rank,
            assignee,
            status=MockStatus('nothing'),
            epic=epic,
            feature=feature,
        )


def _mock_client(self):
    return None


@unittest.mock.patch('tools.client.JiraClient._construct_client', _mock_client)
def test_gather_closed_simple():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = tools.client.JiraClient()
    with unittest.mock.patch('tools.client.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues_closed_since("x", "x")

    assert len(issues) == 1
    assert len(epics) == 0
    assert len(features) == 0
    assert issues[0].key == "FOO-123"


@unittest.mock.patch('tools.client.JiraClient._construct_client', _mock_client)
def test_gather_closed_one_epic():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", epic="FOO-500"),
        ],
        'key=FOO-500': [
            MockRawIssue("FOO-500", "Simple epic", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = tools.client.JiraClient()
    with unittest.mock.patch('tools.client.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues_closed_since("x", "x")

    assert len(issues) == 0  # No orphan issues
    assert len(epics) == 1
    assert len(features) == 0
    assert epics[0].key == "FOO-500"
    assert len(epics[0].children) == 1
    assert epics[0].children[0].key == "FOO-123"


@unittest.mock.patch('tools.client.JiraClient._construct_client', _mock_client)
def test_gather_closed_one_feature():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", epic="FOO-500"),
        ],
        'key=FOO-500': [
            MockRawIssue(
                "FOO-500", "Simple epic", "abcdef", epic=None, feature="FOO-9000"
            ),
        ],
        'key=FOO-9000': [
            MockRawIssue("FOO-9000", "Simple feature", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = tools.client.JiraClient()
    with unittest.mock.patch('tools.client.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues_closed_since("x", "x")

    assert len(issues) == 0  # No orphan issues
    assert len(epics) == 0  # No orphan epics
    assert len(features) == 1
    assert features[0].key == "FOO-9000"
    assert len(features[0].children) == 1
    assert features[0].children[0].key == "FOO-500"
    assert len(features[0].children[0].children) == 1
    assert features[0].children[0].children[0].key == "FOO-123"


@unittest.mock.patch('tools.client.JiraClient._construct_client', _mock_client)
def test_gather_closed_one_extra_orphan_issue():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", epic="FOO-500"),
            MockRawIssue("FOO-124", "Orphan issue", "abcdef"),
        ],
        'key=FOO-500': [
            MockRawIssue(
                "FOO-500", "Simple epic", "abcdef", epic=None, feature="FOO-9000"
            ),
        ],
        'key=FOO-9000': [
            MockRawIssue("FOO-9000", "Simple feature", "abcdef"),
        ],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = tools.client.JiraClient()
    with unittest.mock.patch('tools.client.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues_closed_since("x", "x")

    assert len(issues) == 1
    assert issues[0].key == "FOO-124"
    assert len(epics) == 0  # No orphan epics
    assert len(features) == 1
    assert features[0].key == "FOO-9000"
    assert len(features[0].children) == 1
    assert features[0].children[0].key == "FOO-500"
    assert len(features[0].children[0].children) == 1
    assert features[0].children[0].children[0].key == "FOO-123"


@unittest.mock.patch('tools.client.JiraClient._construct_client', _mock_client)
def test_gather_closed_one_extra_orphan_epic():
    mock_queries = {
        'x and type not in (Feature, Epic) and (statusCategory != Done or resolutionDate > x)': [
            MockRawIssue("FOO-123", "Simple issue", "abcdef", epic="FOO-500"),
            MockRawIssue("FOO-124", "Kinda orphan issue", "abcdef", epic="FOO-501"),
        ],
        'key=FOO-500': [
            MockRawIssue(
                "FOO-500", "Simple epic", "abcdef", epic=None, feature="FOO-9000"
            )
        ],
        'key=FOO-501': [MockRawIssue("FOO-501", "Orphan epic", "abcdef")],
        'key=FOO-9000': [MockRawIssue("FOO-9000", "Simple feature", "abcdef")],
    }

    _mock_search = lambda _, query: mock_queries[query]

    JIRA = tools.client.JiraClient()
    with unittest.mock.patch('tools.client.JiraClient._search', _mock_search):
        issues, epics, features = JIRA.gather_issues_closed_since("x", "x")

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
