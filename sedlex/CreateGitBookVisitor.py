# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor

from duralex.alinea_parser import *
from duralex.AddCommitMessageVisitor import int_to_roman
import duralex.node_type
import duralex.diff

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
            if ancestor['type'] == 'article':
                messages.append('Article ' + str(ancestor['order']))
            if ancestor['type'] == 'bill-header1' and 'implicit' not in ancestor:
                messages.append(int_to_roman(ancestor['order']))
            if ancestor['type'] == 'bill-header2':
                messages.append(unicode(ancestor['order']) + u'°')
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

    def get_articles(self, node):
        articles = []
        article_nodes = filter_nodes(node, lambda n: n['type'] == 'article')
        for article_node in article_nodes:
            edit_nodes = filter_nodes(article_node, lambda n: 'type' in n and n['type'] == 'edit')
            commits = []
            for edit_node in edit_nodes:
                article_ref = filter_nodes(edit_node, lambda n: n['type'] == 'article-reference')[0]
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

            articles.append({
                'order': article_node['order'],
                'content': article_node['content'].replace('\n', '\n\n'),
                'commits': commits,
                'githubIssue': article_node['githubIssue'] if 'githubIssue' in article_node else None,
                'gitlabIssue': article_node['gitlabIssue'] if 'gitlabIssue' in article_node else None
            })
        return articles

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

        if 'parent' not in node:
            edits = self.build_edit_matrix(node)
            articles = self.get_articles(node)
            modified_texts = self.get_modified_texts(edits)
            template_data = {
                'title': self.get_book_title(node),
                'url': node['url'],
                'type': node['type'],
                'modified': modified_texts,
                'articles': articles
            }

            if 'cocoricoVote' in node:
                template_data['cocorico_vote'] = node['cocoricoVote']

            self.template_file('book.json', template_data)
            self.template_file('styles/website.css', template_data)
            self.template_file('SUMMARY.md', template_data)
            self.template_file('README.md', template_data)
            current_article = 0
            for article in articles:
                self.template_file(
                    'article.md',
                    self.merge_dicts(template_data, {'current_article': current_article}),
                    'article-' + str(article['order']) + '.md'
                )
                current_article += 1

            current_article = 0
            current_law = 0
            for modified in modified_texts:
                self.template_file(
                    'law.md',
                    self.merge_dicts(template_data, {
                        'current_law': current_law,
                    }),
                    modified['law'] + '.md'
                )
                for article in modified['articles']:
                    self.template_file(
                        'text.md',
                        self.merge_dicts(template_data, {
                            'current_law': current_law,
                            'current_article': current_article
                        }),
                        modified['law'] + '-' + article['id'] + '.md'
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
        title = root_node['type'].title()
        if 'id' in root_node:
            title += u' N°' + str(root_node['id'])
        if 'legislature' in root_node:
            title += ', ' + str(root_node['legislature']) + u'ème législature'
        return title

    def patch(self, original, unified_diff):
        fd, filename = input_file = tempfile.mkstemp()
        os.write(fd, original.encode('utf-8'))
        process = subprocess.Popen(
            'patch -p0 --output=- ' + filename,
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
            if node['type'] == 'law-reference':
                title.append(u'Loi N°' + node['lawId'])
                href.append(node['lawId'])
            elif node['type'] == 'article':
                title.append(u'Article ' + str(node['order']))
                href.append(u'article-' + str(node['order']) + '.md#article-' + str(node['order']))
            elif node['type'] == 'article-reference':
                title.append(u'Article ' + node['id'])
                href.append(node['id'] + '.md')
            elif node['type'] == 'bill-header1' and 'implicit' not in node:
                title.append(int_to_roman(node['order']))
                href.append(int_to_roman(node['order']))
            elif node['type'] == 'bill-header2':
                title.append(unicode(node['order']) + u'°')
                href.append(str(node['order']) + u'°')
        return (', '.join(title), '-'.join(href))

    def get_edit_target_nodes(self, node):
        nodes = []

        if node_type.is_reference(node):
            nodes.append(node)

        nodes += filter(
            lambda n: node_type.is_reference(n),
            get_node_ancestors(node)
        )

        return sorted(
            nodes,
            key=lambda n: node_type.REFERENCE.index(n['type'])
        )

    def get_edit_source_nodes(self, node):
        edit_source_types = [
            'article',
            'bill-header1',
            'bill-header2'
        ]

        return sorted(
            filter(
                lambda n: 'type' in n and n['type'] in edit_source_types,
                get_node_ancestors(node)
            ),
            key=lambda n: edit_source_types.index(n['type'])
        )

    def get_modified_texts(self, edits):
        modified = []
        law_ids = set([i[0] for i in edits.keys()])
        for law_id in law_ids:
            law_edits = {k: v for k, v in edits.iteritems() if k[0] == law_id}
            articles = []
            for k, v in edits.iteritems():
                law_ref = filter_nodes(v[0][-1], lambda n: n['type'] == 'law-reference' and n['lawId'] == k[0])[0]
                article_ref = filter_nodes(law_ref, lambda n: n['type'] == 'article-reference' and n['id'] == k[1])[0]

                f = open(article_ref['filename'], 'r')
                text = f.read().decode('utf-8')
                original_text = text
                f.close()

                commits = []
                for edit_source in v:
                    title, href = self.get_deep_link(edit_source)
                    commits.append({'title': title, 'link': href})
                    edit_refs = filter_nodes(edit_source[-1], lambda n: n['type'] == 'edit')
                    for edit_ref in edit_refs:
                        text = self.patch(text, edit_ref['diff'])
                article = {
                    'id': k[1],
                    'diff': duralex.diff.make_html_rich_diff(original_text, text),
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
        edits = {}
        article_refs = filter_nodes(node, lambda n: 'type' in n and n['type'] == 'article-reference')
        for article_ref in article_refs:
            law_ref = filter(
                lambda n: 'type' in n and n['type'] == 'law-reference',
                get_node_ancestors(article_ref)
            )[0]
            t = (law_ref['lawId'], article_ref['id'])
            if t not in edits:
                edits[t] = []
            edits[t].append(self.get_edit_source_nodes(article_ref))
        return edits

    def template_file(self, template, values, out=None):
        f = open(os.path.join('./template/gitbook', template), 'r')
        t = jinja2.Environment(loader=jinja2.FileSystemLoader('./template/gitbook')).from_string(f.read().decode('utf-8'))
        f.close()

        filename = os.path.join(self.tmp_dir, out if out else template)
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(filename, 'w')
        f.write(t.render(values).encode('utf-8'))
        f.truncate()
        f.close()
