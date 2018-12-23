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

    def __init__(self, text=None):
        self.filename = ''
        self.content = {}
        self.begin = 0
        self.end = -1
        self.text = text
        super(AddDiffVisitor, self).__init__()

    def compute_location(self, type, typestring, node):
        if self.filename in self.content:
            content = self.content[self.filename]
        elif self.text:
            content = self.text
        else:
            raise ValueError
        end = self.end if self.end >= 0 else self.end + len(content)+1
        match = list(re.finditer(AddDiffVisitor.REGEXP[type], content[self.begin:end]))
        if 'position' in node and node['position'] == 'after':
            if node['order'] < 0:
                node['order'] += len(match)+1
            if node['order'] >= len(match):
                node['error'] = '[SedLex] visit_alinea_reference_node: node[\'order\'] == '+str(node['order'])+' >= len(match) == '+str(len(match))
                return
            match = match[node['order']]
            self.begin += match.start()
        else:
            if node['order'] < 0:
                node['order'] += len(match)+1
            if node['order'] - 1 >= len(match):
                node['error'] = '[SedLex] visit_'+typestring+'_node: node[\'order\']-1 == '+str(node['order'])+'-1 >= len(match) == '+str(len(match))
                return
            match = match[node['order'] - 1]
            self.begin += match.start()
            self.end = self.begin + len(match.group(1))

    def visit_alinea_reference_node(self, node, post):
        if post:
            return
        self.compute_location(tree.TYPE_ALINEA_REFERENCE, 'alinea_reference', node)

    def visit_sentence_reference_node(self, node, post):
        if post:
            return
        self.compute_location(tree.TYPE_SENTENCE_REFERENCE, 'sentence_reference', node)

    def visit_header1_reference_node(self, node, post):
        if post:
            return
        self.compute_location(tree.TYPE_HEADER1_REFERENCE, 'header1_reference', node)

    def visit_header2_reference_node(self, node, post):
        if post:
            return
        self.compute_location(tree.TYPE_HEADER2_REFERENCE, 'header2_reference', node)

    def visit_header3_reference_node(self, node, post):
        if post:
            return
        self.compute_location(tree.TYPE_HEADER2_REFERENCE, 'header3_reference', node)

    def visit_words_reference_node(self, node, post):
        if post:
            return

        if self.filename in self.content:
            content = self.content[self.filename]
        elif self.text:
            content = self.text
        else:
            raise ValueError
        end = self.end if self.end >= 0 else self.end + len(content)+1

        if 'children' in node and node['children'][0]['type'] == 'quote':
            words = node['children'][0]['words'].strip()
            location = content[self.begin:end].lower().find(words.lower())
            if location == -1:
                raise Exception('words not found')
            if 'position' in node and node['position'] == 'after':
                self.begin += content[self.begin:end].lower().find(words.lower()) + len(words)
            else:
                self.begin += content[self.begin:end].lower().find(words.lower())
                self.end = self.begin + len(words)

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
        self.end = -1

    def visit_edit_node(self, node, post):
        if not post:
            self.filename = ''
            self.content = {}
            self.begin = 0
            self.end = -1
            return

        article_reference_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_ARTICLE_REFERENCE)
        article_definition_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_ARTICLE_DEFINITION)
        editTypeArticle = 'edit'
        if node['editType'] == 'add' and len(article_definition_node):
            editTypeArticle = 'add'
        if not article_reference_node and not self.text and editTypeArticle == 'edit':
            node['error'] = '[SedLex] visit_edit_node: no article reference node'
            return
        if len(article_reference_node) > 1:
            node['error'] = '[SedLex] visit_edit_node: multiple article reference nodes'
            return

        filename = 'unnamed article'
        if article_reference_node:
            filename = article_reference_node[0]['filename']
            id = article_reference_node[0]['id']
        elif article_definition_node:
            filename = article_definition_node[0]['filename']
            id = article_definition_node[0]['id']

        if editTypeArticle == 'edit':
            if filename in self.content:
                old_content = self.content[filename]
            elif self.text:
                old_content = self.text
            else:
                node['error'] = '[SedLex] visit_edit_node: filename == '+filename+' should have been read'
                return
        else:
            old_content = None

        new_content = old_content
        new_words = None
        diff = (None, None, None)
        end = self.end if self.end >= 0 else self.end + len(old_content)+1

        try:
            if node['editType'] in ['replace', 'edit']:
                # replace words
                def_node = parser.filter_nodes(node, tree.is_definition)
                if not def_node:
                    node['error'] = '[SedLex] visit_edit_node: no definition node found in editType in [\'replace\', \'edit\']'
                    return
                def_node = def_node[-1]
                new_words = def_node['children'][0]['words']
                diff = (self.begin, old_content[self.begin:end], new_words)
            elif node['editType'] == 'delete':
                art_ref_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_ARTICLE_REFERENCE)
                other_ref_nodes = parser.filter_nodes(node, lambda x: x['type'] not in [tree.TYPE_EDIT, tree.TYPE_ARTICLE_REFERENCE, tree.TYPE_CODE_REFERENCE, tree.TYPE_LAW_REFERENCE])
                if art_ref_node and not other_ref_nodes:
                    new_content = None
                else:
                    new_words = ''
                diff = (self.begin, old_content[self.begin:end], None)
            elif node['editType'] == 'add':
                def_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)[-1]
                # add a word
                if node['children'][1]['type'] == tree.TYPE_WORD_DEFINITION:
                    new_words = def_node['words'] + old_content[self.begin:end]
                    diff = (self.begin, None, def_node['words'])
                elif node['children'][1]['type'] == tree.TYPE_SENTENCE_DEFINITION:
                    new_words = old_content[self.begin:end] + ' ' + def_node['words']
                    diff = (end, None, def_node['words'])
                # add an alinea
                elif node['children'][1]['type'] in [tree.TYPE_ALINEA_DEFINITION, tree.TYPE_HEADER1_DEFINITION, tree.TYPE_HEADER2_DEFINITION, tree.TYPE_HEADER3_DEFINITION]:
                    art_ref_node = parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_ARTICLE_REFERENCE)
                    other_ref_nodes = parser.filter_nodes(node, lambda x: tree.is_reference(x) and x['type'] not in [tree.TYPE_ARTICLE_REFERENCE, tree.TYPE_CODE_REFERENCE, tree.TYPE_LAW_REFERENCE])
                    if art_ref_node and not other_ref_nodes:
                        self.begin = end
                    new_words = '\n' + '\n'.join([
                        n['words'] for n in parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)
                    ]).strip()
                    diff = (self.begin, None, new_words)
                    if self.begin < end:
                        new_words += '\n' + old_content[self.begin:end]
                # add an article
                elif node['children'][1]['type'] == tree.TYPE_ARTICLE_DEFINITION:
                    new_words = '\n'.join([
                        n['words'] for n in parser.filter_nodes(node, lambda x: x['type'] == tree.TYPE_QUOTE)
                    ])
                    self.begin = 0
                    self.end = -1
                    diff = (self.begin, None, new_words)
                    # Note the following instructions are a specific case when an article-ref is replaced by a new article-def, it would not work if there is no article-ref
                    if 'id' in node['children'][1] and node['children'][1]['id'] != id:
                        id = node['children'][1]['id']
                        filename = re.sub(r'Article_(.*)\.md$', 'Article_'+id+'.md', filename)
                        old_content = None
            if new_words != None:
                new_content, left, new_words, right, self.begin, self.end = typography(old_content, new_words, self.begin, self.end)
                if diff[1]:
                    diff = (self.begin, old_content[self.begin:end], new_words)
                elif old_content != None:
                    new_content_bis, left_bis, new_words_bis, right_bis, begin_bis, end_bis = typography(old_content, diff[2], diff[0], diff[0])
                    diff = (begin_bis, old_content[begin_bis:end_bis], new_words_bis)

            old_content_list = old_content.splitlines() if old_content else []
            new_content_list = new_content.splitlines() if new_content else []
            unified_diff = difflib.unified_diff(
                old_content_list,
                new_content_list,
                tofile='\"' + filename + '\"' if new_content != None else '/dev/null',
                fromfile='\"' + filename + '\"' if old_content != None else '/dev/null'
            )
            unified_diff = list(unified_diff)
            if len(unified_diff) > 0:
                node['diff'] = ('\n'.join(unified_diff)).replace('\n\n', '\n') # investigate why double newlines
                #node['htmlDiff'] = diff.make_html_rich_diff(old_content, new_content, self.filename)
            if diff[1] or diff[2]:
                node['exactDiff'] = '--- ' + ('"' + filename + '"' if old_content != None else '/dev/null') + '\n' + \
                                    '+++ ' + ('"' + filename + '"' if new_content != None else '/dev/null') + '\n'
                if diff[0] < 0:
                    diff = (diff[0]+len(old_content), diff[1], diff[2])
                # Modify a part of the text
                if diff[1] != None and diff[2] != None:
                    node['exactDiff'] += '@@ -%d,%d +%d,%d @@' %(diff[0]+1,len(diff[1]),diff[0]+1,len(diff[2]))
                # Remove the entire article
                elif diff[1] != None and diff[2] == None:
                    if diff[0] != 0:
                        raise Exception('Article removed but index was not at the beginning')
                    node['exactDiff'] += '@@ -1,%d +0,0 @@' %(len(diff[1]))
                # Add an entire article
                elif diff[1] == None and diff[2] != None:
                    if diff[0] != 0:
                        raise Exception('Article added but index was not at the beginning')
                    node['exactDiff'] += '@@ -0,0 +1,%d @@' %(len(diff[2]))
                else:
                    raise Exception('Empty diff, should not happen')
                if diff[1]:
                    node['exactDiff'] += '\n-' + diff[1].replace('\n','\n-')
                if diff[2]:
                    node['exactDiff'] += '\n+' + diff[2].replace('\n','\n+')
            node['text'] = old_content

            # See issue #1: it seems that the source text for each verb is the original text and not the text already modified in earlier changes
            #if node['parent']['type'] != tree.TYPE_AMENDMENT or node['parent']['status'] == 'approved':
            #    self.set_content(self.filename, new_content)
        except Exception as e:
            # FIXME: proper error message
            raise e

