layout: false
.left-column[
## Work Completed
]
.right-column[
{% for feature in features -%}
{% if feature.has_work_in_status("Done") %}
[{{feature.key}}]({{feature.url}}) {{feature.summary | truncate(40)}}
{%- for epic in feature.children %}{% if epic.has_work_in_status("Done") %}
* [{{epic.key}}]({{epic.url}}) {{epic.summary | truncate(36)}}
{%- for issue in epic.children %}{% if issue.has_work_in_status("Done") %}
    - [{{issue.key}}]({{issue.url}}) {{issue.summary | truncate(33)}}
{%- endif -%}
{% endfor %}
{% endif -%}
{% endfor %}
{% endif -%}
{% endfor %}
]
