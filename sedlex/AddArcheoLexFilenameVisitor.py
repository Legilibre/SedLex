import os

from duralex.AbstractVisitor import AbstractVisitor
import duralex.tree as tree

class AddArcheoLexFilenameVisitor(AbstractVisitor):
    def __init__(self, repository):
        self.base = repository
        super(AddArcheoLexFilenameVisitor, self).__init__()

    def visit_article_reference_node(self, node, post):
        if post:
            return

        node_law = node
        while 'parent' in node_law and node_law['type'] != tree.TYPE_CODE_REFERENCE and node_law['type'] != tree.TYPE_LAW_REFERENCE:
            node_law = node_law['parent']
        node['filename'] = os.path.join(node_law['repository'], 'Article_' + node['id'] + '.md')

    def visit_article_definition_node(self, node, post):
        if post:
            return

        node_law = node
        while 'parent' in node_law and node_law['type'] != tree.TYPE_CODE_REFERENCE and node_law['type'] != tree.TYPE_LAW_REFERENCE:
            node_law = node_law['parent']
        # TODO: ugly: add an article but code/law only specified in reference, a visitor should previously wrap this article-def in a code-def
        if 'repository' not in node_law:
            node_law = node
            while 'parent' in node_law and node_law['type'] != tree.TYPE_EDIT:
                node_law = node_law['parent']
            node_law = tree.filter_nodes(node_law, lambda x: x['type'] in [tree.TYPE_CODE_REFERENCE, tree.TYPE_LAW_REFERENCE])[0]
        node['filename'] = os.path.join(node_law['repository'], 'Article_' + node['id'] + '.md')

    def visit_code_reference_node(self, node, post):
        if post:
            return

        node['repository'] = os.path.join(self.base, node['id'])

    def visit_law_reference_node(self, node, post):
        if post:
            return

        node['repository'] = os.path.join(self.base, 'loi_' + node['id'])
