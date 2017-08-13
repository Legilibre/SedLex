# -*- coding: utf-8 -*-

from duralex.AbstractVisitor import AbstractVisitor
from AddCommitMessageVisitor import int_to_roman
import template
import diff

from duralex.alinea_parser import *
import duralex.tree as tree

from bs4 import BeautifulSoup
import jinja2

import os
import subprocess
import tempfile
from distutils.dir_util import copy_tree

class CreateGitBookVisitor(AbstractVisitor):
    def __init__(self, args):
        self.gitbook_dir = args.gitbook
        self.tmp_dir = tempfile.mkdtemp()
        self.formats = args.gitbook_format

        super(CreateGitBookVisitor, self).__init__()

    def write_file(self, filename, data):
        f = open(self.tmp_dir + '/' + filename, 'w')
        f.write(data.encode('utf-8'))
        f.close()

    def get_article_commit_title(self, node):
        ancestors = get_node_ancestors(node)
        messages = []
        for ancestor in ancestors:
            if 'type' not in ancestor:
                continue;
            if ancestor['type'] == tree.TYPE_BILL_ARTICLE:
                messages.append('Article ' + str(ancestor['order']))
            elif ancestor['type'] == tree.TYPE_AMENDMENT:
                messages.append('Amendement ' + str(ancestor['id']))
            elif ancestor['type'] == tree.TYPE_HEADER1:
                messages.append(int_to_roman(ancestor['order']))
            elif ancestor['type'] == tree.TYPE_HEADER2:
                messages.append(unicode(ancestor['order']) + u'°')
            elif ancestor['type'] == tree.TYPE_HEADER3:
                messages.append(unicode(chr(ord('a') + ancestor['order'])) + u')')
        return ', '.join(messages[::-1])

    def get_article_commit_diff(self, edit, target_title, target_href):
        if 'htmlDiff' in edit:
            soup = BeautifulSoup(edit['htmlDiff'], "html5lib")
            filename_div = soup.find('div', {'class': 'diff-filename'})
            a_tag = soup.new_tag('a', href=target_href)
            a_tag.string = target_title
            filename_div.string = ''
            filename_div.append(a_tag)
            return unicode(soup.body.div)
        elif 'diff' in edit:
            process = subprocess.Popen(
                'diff2html -i stdin -d word -o stdout --su hidden -s line',
                shell=True,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = process.communicate(input=edit['diff'].encode('utf-8') + '\n')
            soup = BeautifulSoup(out, "html5lib")
            return (str(list(soup.find_all('style'))[0]) + '\n\n'
                + unicode(soup.find('div', {'id': 'diff'})))

    def get_commits(self, node):
        edit_nodes = filter_nodes(node, lambda n: 'type' in n and n['type'] == tree.TYPE_EDIT)
        commits = []
        for edit_node in edit_nodes:
            article_refs = filter_nodes(edit_node, lambda n: n['type'] == tree.TYPE_ARTICLE_REFERENCE)
            # FIXME: amendment that targets a bill article and not a law/code article
            if len(article_refs) == 0:
                continue
            article_ref = article_refs[0]
            target_title, target_href = self.get_deep_link(self.get_edit_target_nodes(article_ref))
            commits.append({
                'title': self.get_article_commit_title(edit_node),
                # remove the " ({reference list})" from the commit message since its already printed
                # in the header above
                'description': re.sub(r' \(.*\)', '', edit_node['commitMessage'].splitlines()[0]) if 'commitMessage' in edit_node else None,
                'diff': self.get_article_commit_diff(edit_node, target_title, target_href),
                'target': {
                    'title': target_title,
                    'link': target_href
                }
            })
        return commits

    def get_articles(self, node):
        articles = []
        article_nodes = filter_nodes(node, lambda n: n['type'] == tree.TYPE_BILL_ARTICLE)
        for article_node in article_nodes:
            articles.append({
                'order': article_node['order'],
                'content': article_node['content'],
                'commits': self.get_commits(article_node),
                'githubIssue': article_node['githubIssue'] if 'githubIssue' in article_node else None,
                'gitlabIssue': article_node['gitlabIssue'] if 'gitlabIssue' in article_node else None
            })
        return articles

    def get_amendments(self, node):
        amendments = []
        amendment_nodes = filter_nodes(node, lambda n: n['type'] == tree.TYPE_AMENDMENT)
        for amendment_node in amendment_nodes:
            amendments.append({
                'id': amendment_node['id'],
                'content': amendment_node['content'],
                'commits': self.get_commits(amendment_node),
                'signatories': amendment_node['signatories'],
                'description': amendment_node['description'],
            })
        return amendments

    def merge_dicts(self, *dict_args):
        """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
        """
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result

    def visit_node(self, node):
        super(CreateGitBookVisitor, self).visit_node(node)

        if tree.is_root(node):
            edits = self.build_edit_matrix(node)
            articles = self.get_articles(node)
            amendments = self.get_amendments(node)
            modified_texts = self.get_modified_texts(edits)
            template_data = {
                'title': self.get_book_title(node),
                'url': node['url'],
                'type': node['type'],
                'description': node['description'],
                'modified': modified_texts,
                'articles': articles,
                'amendments': amendments,
                'tree': node,
            }

            if 'cocoricoVote' in node:
                template_data['cocorico_vote'] = node['cocoricoVote']

            template.template_file(
                'gitbook/book.json.j2',
                template_data,
                os.path.join(self.tmp_dir, 'book.json')
            )
            template.template_file(
                'gitbook/styles/website.css.j2',
                template_data,
                os.path.join(self.tmp_dir, 'styles/website.css')
            )
            template.template_file(
                'gitbook/SUMMARY.md.j2',
                template_data,
                os.path.join(self.tmp_dir, 'SUMMARY.md')
            )
            template.template_file(
                'gitbook/README.md.j2',
                template_data,
                os.path.join(self.tmp_dir, 'README.md')
            )
            current_article = 0
            for article in articles:
                template.template_file(
                    'gitbook/article.md.j2',
                    self.merge_dicts(template_data, {'current_article': current_article}),
                    os.path.join(self.tmp_dir, 'article-' + str(article['order']) + '.md')
                )
                current_article += 1

            current_amendment = 0
            for amendment in amendments:
                template.template_file(
                    'gitbook/amendment.md.j2',
                    self.merge_dicts(template_data, {'current_amendment': current_amendment}),
                    os.path.join(self.tmp_dir, 'amendment-' + str(amendment['id']) + '.md')
                )
                current_amendment += 1

            current_article = 0
            current_law = 0
            for modified in modified_texts:
                template.template_file(
                    'gitbook/law.md.j2',
                    self.merge_dicts(template_data, {
                        'current_law': current_law,
                    }),
                    os.path.join(self.tmp_dir, modified['law'] + '.md')
                )
                for article in modified['articles']:
                    template.template_file(
                        'gitbook/text.md.j2',
                        self.merge_dicts(template_data, {
                            'current_law': current_law,
                            'current_article': current_article
                        }),
                        os.path.join(self.tmp_dir, modified['law'] + '-' + article['id'] + '.md')
                    )
                    current_article += 1
                current_law += 1

            if 'html' in self.formats:
                self.cmd('gitbook install')
                self.cmd('gitbook build')

                if 'markdown' in self.formats:
                    copy_tree(self.tmp_dir, self.gitbook_dir)
                else:
                    copy_tree(os.path.join(self.tmp_dir, '_book'), self.gitbook_dir)
            else:
                copy_tree(self.tmp_dir, self.gitbook_dir)

    def cmd(self, command):
        process = subprocess.Popen(
            command,
            cwd=self.tmp_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process.communicate()

    def get_book_title(self, root_node):
        title = ''

        if root_node['type'] == tree.TYPE_LAW_PROJECT:
            title = 'Projet De Loi'
        elif root_node['type'] == tree.TYPE_LAW_PROPOSAL:
            title = 'Proposition De Loi'

        if 'id' in root_node:
            title += u' N°' + str(root_node['id'])
        if 'legislature' in root_node:
            title += ', ' + str(root_node['legislature']) + u'ème législature'
        return title

    def patch(self, original, unified_diff):
        fd, filename = input_file = tempfile.mkstemp()
        os.write(fd, original.encode('utf-8'))
        process = subprocess.Popen(
            'patch -r - -p0 --output=- ' + filename,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = process.communicate(input=unified_diff.encode('utf-8') + '\n')
        return ''.join(out).decode('utf-8')

    def get_deep_link(self, nodes):
        href = []
        title = []
        for node in nodes:
            if node['type'] == tree.TYPE_LAW_REFERENCE:
                title.append(u'Loi N°' + node['id'])
                href.append(node['id'])
            elif node['type'] == tree.TYPE_BILL_ARTICLE:
                title.append(u'Article ' + str(node['order']))
                href.append(u'article-' + str(node['order']) + '.md#article-' + str(node['order']))
            elif node['type'] == tree.TYPE_AMENDMENT:
                title.append(u'Amendment ' + node['id'])
                href.append(u'amendment-' + node['id'] + '.md#amendment-' + node['id'])
            elif node['type'] == tree.TYPE_ARTICLE_REFERENCE:
                title.append(u'Article ' + node['id'])
                href.append(node['id'] + '.md')
            elif node['type'] == tree.TYPE_HEADER1:
                title.append(int_to_roman(node['order']))
                href.append(int_to_roman(node['order']))
            elif node['type'] == tree.TYPE_HEADER2:
                title.append(unicode(node['order']) + u'°')
                href.append(str(node['order']) + u'°')
            elif ancestor['type'] == tree.TYPE_HEADER3:
                title.append(unicode(chr(ord('a') + ancestor['order'])) + u')')
                href.append(unicode(chr(ord('a') + ancestor['order'])) + u')')
        return (', '.join(title), '-'.join(href))

    def get_edit_target_nodes(self, node):
        nodes = []

        if tree.is_reference(node):
            nodes.append(node)

        nodes += filter(
            lambda n: tree.is_reference(n),
            get_node_ancestors(node)
        )

        return sorted(
            nodes,
            key=lambda n: tree.TYPE_REFERENCE.index(n['type'])
        )

    def get_edit_source_nodes(self, node):
        edit_source_types = [
            tree.TYPE_AMENDMENT,
            tree.TYPE_BILL_ARTICLE,
            tree.TYPE_HEADER1,
            tree.TYPE_HEADER2,
            tree.TYPE_HEADER3,
        ]

        return sorted(
            filter(
                lambda n: 'type' in n and n['type'] in edit_source_types,
                get_node_ancestors(node)
            ),
            key=lambda n: edit_source_types.index(n['type'])
        )

    def get_original_content(self, ref):
        if ref['type'] == tree.TYPE_BILL_ARTICLE_REFERENCE:
            bill_article = tree.filter_nodes(
                tree.get_root(ref),
                lambda n: n['type'] == tree.TYPE_BILL_ARTICLE and n['order'] == ref['order']
            )
            if len(bill_article) == 1:
                return bill_article[0]['content']
        elif ref['type'] == tree.TYPE_ARTICLE_REFERENCE:
            f = open(ref['filename'], 'r')
            text = f.read().decode('utf-8')
            f.close()
            return text

    def get_modified_texts(self, edits):
        modified = []
        edits = edits[tree.TYPE_BILL_ARTICLE]
        law_ids = set([i[0] for i in edits.keys()])
        for law_id in law_ids:
            law_edits = {k: v for k, v in edits.iteritems() if k[0] == law_id}
            articles = []
            for k, v in edits.iteritems():
                law_ref = filter_nodes(v[0][-1], lambda n: n['type'] in [tree.TYPE_LAW_REFERENCE, tree.TYPE_CODE_REFERENCE] and n['id'] == k[0])[0]
                article_ref = filter_nodes(law_ref, lambda n: n['type'] == tree.TYPE_ARTICLE_REFERENCE and n['id'] == k[1])[0]

                original_text = self.get_original_content(article_ref)
                text = original_text

                commits = []
                for edit_source in v:
                    title, href = self.get_deep_link(edit_source)
                    commits.append({'title': title, 'link': href})
                    edit_refs = filter_nodes(edit_source[-1], lambda n: n['type'] == tree.TYPE_EDIT)
                    for edit_ref in edit_refs:
                        if 'diff' in edit_ref:
                            text = self.patch(text, edit_ref['diff'])
                article = {
                    'id': k[1],
                    'diff': diff.make_html_rich_diff(original_text, text),
                    'commits': commits
                }
                if 'gitlabHistory' in article_ref:
                    article['gitlabHistory'] = article_ref['gitlabHistory']
                if 'githubHistory' in article_ref:
                    article['githubHistory'] = article_ref['githubHistory']
                articles.append(article)
            articles = sorted(articles, key=lambda x: x['id'].replace('-', ' '))
            modified.append({'law': law_id, 'articles': articles})
        return modified

    def build_edit_matrix(self, node):
        edits = {
            tree.TYPE_BILL_ARTICLE: {},
            tree.TYPE_AMENDMENT: {},
        }

        # fetch bill articles targeting law articles
        self.build_edit_matrix_for_types(
            node,
            edits[tree.TYPE_BILL_ARTICLE],
            [tree.TYPE_BILL_ARTICLE],
            [tree.TYPE_ARTICLE_REFERENCE],
            [tree.TYPE_LAW_REFERENCE, tree.TYPE_CODE_REFERENCE]
        )
        self.build_edit_matrix_for_types(
            node,
            edits[tree.TYPE_AMENDMENT],
            [tree.TYPE_AMENDMENT],
            [tree.TYPE_ARTICLE_REFERENCE],
            [tree.TYPE_LAW_REFERENCE, tree.TYPE_CODE_REFERENCE]
        )

        # fetch amendments targeting bill articles
        # self.build_edit_matrix_for_types(
        #     node,
        #     edits,
        #     [tree.TYPE_AMENDMENT],
        #     [tree.TYPE_BILL_ARTICLE_REFERENCE],
        #     None
        # )

        return edits

    def build_edit_matrix_for_types(self, node, edits, source_type, target_type, repo_types):
        article_refs = []
        sources = filter_nodes(
            node,
            lambda n: 'type' in n and n['type'] in source_type
        )
        for source in sources:
            article_refs += filter_nodes(
                source,
                lambda n: 'type' in n and n['type'] in target_type
            )
        for article_ref in article_refs:
            repo_refs = filter(
                lambda n: 'type' in n and n['type'] in repo_types,
                get_node_ancestors(article_ref)
            )
            if len(repo_refs) != 0:
                key = (repo_refs[0]['id'], article_ref['id'])
                if key not in edits:
                    edits[key] = []
                edits[key].append(self.get_edit_source_nodes(article_ref))
