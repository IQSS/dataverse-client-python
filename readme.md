## Dataverse Network (DVN) API Client

This is a library for writing Python applications that make use of Dataverse
Network (DVN) APIs.  The code started as a "proof of concept" in the
[dvn/swordpoc](https://github.com/dvn/swordpoc) repo and the intent is to
publish the python client on https://pypi.python.org.

The proof of concept
[README.md](https://github.com/dvn/swordpoc/blob/master/dvn_client/README.md)
has some tips that have not been incorporated in to this readme yet.

We have been trying to target Python 2.6 because that's the version that ships
with the latest version (6) of Red Hat Enterprise Linux (RHEL) and CentOS. For
testing backward compatibility with Python 2.6, this repo includes a Vagrant
environment. Please note that before you run `vagrant up` you'll need to run
`git submodule init` and `git submodule update` once after cloning this repo.

## Installation

For development, you will need:

* Python 2.6+
* [pip](http://www.pip-installer.org/en/latest/)
* gcc compiler (For OSX you will need xcode + command line tools, or [standalone install](https://github.com/kennethreitz/osx-gcc-installer#readme))
* Dataverse account

To install dataverse as a package:

    $ pip install -e git+https://github.com/rliebz/python-client-sword2.git#egg=sword2
    $ pip install -e git+https://github.com/rliebz/dvn-client-python.git#egg=dataverse

Once you have satisfied the above requirements, try the following commands.

    $ git clone https://github.com/IQSS/dvn-client-python.git
    $ cd dvn-client-python
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r dvn_client/src/requirements.txt

You may wish to manage virtualenvs using [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) instead.

## Configuration

Copy `config.py` to `local.py` and fill out the config elements as appropriate. Do not commit this file.

```python
DEFAULT_USERNAME = ""
DEFAULT_PASSWORD = ""
DEFAULT_HOST = "dvn-demo.iq.harvard.edu"
DEFAULT_CERT = "dvn_client/resources/dvn-4.hmdc.harvard.edu" #see below for info on the cert
```

## Installation Test

* Navigate to `dvn-client-python/dvn-client/src/test/`
* Edit test data in `tests.py` as appropriate
* Run the client `python dvn_client.py`
* To run all of the tests, run `python test_dvn.py` (for more options see [unittest](http://docs.python.org/2/library/unittest.html#assert-methods))

## PEM Certificate (optional)

If you are using a self-signed certificate, you may see an SSL error when you
try to hit the server. In that case, follow these instructions.

1. Open private/incognito window (in case you have already added a security exception) in FireFox (instructions will be slightly different for other browsers)
2. Go to: https://{SERVER}/dvn/api/data-deposit/swordv2/service-document
3. Add Exception > View > Details > Export
4. Save the PEM to the “resources” folder of the dvn\_client project
5. When calling `Dataverse.connect()` or `Dataverse()` constructor, pass a path to this file as `cert=[PATH_TO_CERTIFICATE]`
