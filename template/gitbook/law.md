{%- import 'html.j2' as html -%}

# {{ html.icon('balance-scale') }} Loi N°{{ modified[current_law].law }}

## {{ html.icon('pencil-square-o') }} Articles modifiés

{{ 'La' if 'proposition' in type else 'Le' }} {{ type }} modifie les articles de la loi N°{{ modified[current_law].law }} suivants :

{%- for article in modified[current_law].articles %}
* [Article {{ article.id }}]({{ modified[current_law].law }}-{{ article.id }}.md)
{%- endfor %}
