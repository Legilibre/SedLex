# -*- coding: utf-8 -*-

from duralex.AbstractVisitor import AbstractVisitor

from duralex.alinea_parser import *

import duralex.tree

import re

def int_to_roman(integer):
    string = ''
    table = [
        ['M',1000], ['CM',900], ['D',500], ['CD',400], ['C',100], ['XC',90], ['L',50], ['XL',40], ['X',10], ['IX',9],
        ['V',5], ['IV',4], ['I',1]
    ]

    for pair in table:
        while integer - pair[1] >= 0:
            integer -= pair[1]
            string += pair[0]

    return string

class AddCommitMessageVisitor(AbstractVisitor):
    def __init__(self):
        self.ref_parts = []
        self.def_parts = []

        super(AddCommitMessageVisitor, self).__init__()

    def visit_law_reference_node(self, node, post):
        if post:
            return

        self.ref_parts.append(u'de la loi N°' + node['id'])

    def visit_article_reference_node(self, node, post):
        if post:
            return

        if 'children' in node and len(node['children']) > 0:
            self.ref_parts.append(u'de l\'article ' + node['id'])
        else:
            self.ref_parts.append(u'l\'article ' + node['id'])
            if 'position' in node and node['position'] == 'after':
                self.ref_parts.append(u'après')

    def visit_bill_article_reference_node(self, node, post):
        if post:
            return

        if duralex.tree.get_root(node)['type'] == duralex.tree.TYPE_LAW_PROJECT:
            self.ref_parts.append(u'du projet de loi')
        elif duralex.tree.get_root(node)['type'] == duralex.tree.TYPE_LAW_PROPOSAL:
            self.ref_parts.append(u'de la proposition de loi')

        if 'children' in node and len(node['children']) > 0:
            self.ref_parts.append(u'de l\'article ' + str(node['order']))
        else:
            self.ref_parts.append(u'l\'article ' + str(node['order']))
            if 'position' in node and node['position'] == 'after':
                self.ref_parts.append(u'après')

    def visit_alinea_reference_node(self, node, post):
        if post:
            return

        if 'children' in node and len(node['children']) > 0:
            if node['order'] == -1:
                self.ref_parts.append(u'du dernier alinéa')
            elif node['order'] == -2:
                self.ref_parts.append(u'de l\'avant-dernier alinéa')
            else:
                self.ref_parts.append(u'de l\'alinéa ' + str(node['order']))
        else:
            if node['order'] == -1:
                self.ref_parts.append(u'le dernier alinéa')
            elif node['order'] == -2:
                self.ref_parts.append(u'l\'avant-dernier alinéa')
            else:
                self.ref_parts.append(u'l\'alinéa ' + str(node['order']))

    def visit_sentence_reference_node(self, node, post):
        if post:
            return

        if node['order'] == 1:
            number_word = u'la 1ère'
        elif node['order'] == -1:
            number_word = u'la dernière'
        elif node['order'] == -1:
            number_word = u'l\'avant-dernière'
        else:
            number_word = u'la ' + node['order'] + u'ème'

        if 'children' in node and len(node['children']) > 0:
            self.ref_parts.append(u'de ' + number_word + ' phrase')
        else:
            self.ref_parts.append(number_word + ' phrase')

    def visit_words_reference_node(self, node, post):
        if post:
            return

        quotes = filter_nodes(node, lambda n: n['type'] == 'quote')
        quotes = ''.join([n['words'] for n in quotes])
        num_words = len(re.findall(r'\S+', quotes))

        if num_words == 1:
            self.ref_parts.append(u'le mot "' + quotes + '"')
        else:
            self.ref_parts.append(u'les mots "' + quotes + '"')

    def visit_header1_reference_node(self, node, post):
        if post:
            return

        # FIXME

    def visit_words_definition_node(self, node, post):
        if post:
            return

        quotes = filter_nodes(node, lambda n: n['type'] == 'quote')
        quotes = ''.join([n['words'] for n in quotes])
        num_words = len(re.findall(r'\S+', quotes))

        if num_words == 1:
            self.def_parts.append(u'le mot "' + quotes + '"')
        else:
            self.def_parts.append(u'les mots "' + quotes + '"')

    def visit_article_definition_node(self, node, post):
        if post:
            return

        self.def_parts.append(u'un article ' + node['id'])

    def visit_edit_node(self, node, post):
        if not post:
            self.ref_parts = []
            self.def_parts = []
            return

        edit_desc = ''
        if node['editType'] == 'delete':
            edit_desc = 'supprimer ' + ' '.join(self.ref_parts[::-1])
        elif node['editType'] == 'edit' or node['editType'] == 'replace':
            edit_desc = 'remplacer ' + ' '.join(self.ref_parts[::-1]) + ' par ' + ', '.join(self.def_parts)
        elif node['editType'] == 'add':
            edit_desc = ' '.join(self.ref_parts[::-1]) + ' ajouter ' + ' '.join(self.def_parts[::-1])

        origin = []
        ancestors = get_node_ancestors(node)
        for ancestor in ancestors:
            if 'type' not in ancestor:
                continue;

            if ancestor['type'] == duralex.tree.TYPE_AMENDMENT:
                origin.append('Amendement ' + ancestor['id'])
            if ancestor['type'] == duralex.tree.TYPE_BILL_ARTICLE:
                origin.append('Article ' + str(ancestor['order']))
            if ancestor['type'] == duralex.tree.TYPE_HEADER1:
                origin.append(int_to_roman(ancestor['order']))
            if ancestor['type'] == duralex.tree.TYPE_HEADER2:
                origin.append(unicode(ancestor['order']) + u'°')
            # FIXME: handle duralex.tree.TYPE_HEADER3
        origin = ', '.join(origin[::-1])

        node['commitMessage'] = edit_desc[0].upper() + edit_desc[1:] + ' (' + origin + ').'
