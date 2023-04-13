import os

import jinja2

from jinja2 import select_autoescape


def _truncate_filter(text, length):
    if len(text) > length:
        text = text[: length - 3] + '...'
    return text


def render(issues, epics, features, incoming, outgoing, template, start, end, title):
    basedir = os.path.dirname(os.path.dirname(__file__))
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(f'{basedir}/templates/'),
        autoescape=select_autoescape(),
    )
    env.filters['truncate'] = _truncate_filter
    return env.get_template(template).render(
        issues=issues,
        epics=epics,
        features=features,
        incoming=incoming,
        outgoing=outgoing,
        start=start,
        end=end,
        title=title,
    )
