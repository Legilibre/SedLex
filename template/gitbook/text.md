# <i class="fa fa-balance-scale"></i> Loi N°{{ modified[current_law].law }}, Article {{ modified[current_law].articles[current_article].id }}

## <i class="fa fa-file-text-o"></i> Texte

{{ modified[current_law].articles[current_article].diff }}

## <i class="fa fa-pencil-square-o"></i> Modifications

{% if modified[current_law].articles[current_article].gitlabLink is defined %}
[<i class="fa fa-code-fork"></i> Voir dans le système de gestion de versions (expert)]({{ modified[current_law].articles[current_article].gitlabLink }})
{% elif modified[current_law].articles[current_article].githubLink is defined %}
[<i class="fa fa-code-fork"></i> Voir dans le système de gestion de versions (expert)]({{ modified[current_law].articles[current_article].githubLink }})
{% endif %}

{% for commit in modified[current_law].articles[current_article].commits %}
* [{{ commit.title }}]({{ commit.link }})
{% endfor %}
