# Summary

## {{ type | title }}
{% for article in articles %}
* [Article {{ article.order }}](article-{{ article.order }}.md)
{%- endfor %}

{% if modified is defined and modified | length > 0 %}
## Textes modifiés
{% for m in modified %}
* [Loi N°{{ m.law }}]({{ m.law }}.md)
 {%- for article in m.articles %}
 * [Article {{ article.id }}]({{ m.law }}-{{ article.id }}.md)
 {%- endfor %}
{%- endfor %}

{%- endif %}
