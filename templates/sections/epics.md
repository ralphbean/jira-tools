.left-column[
## Completed
## In Progress
## Next
## Dependencies
## Other Epics
]
.right-column[

## Work completed on epics with no feature
{%- for epic in epics %}
* [{{epic.key}}]({{epic.url}}) {{epic.summary | truncate(36)}}
{%- for issue in epic.children %}{% if issue.has_work_in_status("Done") %}
    - [{{issue.key}}]({{issue.url}}) {{issue.summary | truncate(33)}}
{%- endif -%}
{% endfor %}
{% endfor %}
]
