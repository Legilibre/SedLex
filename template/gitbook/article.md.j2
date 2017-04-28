{%- import 'html.j2' as html -%}

# {{ html.icon('bookmark-o') }} {{ title | title }}, Article {{ articles[current_article].order }}

## {{ html.icon('file-text-o') }} Texte

{{ articles[current_article].content }}

## {{ html.icon('pencil-square-o') }} Suivi des modifications

{% if articles[current_article].gitlabIssue is defined %}
[{{ html.icon('code-fork') }} Voir dans le système de gestion de versions (expert)]({{ articles[current_article].gitlabIssue }})
{% elif articles[current_article].githubIssue is defined %}
[{{ html.icon('code-fork') }} Voir dans le système de gestion de versions (expert)]({{ articles[current_article].githubIssue }})
{% endif %}

L'article {{ articles[current_article].order }} {{ 'de la' if 'proposition' in type else 'du' }} {{ type }} apporte les modifications suivantes :

{% for commit in articles[current_article].commits %}
### {{ commit.title }}

{{ commit.description | default('') }}

{{ commit.diff }}
{% endfor %}
