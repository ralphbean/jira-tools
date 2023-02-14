.left-column[
## Completed
## In Progress
## Next Up
## Dependencies
]
.right-column[

## Incoming Dependencies
Stuff we need from other teams ({{incoming | length}} issues).
{% for issue in incoming -%}
* [{{issue.key}}]({{issue.url}}) {{issue.summary | truncate(40)}}
{% endfor %}

## Outgoing Dependencies
Stuff that other teams need from us ({{outgoing | length}} issues).
{% for issue in outgoing -%}
* [{{issue.key}}]({{issue.url}}) {{issue.summary | truncate(40)}}
{% endfor %}
]
