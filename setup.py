#!/usr/bin/env python

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='Atlassian Permissions',
    version='1.2',
    description='Extract Atlassian permissions',
    author='Sýlvan Heuser, Victor Hahn Castell',
    author_email='victor.hahn@flexoptix.net',
    packages=find_packages(),
    scripts=['run.py'],
    install_requires=required
)
