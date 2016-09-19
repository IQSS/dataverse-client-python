from __future__ import absolute_import

import os

TEST_HOST = 'demo.dataverse.org'

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.abspath(os.path.join(HERE, os.pardir))

EXAMPLE_DICT = {
    'title': 'ExampleTitle',
    'id': 'ExampleID',
    'author': ['ExampleAuthor1', 'ExampleAuthor2'],
    'producer': 'ExampleProducer',
    'date': '1992-10-04',
    'description': 'ExampleDescription',
    'abstract': 'ExampleAbstract',
    'type': 'ExampleType',
    'source': 'ExampleSource',
    'restriction': 'ExampleRestriction',
    'relation': 'ExampleRelation',
    'keyword': 'ExampleKeyword',
    'coverage': 'ExampleCoverage',
    'publication': 'ExamplePublication',
}

SWORD_BOOTSTRAP = '''<?xml version='1.0'?>
<entry xmlns='http://www.w3.org/2005/Atom'
        xmlns:dcterms='http://purl.org/dc/terms/'>
</entry>'''

SWORD_NAMESPACE = {
    'dcterms': 'http://purl.org/dc/terms/',
    'atom': 'http://www.w3.org/2005/Atom',
}

UNIQUE_FIELDS = ['title', 'id', 'updated', 'summary']

REPLACEMENT_DICT = {
    'id': 'identifier',
    'author': 'creator',
    'producer': 'publisher',
    'restriction': 'rights',
    'keyword': 'subject',
    'publication': 'isReferencedBy'
}
