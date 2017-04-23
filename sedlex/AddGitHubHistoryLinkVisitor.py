# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor

class AddGitHubHistoryLinkVisitor(AbstractVisitor):
    def __init__(self, args):
        self.repo = args.github_repository
        self.law_id = None

        super(AddGitHubHistoryLinkVisitor, self).__init__()

    def visit_law_reference_node(self, node, post):
        if post:
            return

        self.law_id = node['lawId']

    def visit_article_reference_node(self, node, post):
        if post:
            return

        node['githubHistory'] = ('https://github.com/'
            + self.repo + '/commits/master/'
            + 'loi_' + self.law_id + '/'
            + 'Article_' + node['id'] + '.md')
