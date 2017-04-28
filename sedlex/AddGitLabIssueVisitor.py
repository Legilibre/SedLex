# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor
import template

from duralex.alinea_parser import *

import gitlab

class AddGitLabIssueVisitor(AbstractVisitor):
    def __init__(self, args):
        self.gitlab = gitlab.Gitlab('https://gitlab.com', args.gitlab_token)
        self.repo_name = args.gitlab_repository
        self.repo = self.gitlab.projects.get(self.repo_name)
        self.issues = self.repo.issues.list(state='opened')
        self.current_issue_number = -1
        self.current_issue_link = None

        super(AddGitLabIssueVisitor, self).__init__()

    def visit_edit_node(self, node, post):
        if post:
            return
        node['gitlabIssue'] = self.current_issue_link
        node['commitMessage'] = template.template_string('./template/gitlab/commit_message.j2', {'edit': node})

    def visit_node(self, node):
        if 'type' in node and node['type'] == 'article':
            title = template.template_string('./template/gitlab/issue_title.j2', {'article': node})
            description = template.template_string('./template/gitlab/issue_description.j2', {'article': node})
            found = False
            for issue in self.issues:
                if issue.title == title:
                    found = True
                    self.current_issue_number = issue.iid
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
                self.current_issue_number = issue.iid
            self.current_issue_link = 'https://gitlab.com/' + self.repo_name + '/issues/' + str(self.current_issue_number)
            node['gitlabIssue'] = self.current_issue_link

        super(AddGitLabIssueVisitor, self).visit_node(node)
