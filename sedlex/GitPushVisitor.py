# -*- coding: utf-8 -*-

from duralex.AbstractVisitor import AbstractVisitor

import subprocess
import os

class GitPushVisitor(AbstractVisitor):

    def __init__(self):
        self.repositories = []
        super(GitPushVisitor, self).__init__()

    def visit_node(self, node):
        if 'repository' in node:
            self.repositories.append(node['repository'])

        super(GitPushVisitor, self).visit_node(node)

        if 'parent' not in node:
            for repository in self.repositories:
                process = subprocess.Popen(
                    [
                        'git',
                        '-C', repository,
                        'push', '--all', 'origin'
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                out, err = process.communicate()
