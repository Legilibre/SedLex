# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor

from duralex.alinea_parser import *

from github import Github

import template

class AddGitHubIssueVisitor(AbstractVisitor):
    def __init__(self, args):
        self.github = Github(args.github_token)
        self.repo = self.github.get_repo(args.github_repository)
        self.issues = list(self.repo.get_issues())
        self.current_issue_number = -1
        self.current_issue_link = None

        super(AddGitHubIssueVisitor, self).__init__()

    def visit_edit_node(self, node, post):
        if post:
            return
        node['githubIssue'] = self.current_issue_link
        node['commitMessage'] = template.template_string('./template/github/commit_message.j2', {'edit': node})

    def visit_node(self, node):
        if 'type' in node and node['type'] == 'article':
            title = template.template_string('./template/github/issue_title.j2', { 'article': node })
            body = template.template_string('./template/github/issue_body.j2', { 'article': node })
            found = False
            for issue in self.issues:
                if issue.title == title:
                    found = True
                    self.current_issue_link = issue.html_url
                    node['githubIssue'] = self.current_issue_link
                    self.current_issue_number = issue.number
                    if issue.body != body:
                        issue.edit(title=title, body=body)
            if not found:
                issue = self.repo.create_issue(title=title, body=body)
                self.current_issue_link = issue.html_url
                node['githubIssue'] = self.current_issue_link
                self.current_issue_number = issue.number

        super(AddGitHubIssueVisitor, self).visit_node(node)
