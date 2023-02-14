.left-column[
## Completed
## In Progress
## Next Up
]
.right-column[
{% for feature in features -%}
{% if feature.has_work_in_status("To Do") %}
[{{feature.key}}]({{feature.url}}) {{feature.summary | truncate(40)}}
{%- for epic in feature.children %}{% if epic.has_work_in_status("To Do") %}
* [{{epic.key}}]({{epic.url}}) {{epic.summary | truncate(36)}}
{%- endif -%}
{% endfor %}
{% endif -%}
{% endfor %}
]
