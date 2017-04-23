# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor

import os

class AddGitLabHistoryLinkVisitor(AbstractVisitor):
    def __init__(self, args):
        self.repo = args.gitlab_repository
        self.law_id = None

        super(AddGitLabHistoryLinkVisitor, self).__init__()

    def visit_law_reference_node(self, node, post):
        if post:
            return
        self.law_id = node['lawId']

    def visit_article_reference_node(self, node, post):
        if post:
            return

        node['gitlabHistory'] = ('https://gitlab.com/'
            + self.repo + '/commits/master/'
            + 'loi_' + self.law_id + '/'
            + 'Article_' + node['id'] + '.md')
