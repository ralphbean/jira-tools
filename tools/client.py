import operator as op
import os
import textwrap

import jira

import tools.model


url = os.environ.get("JIRA_URL", "https://issues.redhat.com")


def _trim(jql):
    return textwrap.dedent(jql).replace("\n", " ").strip()


class JiraClient(object):
    def __init__(self):
        self._client = self._construct_client()
        self.cache = {}

    @staticmethod
    def _construct_client():
        token = os.environ.get("JIRA_TOKEN")
        if not token:
            raise KeyError(
                "Set JIRA_TOKEN environment variable to your JIRA personal access token"
            )

        return jira.client.JIRA(server=url, token_auth=token)

    def _search(self, query, page_size=50):
        def _paginate():
            i = 0
            results = self._client.search_issues(
                query, maxResults=page_size, startAt=i, expand='changelog'
            )
            while results:
                for result in results:
                    yield result
                i = i + page_size
                results = self._client.search_issues(
                    query, maxResults=page_size, startAt=i, expand='changelog'
                )

        return _paginate()

    def search(self, query):
        issues = self._search(query)
        return [tools.model.Issue.from_raw(self, issue) for issue in issues]

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

    def gather_issues(self, jql):
        issues = self.search(jql)

        orphan_issues, orphan_epics, features = set(), set(), set()

        for issue in issues:
            if issue.feature:
                features.add(issue.feature)
            elif issue.epic:
                orphan_epics.add(issue.epic)
            else:
                orphan_issues.add(issue)

        orphan_issues = sorted(orphan_issues, key=op.attrgetter('rank'))
        orphan_epics = sorted(orphan_epics, key=op.attrgetter('rank'))
        features = sorted(features, key=op.attrgetter('rank'))

        return orphan_issues, orphan_epics, features

    def gather_issues_closed_since(self, jql, since):
        issue_query = _trim(
            f"""
            {jql} and
            type not in (Feature, Epic) and
            (statusCategory != Done or resolutionDate > {since})
        """
        )
        issues = self.search(issue_query)

        orphan_issues, orphan_epics, features = set(), set(), set()

        for issue in issues:
            if issue.feature:
                features.add(issue.feature)
            elif issue.epic:
                orphan_epics.add(issue.epic)
            else:
                orphan_issues.add(issue)

        orphan_issues = sorted(orphan_issues, key=op.attrgetter('rank'))
        orphan_epics = sorted(orphan_epics, key=op.attrgetter('rank'))
        features = sorted(features, key=op.attrgetter('rank'))

        return orphan_issues, orphan_epics, features

    def gather_dependencies(self, jql):
        not_done = "statusCategory != Done"
        jql = f"{jql} and {not_done}"
        incoming_query = (
            f"issueFunction in linkedIssuesOf('{jql}', 'is blocked by') and {not_done}"
        )
        incoming = sorted(self.search(incoming_query), key=op.attrgetter('rank'))
        outgoing_query = (
            f"issueFunction in linkedIssuesOf('{jql}', 'blocks') and {not_done}"
        )
        outgoing = sorted(self.search(outgoing_query), key=op.attrgetter('rank'))
        return incoming, outgoing
