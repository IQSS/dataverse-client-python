This is a library for writing Python applications that make use of Dataverse Network (DVN) APIs.

The code was originally written as a "proof of concept" at https://github.com/dvn/swordpoc/tree/master/dvn_client but the intention is to eventually publish the code on https://pypi.python.org so users can run `pip install dvn-client` to use the Python library.

For now https://github.com/dvn/swordpoc/blob/master/dvn_client/README.md has some tips but they should be incorporated into this repo.

We have been trying to target Python 2.6 because that's the version that ships with the latest version (6) of Red Hat Enterprise Linux (RHEL) and CentOS. For testing backward compatibility with Python 2.6, this repo includes a Vagrant environment. Please note that before you run `vagrant up` you'll need to run `git submodule init` and `git submodule update` once after cloning this repo.
