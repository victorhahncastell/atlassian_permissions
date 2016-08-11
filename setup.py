#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Atlassian Permissions',
    version='1.2',
    description='Extract Atlassian permissions',
    author='Sýlvan Heuser, Victor Hahn Castell',
    author_email='victor.hahn@flexoptix.net',
    packages=find_packages(),
    scripts=['run.py'],
    install_requires=[
        'requests>=2.5.1',
        'deepdiff>=2.1.2',
        'dill',
        'Jinja2'
    ]
)
