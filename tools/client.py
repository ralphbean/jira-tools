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

    def get_project(self, project_id):
        project = self._client.project(project_id)
        return {
            'key': project.key,
            'description': project.name,
        }

    def _search(self, query, page_size=50, limit=None):
        def _paginate():
            i = 0
            results = self._client.search_issues(
                query, maxResults=page_size, startAt=i, expand='changelog'
            )
            while results:
                for result in results:
                    yield result
                    i = i + 1
                    if limit and i >= limit:
                        break
                results = self._client.search_issues(
                    query, maxResults=page_size, startAt=i, expand='changelog'
                )

        return _paginate()

    def search(self, query):
        issues = self._search(query)
        return [tools.model.Issue.from_raw(self, issue) for issue in issues]

    def count_issues(self, query):
        response = self._client.search_issues(query, maxResults=1, fields='summary')
        return response.total

    def _get(self, key):
        query = f"key={key}"
        results = list(self._search(query))
        if len(results) == 0:
            raise ValueError(f"Could not find issue {key}")
        if len(results) > 1:
            raise ValueError(f"Impossible! Found more than one issue {key}")
        return results[0]

    def get(self, key):
        if key not in self.cache:
            issue = self._get(key)
            self.cache[key] = tools.model.Issue.from_raw(self, issue)
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


if __name__ == '__main__':
    client = JiraClient()
    print(client.count_issues("project=KONFLUX"))