def typography(old_content, new_words, begin, end):

    # Replace simple newlines by double newlines (Markdown syntax for new paragraphs)
    new_words = re.sub(r'(^|[^\n])\n([^\n]|$)', r'\1\n\n\2', new_words.strip(' '))
    new_words = re.sub(r'(^|[^\n])\n{3,}([^\n]|$)', r'\1\n\n\2', new_words)

    if not old_content:
        return new_words, '', new_words, '', begin, end

    right = old_content[end:]
    left = old_content[:begin]

    # Remove orphan spaces before or after the introduced words
    left_spaces = ''
    right_spaces = ''
    if right:
        right_re = re.search(r'^( *)[^ ]', right)
        if right_re:
            right_spaces = right_re.group(1)
            end += len(right_spaces)
            right = old_content[end:]
    if left:
        left_re = re.search(r'[^ ]( *)$', left)
        if left_re:
            left_spaces = left_re.group(1)
            begin -= len(left_spaces)
            left = old_content[:begin]

    # Add a sigle space before or after the introduced words depending if we have two letters or point/comma/colon/semicolon + letter
    if new_words and right and re.match(r'^[.,:;]?[0-9a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ]+$', new_words[-1]+right[0], flags=re.IGNORECASE):
        new_words = new_words+' '
    if new_words and left and re.match(r'^[.,:;]?[0-9a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ]+$', left[-1]+new_words[0], flags=re.IGNORECASE):
        new_words = ' '+new_words
    if not new_words and right and left and re.match(r'^[.,:;]?[0-9a-záàâäéèêëíìîïóòôöøœúùûüýỳŷÿ]+$', left[-1]+right[0], flags=re.IGNORECASE):
        new_words = ' '+new_words

    # Transfer spaces to old_content if common with the new_words to minimise the length of new_words
    if new_words and new_words[0] == ' ' and left_spaces:
        new_words = new_words[1:]
        begin += 1
        left = old_content[:begin]
    if new_words and new_words[-1] == ' ' and right_spaces:
        new_words = new_words[:-1]
        end -= 1
        right = old_content[end:]

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

    return left+new_words+right, left, new_words, right, begin, end

# vim: set ts=4 sw=4 sts=4 et:
