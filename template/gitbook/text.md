# <i class="fa fa-balance-scale"></i> Loi N°{{ modified[current_law].law }}, Article {{ modified[current_law].articles[current_article].id }}

## <i class="fa fa-file-text-o"></i> Texte

{{ modified[current_law].articles[current_article].diff }}

## <i class="fa fa-pencil-square-o"></i> Modifications

{% if modified[current_law].articles[current_article].gitlabHistory is defined %}
[<i class="fa fa-code-fork"></i> Voir l'historique complet de cet article (expert)]({{ modified[current_law].articles[current_article].gitlabHistory }})
{% elif modified[current_law].articles[current_article].githubLink is defined %}
[<i class="fa fa-code-fork"></i> Voir l'historique complet de cet article (expert)]({{ modified[current_law].articles[current_article].githubHistory }})
{% endif %}

Cet article est modifié par les articles {{ 'de la' if 'proposition' in type else 'du' }} {{ type }} suivants :

{% for commit in modified[current_law].articles[current_article].commits %}
* [{{ commit.title }}]({{ commit.link }})
{% endfor %}
