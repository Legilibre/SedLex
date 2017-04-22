# <i class="fa fa-balance-scale"></i> Loi N°{{ modified[current_law].law }}, Article {{ modified[current_law].articles[current_article].id }}

## <i class="fa fa-file-text-o"></i> Texte

{{ modified[current_law].articles[current_article].diff }}

## <i class="fa fa-pencil-square-o"></i> Modifications

{% for commit in modified[current_law].articles[current_article].commits %}
* [{{ commit.title }}]({{ commit.link }})
{% endfor %}
