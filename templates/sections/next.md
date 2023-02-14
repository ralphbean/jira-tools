.left-column[
## Completed
## In Progress
## Next Up
]
.right-column[
{% for feature in features -%}
{% if feature.has_work_in_status("To Do") %}
[{{feature.key}}]({{feature.url}}) {{feature.summary}}
{%- for epic in feature.children %}{% if epic.has_work_in_status("To Do") %}
* [{{epic.key}}]({{epic.url}}) {{epic.summary}}
{%- endif -%}
{% endfor %}
{% endif -%}
{% endfor %}
]
