{%- import 'html.j2' as html -%}

# {{ html.icon('university" aria-hidden="true') }} {{ title | title }}

[{{ html.icon('external-link" aria-hidden="true') }} Texte original]({{ url }})

## {{ html.icon('bookmark-o') }} Articles

{{ 'La' if 'proposition' in type else 'Le' }} {{ type }} est constitué{{ 'e' if 'proposition' in type}} des articles suivants :

{% for article in articles %}
* [Article {{ article.order }}](article-{{ article.order }}.md)
{%- endfor %}

{% if modified is defined and modified | length > 0 %}
## {{ html.icon('file-text-o') }} Textes modifiés

{{ 'La' if 'proposition' in type else 'Le' }} {{ type }} modifie les textes suivants :

{% for m in modified %}
* [Loi N°{{ m.law }}]({{ m.law }}.md)
 {%- for article in m.articles %}
 * [Article {{ article.id }}]({{ m.law }}-{{ article.id }}.md)
 {%- endfor %}
{%- endfor %}

{%- endif %}

{% if cocorico_vote is defined %}
## Vote

* [Voter](https://cocorico.cc/embed/vote-widget/{{ cocorico_vote }})
* [Résultats du vote](https://cocorico.cc/ballot-box/{{ cocorico_vote }})
{% endif %}
