## Dataverse API Client

This is a library for writing Python applications that make use of Dataverse
Sword APIs.  The code started as a "proof of concept" in the
[dvn/swordpoc](https://github.com/dvn/swordpoc) repo and the intent is to
publish the python client on https://pypi.python.org.

## Installation

This client requires python 2.6+.
It has not been tested in python 3.

To install dataverse as a package:

    $ pip install -e git+https://github.com/rliebz/dvn-client-python.git#egg=dataverse

## Configuration

Create a file at `settings/local.py`. The file should contain the following
information:

```python
DEFAULT_HOST = "dataverse-demo.iq.harvard.edu"
DEFAULT_TOKEN = "" # Token can be generated at {host}/account/apitoken
```

Do not commit this file.

## Testing

Not all tests are functional. 

In order to run any tests, you must first create and publish a Dataverse on the
host you wish to test. Do not run tests on the production server.
