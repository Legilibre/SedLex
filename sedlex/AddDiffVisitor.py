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
        self.begin += match.start()
        self.end = self.begin + len(match.group(1))

    def visit_sentence_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_SENTENCE_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin += match.start()
        self.end = self.begin + len(match.group(1))

    def visit_header1_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_HEADER1_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin += match.start()
        self.end = self.begin + len(match.group(1))

    def visit_header2_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_HEADER2_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin += match.start()
        self.end = self.begin + len(match.group(1))

    def visit_header3_reference_node(self, node, post):
        if post:
            return

        match = re.finditer(AddDiffVisitor.REGEXP[tree.TYPE_HEADER3_REFERENCE], self.content[self.filename][self.begin:self.end])
        match = list(match)[node['order'] - 1 if node['order'] > 0 else node['order']]
        self.begin += match.start()
        self.end = self.begin + len(match.group(1))

    def visit_words_reference_node(self, node, post):
        if post:
            return

        if 'children' in node and node['children'][0]['type'] == 'quote':
            if 'position' in node and node['position'] == 'after':
                self.begin += (self.content[self.filename][self.begin:self.end].find(node['children'][0]['words'])
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
        new_words = None

        try:
            if node['editType'] in ['replace', 'edit']:
                # replace words
                def_node = parser.filter_nodes(node, lambda x: tree.is_definition(x))[-1]
                if def_node['type'] == tree.TYPE_WORD_DEFINITION:
                    new_words = def_node['children'][0]['words']
            elif node['editType'] == 'delete':
                art_ref_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_ARTICLE_REFERENCE)
                other_ref_nodes = parser.filter_nodes(node, lambda x: x['type'] not in [tree.TYPE_EDIT, tree.TYPE_ARTICLE_REFERENCE, tree.TYPE_CODE_REFERENCE, tree.TYPE_LAW_REFERENCE])
                if art_ref_node and not other_ref_nodes:
                    new_content = None
                else:
                    new_words = ''
            elif node['editType'] == 'add':
                def_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)[-1]
                # add a word
                if node['children'][1]['type'] == tree.TYPE_WORD_DEFINITION:
                    new_words = def_node['words'] + old_content[self.begin:self.end] # not sure about the 2nd part - see XVe pl911 article 2
                # add an alinea
                elif node['children'][1]['type'] == tree.TYPE_ALINEA_DEFINITION:
                    new_content += '\n' + '\n'.join([
                        n['words'] for n in parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)
                    ])
                # add an article
                elif node['children'][1]['type'] == tree.TYPE_ARTICLE_DEFINITION:
                    new_content = '\n'.join([
                        n['words'] for n in parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)
                    ])
            if new_words != None:
                new_content, self.begin, self.end = typography(old_content, new_words, self.begin, self.end)

            unified_diff = difflib.unified_diff(
                old_content.splitlines() if old_content else [],
                new_content.splitlines() if new_content else [],
                tofile=('\"' + self.filename + '\"' if new_content != None else '/dev/null'),
                fromfile='\"' + self.filename + '\"'
            )
            unified_diff = list(unified_diff)
            if len(unified_diff) > 0:
                node['diff'] = ('\n'.join(unified_diff)).replace('\n\n', '\n') # investigate why double newlines
                #node['htmlDiff'] = diff.make_html_rich_diff(old_content, new_content, self.filename)

            # See issue #1: it seems that the source text for each verb is the original text and not the text already modified in earlier changes
            #if node['parent']['type'] != tree.TYPE_AMENDMENT or node['parent']['status'] == 'approved':
            #    self.set_content(self.filename, new_content)
        except Exception as e:
            # FIXME: proper error message
            raise e

def typography(old_content, new_words, begin, end):

    # Replace simple newlines by double newlines (Markdown syntax for new paragraphs)
    new_words = re.sub(r'([^\n])\n([^\n])', r'\1\n\n\2', new_words.strip())

    if not old_content:
        return new_words, begin, end

    right = old_content[end:]
    left = old_content[:begin]

    # Remove orphan spaces before or after the introduced words
    if right:
        right_re = re.search(r'^( *)[^ ]', right)
        end += len(right_re.group(1)) if right_re else 0
        right = old_content[end:]
    if left:
        left_re = re.search(r'[^ ]( *)$', left)
        begin -= len(left_re.group(1)) if left_re else 0
        left = old_content[:begin]

    # Add a sigle space before or after the introduced words depending if we have two letters or point/comma/colon/semicolon + letter
    if new_words and right and re.match(r'^[.,:;]?[0-9a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ]+$', new_words[-1]+right[0], flags=re.IGNORECASE):
        new_words = new_words+' '
    if new_words and left and re.match(r'^[.,:;]?[0-9a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ]+$', left[-1]+new_words[0], flags=re.IGNORECASE):
        new_words = ' '+new_words

    # Remove empty alineas
    if not new_words:
        left_re = re.search(r'[^\n](\n{2,})$', left)
        right_re = re.search(r'^(\n{2,})[^\n]', right)
        # Do not invert these two if: the specific case of the last alinea removed would not work
        if left_re and (right_re or re.search(r'^\n*$', right)):
            begin -= len(left_re.group(1))
            left = old_content[:begin]
        elif right_re and (left_re or not left):
            end += len(right_re.group(1))
            right = old_content[end:]

    return left+new_words+right, begin, end

# vim: set ts=4 sw=4 sts=4 et:
