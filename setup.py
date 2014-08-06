# -*- coding: utf-8 -*-
import re
import sys
from setuptools import setup, find_packages
import unittest
from setuptools.command.test import test as TestCommand


REQUIRES = [
    'bleach>=1.2.2',
    'requests>=2.2.1',
    'lxml>=3.2.5'
]

TEST_REQUIRES = [

]


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content

setup(
    name='dataverse',
    version='0.1',
    description='Python client for Dataverse version 3.X',
    long_description=read("readme.md"),
    author='Dataverse',
    author_email='rliebz@gmail.com',
    url='https://github.com/rliebz/dvn-client-python',
    packages=find_packages(),
    package_dir={'dvn-client-python': 'dataverse'},
    include_package_data=True,
    install_requires=REQUIRES,
    license=read("LICENSE"),
    zip_safe=False,
    keywords='dataverse',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
    ],
    test_suite='dataverse/test',
    tests_require=TEST_REQUIRES,
    cmdclass={'test': unittest}
)
