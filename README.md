# SedLex

SedLex is a frontend generator for French bills compiled using [DuraLex](https://github.com/Legilibre/DuraLex).

## Installation

### Installing dependencies

```bash
pip install -r requirements.txt
```

### Fetching the original law texts

If you want to generate diffs, you will need to have the corresponding original law texts in the `data` directory.
This original data is expected to be a Git repositories created using  [Archeo-Lex](https://github.com/Legilibre/Archeo-Lex).

## Generating patch files

**Before generating patch files, you must fetch the corresponding original law texts. In order to do so, please read the ["Fetching the original law texts"](#fetching-the-original-law-texts) section.**

By default, the intermediary representation will not compute/feature the diff of each edit.
You must add the `--diff` switch to the command line:

```bash
duralex --file bill.html | ./bin/sedlex --diff
```

```json
{
  "children": [
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "type": "quote",
                  "words": "autorisé"
                }
              ],
              "type": "words"
            },
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "type": "quote",
                              "words": "défendu"
                            }
                          ],
                          "type": "words-reference"
                        }
                      ],
                      "order": 1,
                      "type": "sentence-reference"
                    }
                  ],
                  "filename": "data/code des instruments monétaires et des médailles/9.md",
                  "id": "9",
                  "type": "article-reference"
                }
              ],
              "codeName": "code des instruments monétaires et des médailles",
              "type": "code-reference"
            }
          ],
          "diff": "--- \"data/code des instruments monétaires et des médailles/9.md\"\n+++ \"data/code des instruments monétaires et des médailles/9.md\"\n@@ -1,6 +1,6 @@\n # titre 1\n \n-Il est expressément défendu à toutes personnes, quelles que soient les professions qu'elles exercent, de frapper ou de faire frapper des médailles, jetons ou pièces de plaisir, d'or, d'argent et autres métaux, ailleurs que dans les ateliers de la monnaie, à moins d'être munies d'une autorisation spéciale du ministre de l'économie et des finances.\n+Il est expressément autorisé à toutes personnes, quelles que soient les professions qu'elles exercent, de frapper ou de faire frapper des médailles, jetons ou pièces de plaisir, d'or, d'argent et autres métaux, ailleurs que dans les ateliers de la monnaie, à moins d'être munies d'une autorisation spéciale du ministre de l'économie et des finances.\n \n # titre 2\n ",
          "editType": "replace",
          "type": "edit"
        }
      ],
      "isNew": false,
      "order": 1,
      "type": "article"
    }
  ]
}
```

Then, using [jq](https://stedolan.github.io/jq/), it is easy to extract only the `diff` fields:

```bash
duralex --file bill.html | ./bin/sedlex --diff | jq -r '.. | .diff? | strings'
```

```patch
--- "data/code des instruments monétaires et des médailles/9.md"
+++ "data/code des instruments monétaires et des médailles/9.md"
@@ -1,6 +1,6 @@
 # titre 1

-Il est expressément défendu à toutes personnes, quelles que soient les professions qu'elles exercent, de frapper ou de faire frapper des médailles, jetons ou pièces de plaisir, d'or, d'argent et autres métaux, ailleurs que dans les ateliers de la monnaie, à moins d'être munies d'une autorisation spéciale du ministre de l'économie et des finances.
+Il est expressément autorisé à toutes personnes, quelles que soient les professions qu'elles exercent, de frapper ou de faire frapper des médailles, jetons ou pièces de plaisir, d'or, d'argent et autres métaux, ailleurs que dans les ateliers de la monnaie, à moins d'être munies d'une autorisation spéciale du ministre de l'économie et des finances.

 # titre 2
```

Such output can be written in a patch file to be applied later:

```bash
duralex --file bill.html | ./bin/sedlex --diff | jq -r '.. | .diff? | strings' > articles.patch
```

or it can be piped to apply the patch directly:

```bash
duralex --file bill.html | ./bin/sedlex --diff | jq -r '.. | .diff? | strings' | patch -p0
```

## Git Integration

SedLex can automagically apply each `edit` node into an actual Git commit by passing the `--git-commit` flag.

SedLex can also generate meaningful commit messages by passing the `--commit-message` flag.
For example, the following `edit` node:

```json
{
  "children": [
    {
      "children": [
        {
          "type": "quote",
          "words": "autorisé"
        }
      ],
      "type": "words"
    },
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "type": "quote",
                      "words": "défendu"
                    }
                  ],
                  "type": "words-reference"
                }
              ],
              "order": 1,
              "type": "sentence-reference"
            }
          ],
          "filename": "data/code des instruments monétaires et des médailles/9.md",
          "id": "9",
          "type": "article-reference"
        }
      ],
      "codeName": "code des instruments monétaires et des médailles",
      "type": "code-reference"
    }
  ],
  "editType": "replace",
  "type": "edit"
}
```

will generate the following commit message:

> Remplacer les mots "défendu" dans l'article 9 par les mots "autorisé" (Article 1).

Each commit message is added as a `commitMessage` field on the corresponding edit node:

```json
{
  "type": "edit",
  "editType": "replace",
  "commitMessage": "Remplacer les mots \"défendu\" dans l'article 9 par les mots \"autorisé\" (Article 1).",
  "children": [
      ...
  ]
}
```

## GitHub Integration

SedLex can automagically create a GitHub issue for each `article` node by passing the `--github-repository` and
`--github-token` flags. Such issue will also be referenced by the commit message of all the `edit` nodes that are
descendants of the corresponding `article` node. Thus, each edit/commit will reference the corresponding article/issue.
