# <i class="fa fa-bookmark-o"></i> {{ title | title }}, Article {{ articles[current_article].order }}

## <i class="fa fa-file-text-o"></i> Texte

{{ articles[current_article].content }}

## <i class="fa fa-pencil-square-o"></i> Suivi des modifications

[<i class="fa fa-code-fork"></i> Voir dans le système de gestion de versions (expert)]({{ articles[current_article].githubIssue }})

{% for commit in articles[current_article].commits %}
### {{ commit.title }}

{{ commit.description | default('') }}

{{ commit.diff }}
{% endfor %}
