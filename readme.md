## Dataverse API Client

**PLEASE NOTE: This library is maintained by the Dataverse community, not IQSS.**

This is a library for writing Python applications that make use of Dataverse
APIs v4.0.  The intent is to publish the python client on https://pypi.python.org.

## Installation

    $ pip install -e git+https://github.com/IQSS/dataverse-client-python.git#egg=dataverse

Requires Python >= 2.6.


## Usage

To use the python client, you will need a dataverse account and an API token.
```python
from dataverse import Connection

host = 'demo.dataverse.org'                  # All clients >4.0 are supported
token = '4d0634d3-74d5-4770-8088-1971847ac75e'  # Generated at /account/apitoken

connection = Connection(host, token)
# For non-https connections (e.g. local dev environment), try:
#   connection = Connection(host, token, use_https=False)
```

Dataverse Objects can be retrieved from their respective containers
```python
dataverse = connection.get_dataverse('ALIAS')
dataset = dataverse.get_dataset_by_doi('DOI:10.5072/FK2/ABC123')
files = dataset.get_files('latest')
```

## Testing

### Configuration

Create a file at `dataverse/settings/local.py`. The file should contain the following
information:

```python
TEST_HOST = 'demo.dataverse.org'
```

Do not commit this file.

### Running Tests

To run tests:

    $ py.test

Or, to run a specific test:

    $ py.test dataverse/test/test_dataverse.py::TestClassName::test_method_name

To check for style:

    $ flake8 .
