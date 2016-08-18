#!/usr/bin/env python3

from setuptools import setup

setup(
    name='ReleaseEssentials',
    version='1.2',
    description='Application helper suite for software releases',
    author='Martin Proffitt',
    author_email='mproffitt@jitsc.co.uk',
    url='https://bitbucket.org/mproffitt/releaseessentials',

    packages=[
        'releaseessentials',
        'releaseessentials.managers',
        'releaseessentials.managers.subjects',
        'releaseessentials.parts'
    ],
    scripts=[
        'bin/releasenote.py',
        'bin/releaseinstructions.py'
    ],
    install_requires=[
        'jira',
        'lxml',
        'cffi',
        'cairosvg',
        'tinycss',
        'cssselect',
        'pygal',
        'numpy',
        'Pillow',
        'python-docx',
        'pyquery',
        'pycurl'
    ],

    test_suite='nose.collector',
    tests_require=[
        'nose',
        'coverage',
        'pbr',
        'mock',
        'ddt'
    ]
)

