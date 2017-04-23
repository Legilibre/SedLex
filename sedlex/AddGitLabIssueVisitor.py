# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor

from duralex.alinea_parser import *

import gitlab

class AddGitLabIssueVisitor(AbstractVisitor):
    def __init__(self, args):
        self.gitlab = gitlab.Gitlab('https://gitlab.com', args.gitlab_token)
        self.repo_name = args.gitlab_repository
        self.repo = self.gitlab.projects.get(self.repo_name)
        self.issues = self.repo.issues.list(state='opened')
        self.current_issue = -1

        super(AddGitLabIssueVisitor, self).__init__()

    def visit_edit_node(self, node, post):
        if post:
            return

        if 'commitMessage' not in node:
            node['commitMessage'] = '(#' + str(self.current_issue) + ')'
        else:
            node['commitMessage'] = node['commitMessage'] + '\nGitLab: #' + str(self.current_issue)


    def visit_node(self, node):
        if 'type' in node and node['type'] == 'article':
            title = 'Article ' + str(node['order'])
            description = node['content'].replace('\n', '\n\n')
            found = False
            for issue in self.issues:
                if issue.title == title:
                    found = True
                    self.current_issue = issue.iid
                    if issue.description != description:
                        issue.save(title=title, description=description)
            if not found:
                issue = self.gitlab.project_issues.create(
                    {
                        'title': title,
                        'description': description
                    },
                    project_id=self.repo.id
                )
                self.current_issue = issue.iid
            node['gitlabIssue'] = 'https://gitlab.com/' + self.repo_name + '/issues/' + str(self.current_issue)

        super(AddGitLabIssueVisitor, self).visit_node(node)
