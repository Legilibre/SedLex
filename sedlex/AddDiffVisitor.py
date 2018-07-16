# -*- coding: utf-8 -*-

import codecs
import re
import difflib
import sys
import os

import duralex.alinea_parser as parser
import diff

from duralex.AbstractVisitor import AbstractVisitor

import duralex.tree as tree

class AddDiffVisitor(AbstractVisitor):
    REGEXP = {
        tree.TYPE_HEADER1_REFERENCE     : re.compile(r'([IVXCLDM]+\. - (?:(?:.|\n)(?![IVXCLDM]+\. - ))*)', re.UNICODE),
        tree.TYPE_HEADER2_REFERENCE     : re.compile(r'(\d+\. (?:(?:.|\n)(?!\d+\. ))*)', re.UNICODE),
        tree.TYPE_HEADER3_REFERENCE     : re.compile(r'([a-z]+\) (?:(?:.|\n)(?![a-z]+\) ))*)', re.UNICODE),
        tree.TYPE_ALINEA_REFERENCE      : re.compile(r'^(.+)$', re.UNICODE | re.MULTILINE),
        tree.TYPE_SENTENCE_REFERENCE    : re.compile(r'([A-ZÀÀÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏ].*?\.)', re.UNICODE),
        tree.TYPE_WORD_REFERENCE        : re.compile(r'(\b\w.*?\b)', re.UNICODE)
    }

    def __init__(self):
        self.filename = ''
        self.content = {}
        self.begin = 0
        self.end = -1
        super(AddDiffVisitor, self).__init__()

    def visit_alinea_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_ALINEA_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin = match.start()
        self.end = match.start() + len(match.group(1))

    def visit_sentence_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_SENTENCE_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin = match.start()
        self.end = match.start() + len(match.group(1))

    def visit_header1_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_HEADER1_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin = match.start()
        self.end = match.start() + len(match.group(1))

    def visit_header2_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_HEADER2_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin = match.start()
        self.end = match.start() + len(match.group(1))

    def visit_header3_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_HEADER3_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin = match.start()
        self.end = match.start() + len(match.group(1))

    def visit_words_reference_node(self, node, post):
        if post:
            return

        if 'children' in node and node['children'][0]['type'] == 'quote':
            if 'position' in node and node['position'] == 'after':
                self.begin = (self.content[self.filename][self.begin:self.end].find(node['children'][0]['words'])
                    + len(node['children'][0]['words']))
            else:
                self.begin += self.content[self.filename][self.begin:self.end].find(node['children'][0]['words'])
                self.end = self.begin + len(node['children'][0]['words'])

    def visit_article_reference_node(self, node, post):
        if post:
            return
        self.set_content_from_file(node['filename'])

    def visit_bill_article_reference_node(self, node, post):
        bill_article = tree.filter_nodes(
            tree.get_root(node),
            lambda n: n['type'] == tree.TYPE_BILL_ARTICLE and n['order'] == node['order']
        )
        if len(bill_article) == 1:
            self.set_content(bill_article[0]['order'], bill_article[0]['content'])

    def visit_article_definition_node(self, node, post):
        if post:
            return
        self.set_content_from_file(node['filename'])

    def set_content_from_file(self, filename):
        self.filename = filename
        if self.filename not in self.content:
            if os.path.isfile(self.filename):
                input_file = codecs.open(self.filename, mode="r", encoding="utf-8")
                self.set_content(self.filename, input_file.read())
            else:
                self.set_content(self.filename, '')

    def set_content(self, key, content):
        self.content[key] = content
        self.begin = 0
        self.end = len(content)

    def visit_edit_node(self, node, post):
        if not post:
            self.begin = 0
            self.end = -1
            return

        old_content = self.content[self.filename]
        new_content = old_content

        try:
            if node['editType'] == 'replace':
                # replace words
                def_node = parser.filter_nodes(node, lambda x: tree.is_definition(x))[-1]
                if def_node['type'] == tree.TYPE_WORD_DEFINITION:
                    new_content = old_content[0:self.begin] + def_node['children'][0]['words'] + old_content[self.end:]
            elif node['editType'] == 'delete':
                new_content = old_content[0:self.begin] + old_content[self.end:]
            elif node['editType'] == 'edit':
                def_node = parser.filter_nodes(node, lambda x: tree.is_definition(x))[-1]
                # edit words
                if def_node['type'] == tree.TYPE_WORD_DEFINITION:
                    new_content = old_content[0:self.begin] + def_node['children'][0]['words'] + old_content[self.end:]
            elif node['editType'] == 'add':
                # add an alinea
                if node['children'][1]['type'] == tree.TYPE_ALINEA_DEFINITION:
                    def_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)[-1]
                    new_content += '\n' + '\n'.join([
                        n['words'] for n in parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)
                    ])
                # add an article
                elif node['children'][1]['type'] == tree.TYPE_ARTICLE_DEFINITION:
                    def_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)[-1]
                    new_content = '\n'.join([
                        n['words'] for n in parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)
                    ])

            unified_diff = difflib.unified_diff(
                old_content.splitlines() if old_content != '' else [],
                new_content.splitlines() if new_content != '' else [],
                tofile='\"' + self.filename + '\"',
                fromfile='\"' + self.filename + '\"'
            )
            unified_diff = list(unified_diff)
            if len(unified_diff) > 0:
                node['diff'] = ('\n'.join(unified_diff)).replace('\n\n', '\n') # investigate why double newlines
                #node['htmlDiff'] = diff.make_html_rich_diff(old_content, new_content, self.filename)

            if node['parent']['type'] != tree.TYPE_AMENDMENT or node['parent']['status'] == 'approved':
                self.set_content(self.filename, new_content)
        except Exception as e:
            # FIXME: proper error message
            raise e
