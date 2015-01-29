DEFAULT_USERNAME = "changeme"
DEFAULT_PASSWORD = "changeme"
DEFAULT_HOST = "dataverse-demo.iq.harvard.edu"
DEFAULT_CERT = "dataverseclient/resources/dvn-4.hmdc.harvard.edu"

EXAMPLE_DICT = {
    "title": "ExampleTitle",
    "id": "ExampleID",
    "author": ["ExampleAuthor1", "ExampleAuthor2"],
    "producer": "ExampleProducer",
    "date": "1992-10-04",
    "description": "ExampleDescription",
    "abstract": "ExampleAbstract",
    "type": "ExampleType",
    "source": "ExampleSource",
    "restriction": "ExampleRestriction",
    "relation": "ExampleRelation",
    "keyword": "ExampleKeyword",
    "coverage": "ExampleCoverage",
    "publication": "ExamplePublication",
}


try:
    from local import *
except ImportError:
    pass