#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='scotch',
    version='0.3',
    description='Simplifies WSGI application deployment.',
    long_description=read('README.rst'),
    author='Marc Brinkmann',
    author_email='git@marcbrinkmann.de',
    url='http://github.com/mbr/scotch',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=['logbook', 'blinker', 'shortuuid', 'virtualenv',
                      'jinja2', 'configparser', 'pathlib'],
    entry_points={
        'console_scripts': [
            'scotch = scotch.cmd:main_scotch_deploy',
        ],
    }
)
