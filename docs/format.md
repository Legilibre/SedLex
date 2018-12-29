Data format
===========

To compute the diff of an amendment on some amended text (e.g. an article of law proposal), the DuraLex tree passed to AddDiffVisitor should be:

```
{
  "children": [
    {
      "children": [
        {
          "children": [
            {
              …
            }
          ],
          "content": "Au premier alinéa, les mots \"quarante députés ou quarante sénateurs\" sont remplacés par les mots \"trente députés ou trente sénateurs\".",
          "type": "amendment"
        }
      ],
      "content": "Au sixième alinéa de l'article 16 de la Constitution, les mots : \"soixante députés ou soixante sénateurs\" sont remplacés par les mots : \"quarante députés ou quarante sénateurs\".",
      "order": 11,
      "type": "bill-article"
    }
  ],
  "type": "law-proposal"
}
```

If the DuraLex tree was already computed as `tree` and the root node has no type, it can be attached to its content:
```python
bill = duralex.tree.create_node(None, {'type': duralex.tree.TYPE_LAW_PROPOSAL})
bill_article = duralex.tree.create_node(bill, {'type': duralex.tree.TYPE_BILL_ARTICLE, 'content': 'Au sixième alinéa…', 'order': 11})
tree['type'] = duralex.tree.TYPE_AMENDMENT
tree['content'] = 'Au premier alinéa…'
duralex.tree.push_node(bill_article, tree)
amendment = tree
```

To compute the diff of the bill article or any in-force article (of type “modifying text”/“amendment”), it can be done similarly one level above. Or, if all texts modified by the bill article are available through Archéo Lex, it is not needed to encapsulate the DuraLex tree of the bill article in higher-level tree.
