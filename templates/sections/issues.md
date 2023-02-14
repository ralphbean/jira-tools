.left-column[
## Completed
## In Progress
## Next
## Dependencies
## Other Epics
## Other Issues
]
.right-column[

## Work completed on issues with no epic
{%- for issue in issues %}{% if issue.has_work_in_status("Done") %}
* [{{issue.key}}]({{issue.url}}) {{issue.summary}}
{%- endif -%}
{% endfor %}
]
