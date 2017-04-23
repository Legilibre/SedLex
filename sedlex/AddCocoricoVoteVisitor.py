# -*- coding: utf-8 -*-

from AbstractVisitor import AbstractVisitor

from duralex.alinea_parser import *

import requests

class AddCocoricoVoteVisitor(AbstractVisitor):
    def __init__(self, args):
        self.url = args.cocorico_url
        if not self.url:
            self.url = 'https://cocorico.cc'

        r = requests.post(
            self.url + '/api/oauth/token',
            auth=(args.cocorico_app_id, args.cocorico_secret),
            data={ 'grant_type': 'client_credentials' },
            verify=self.url != 'https://local.cocorico.cc'
        )
        self.access_token = r.json()['access_token']

        super(AddCocoricoVoteVisitor, self).__init__()

    def visit_node(self, node):
        if not self.access_token:
            return

        # if on root node
        if 'parent' not in node and 'type' not in node:
            r = requests.post(
                self.url + '/api/vote',
                headers={'Authorization': 'Bearer ' + self.access_token},
                data={
                    'title': 'test de vote',
                    'description': 'ceci est un test',
                    'url': 'https://legilibre.fr/?test=49'
                },
                verify=self.url != 'https://local.cocorico.cc'
            )
            node['cocoricoVote'] = r.json()['vote']['id']
