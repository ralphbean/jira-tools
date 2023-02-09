import os
import textwrap

import jira

# import jinja2


class Issue(object):
    def __init__(self, client, raw_issue):
        self.client = client

        # TODO - these uses of customfield_... aren't portable.
        # Look them up using the meta API.
        self.key = raw_issue.key
        self.summary = raw_issue.fields.summary
        self.rank = raw_issue.fields.customfield_12311940
        self.assignee = getattr(raw_issue.fields.assignee, 'raw', None)
        self.status = raw_issue.fields.status.raw['statusCategory']['name']
        self.children = []

        client.cache[self.key] = self

        self.epic = None
        self.feature = None

        epic_key = getattr(raw_issue.fields, 'customfield_12311140', None)
        feature_key = getattr(raw_issue.fields, 'customfield_12313140', None)
        if epic_key:
            self.epic = Issue.from_raw(client, client.get(epic_key))
            if self not in self.epic.children:
                self.epic.children.append(self)
            self.feature = self.epic.feature
        elif feature_key:
            self.feature = Issue.from_raw(client, client.get(feature_key))
            if self not in self.feature.children:
                self.feature.children.append(self)

    @staticmethod
    def from_raw(client, raw_issue):
        if raw_issue.key in client.cache:
            return client.cache[raw_issue.key]
        return Issue(client, raw_issue)

    def __repr__(self):
        return f"<{self.key}: {self.summary}>"


class JiraClient(object):
    def __init__(self):
        self._client = self._construct_client()
        self.cache = {}

    @staticmethod
    def _construct_client():
        url = os.environ.get("JIRA_URL", "https://issues.redhat.com")
        token = os.environ.get("JIRA_TOKEN")
        if not token:
            raise KeyError(
                "Set JIRA_TOKEN environment variable to your JIRA personal access token"
            )

        return jira.client.JIRA(server=url, token_auth=token)

    def _search(self, query):
        def _paginate():
            i = 0
            page_size = 50
            results = self._client.search_issues(query, maxResults=page_size, startAt=i)
            while results:
                for result in results:
                    yield result
                i = i + page_size
                results = self._client.search_issues(query, maxResults=page_size, startAt=i)
        return _paginate()

    def search(self, query):
        issues = self._search(query)
        return [Issue.from_raw(self, issue) for issue in issues]

    def get(self, key):
        if key not in self.cache:
            query = f"key={key}"
            results = self.search(query)
            if len(results) == 0:
                raise ValueError(f"Could not find issue {key}")
            if len(results) > 1:
                raise ValueError(f"Impossible! Found more than one issue {key}")
            self.cache[key] = results[0]
        return self.cache[key]

    def gather_issues(self, jql, sprint_start):
        issue_query = trim(
            f"""
            {jql} and
            type not in (Feature, Epic) and
            (statusCategory != Done or resolutionDate > {sprint_start})
        """
        )
        issues = self.search(issue_query)

        orphan_issues, orphan_epics, features = [], [], []

        for issue in issues:
            if issue.feature:
                features.append(issue.feature)
            elif issue.epic:
                orphan_epics.append(issue.epic)
            else:
                orphan_issues.append(issue)

        return orphan_issues, orphan_epics, features


def trim(jql):
    return textwrap.dedent(jql).replace("\n", " ").strip()


def render(issues, epics, features, incoming, outgoing):
    return "TODO"
