# -*- coding: utf-8 -*-

from duralex.AbstractVisitor import AbstractVisitor

import duralex.tree
import subprocess

import os
import json
import tempfile

class InitializeGitRepositoryVisitor(AbstractVisitor):
    def __init__(self, args):
        self.repository = args.repository
        self.num_subtrees = 0
        self.rev_date = None

        super(InitializeGitRepositoryVisitor, self).__init__()

    def repository_is_initialized(self):
        return os.path.isdir(os.path.join(self.repository, '.git'))

    def visit_node(self, node):
        if duralex.tree.is_root(node):
            self.rev_date = node['date']
            if not os.path.isdir(self.repository):
                os.mkdir(self.repository)
            if not self.repository_is_initialized():
                self.git('init')
                # We cannot do anything until the repo's HEAD exists.
                # So we make a first dummy commit.
                # This commit will never be pushed: we will revert to the most recent subtree commit instead.
                self.git('commit --allow-empty -m "Initialisation du projet de loi." --author "SedLex <SedLex@Legilibre.fr>"')

        super(InitializeGitRepositoryVisitor, self).visit_node(node)

        if duralex.tree.is_root(node):
            # The "debug" branch will be used to store debug files with stdin, stdout, argv...
            self.git('branch debug')
            # The "pages" branch will be used to store the static HTML files for GitHub pages.
            self.git('branch gh-pages')
            pass

    def visit_code_reference_node(self, node, post):
        if post:
            return

        if os.path.isdir(os.path.join(self.repository, node['id'])):
            return

        self.git_subtree(
            'git@github.com:Assemblee-Citoyenne/' + node['id'],
            node['id'],
            u'Ajout du ' + node['id'] + '.'
        )

    def visit_law_reference_node(self, node, post):
        if post:
            return

        if os.path.isdir(os.path.join(self.repository, node['id'])):
            return

        self.git_subtree(
            'git@github.com:Assemblee-Citoyenne/loi_' + node['id'],
            node['id'],
            u'Ajout de la loi N°' + node['id'] + '.'
        )

    def visit_bill_article_node(self, node, post):
        if post:
            return

        git_filename = u'Article_' + unicode(node['order']) + u'.md'

        node['filename'] = os.path.join(self.repository, git_filename)
        article_file = open(node['filename'], 'w')
        article_file.write(node['content'].replace('\n', '\n\n').encode('utf-8'))
        article_file.truncate()
        article_file.close()

        self.git('add ' + git_filename)
        self.git(
            'commit ' + git_filename
            + ' -m "Ajout de l\'article ' + unicode(node['order']) + '"'
            + ' --author "SedLex <SedLex@Legilibre.fr>"'
        )

    # https://stackoverflow.com/questions/33855701/git-read-tree-removed-all-the-history#33856740
    def git_subtree(self, repo, prefix, message):
        self.git('remote add ' + prefix + ' ' + repo)
        self.git('fetch ' + prefix)
        rev_hash, err, rc = self.git('rev-list -n1 --before=' + self.rev_date + ' ' + prefix + '/master')
        rev_hash = rev_hash.strip()
        self.git('branch ' + prefix + ' ' + rev_hash)
        self.git('merge -sours --no-commit --allow-unrelated-histories --squash ' + prefix)
        self.git('read-tree --prefix=' + prefix + ' -u ' + prefix)
        self.git('commit -m "' + message + '" --author="SedLex <SedLed@Legilibre.fr>"')
        # self.git('branch -d ' + prefix)

    def git(self, command, path=None):
        # print('git ' + command)
        process = subprocess.Popen(
            'git ' + command,
            cwd=path or self.repository,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = process.communicate()
        return out, err, process.returncode
