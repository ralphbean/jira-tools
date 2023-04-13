import os


class Issue(object):
    def __init__(self, client, raw_issue):
        self.client = client

        # TODO - these uses of customfield_... aren't portable.
        # Look them up using the meta API.
        self.key = raw_issue.key
        base_url = os.environ.get("JIRA_URL", "https://issues.redhat.com")
        self.url = base_url + "/browse/" + self.key
        self.type = raw_issue.fields.issuetype.name
        self.summary = raw_issue.fields.summary
        self.rank = raw_issue.fields.customfield_12311940
        self.assignee = getattr(raw_issue.fields.assignee, 'raw', None)
        self.status = raw_issue.fields.status.raw['statusCategory']['name']

        self.start_date = self._determine_start_date(raw_issue)

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
            feature = Issue.from_raw(client, client.get(feature_key))
            # Disambiguate between "market problems" and "features"
            if feature.type == 'Feature':
                self.feature = feature
                if self not in self.feature.children:
                    self.feature.children.append(self)

    @staticmethod
    def from_raw(client, raw_issue):
        if raw_issue.key in client.cache:
            return client.cache[raw_issue.key]
        return Issue(client, raw_issue)

    @staticmethod
    def _determine_start_date(raw_issue):
        for event in raw_issue.changelog.histories:
            for change in event.items:
                if change.field == 'status':
                    if change.toString == 'In Progress':
                        return event.created.split('T')[0]

        return None

    def __repr__(self):
        return f"<{self.key} ({self.type}, {self.status}): {self.summary}>"

    def has_work_in_status(self, status):
        if self.status == status:
            return True
        for child in self.children:
            if child.has_work_in_status(status):
                return True
        return False
