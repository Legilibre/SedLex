import os
import codecs
import re

from duralex.AbstractVisitor import AbstractVisitor
import duralex.tree as tree

class AddArcheoLexFilenameVisitor(AbstractVisitor):
    def __init__(self, repositoryArticles=None, repositoryFile=None):
        self.base = repositoryArticles
        self.baseFile = repositoryFile
        self.content = {}
        super(AddArcheoLexFilenameVisitor, self).__init__()

    def visit_article_reference_node(self, node, post):
        if post:
            return

        node_law = node
        while 'parent' in node_law and node_law['type'] != tree.TYPE_CODE_REFERENCE and node_law['type'] != tree.TYPE_LAW_REFERENCE:
            node_law = node_law['parent']
        if 'repository' in node_law:
            node['filename'] = os.path.join(node_law['repository'], 'Article_' + node['id'].replace(' ', '_') + '.md')
        if 'filename' in node_law and node_law['filename'] in self.content:
            content = re.search(r'\n\n#+ Article ' + node['id'] + '\n\n([^\n]*(\n([^\n]+|(\n[^#]*)))*)', '\n\n' + self.content[node_law['filename']])
            if content:
                node['content'] = content.group(1).strip()

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
            node_law = tree.filter_nodes(node_law, lambda x: x['type'] in [tree.TYPE_CODE_REFERENCE, tree.TYPE_LAW_REFERENCE])
            if len(node_law):
                node_law = node_law[0]
            else:
                node_law = None
        if node_law and 'repository' in node_law:
            node['filename'] = os.path.join(node_law['repository'], 'Article_' + node['id'].replace(' ', '_') + '.md')
        if node_law and 'filename' in node_law and node_law['filename'] in self.content:
            content = re.search(r'\n\n#+ Article ' + node['id'] + '\n\n([^\n]*(\n([^\n]+|(\n[^#]*)))*)', '\n\n' + self.content[node_law['filename']])
            if content:
                node['content'] = content.group(1).strip()

    def visit_code_reference_node(self, node, post):
        if post:
            return

        if self.base:
            node['repository'] = os.path.join(self.base, node['id'].replace(' ', '_'))
        if self.baseFile:
            node['filename'] = os.path.join(self.baseFile, node['id'].replace(' ', '_'), node['id'].replace(' ', '_') + '.md')
        if 'filename' in node and node['filename'] not in self.content:
            try:
                input_file = codecs.open(node['filename'], mode='r', encoding='utf-8').read()
                self.content[node['filename']] = input_file
            except FileNotFoundError:
                pass

    def visit_law_reference_node(self, node, post):
        if post:
            return

        node['repository'] = os.path.join(self.base, 'loi_' + node['id'].replace(' ', '_'))
        if self.baseFile:
            node['filename'] = os.path.join(self.baseFile, node['id'].replace(' ', '_'), node['id'].replace(' ', '_') + '.md')
        if 'filename' in node and node['filename'] not in self.content:
            try:
                input_file = codecs.open(node['filename'], mode='r', encoding='utf-8').read()
                self.content[node['filename']] = input_file
            except FileNotFoundError:
                pass

# vim: set ts=4 sw=4 sts=4 et:
