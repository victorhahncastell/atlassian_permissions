#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Atlassian Permissions',
    version='1.0',
    description='Extract Atlassian permissions',
    author='Sýlvan Heuser',
    author_email='sylvan.heuser@flexoptix.net',
    packages=find_packages(),
    scripts=['run.py'],
    install_requires=[
        'selenium>=2.44.0',
        'requests>=2.5.1'
    ]
)