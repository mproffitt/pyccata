#!/usr/bin/env python

from setuptools import setup

setup(
    name='JiraWeeklyReport',
    version='0.1',
    description='Application for generating a weekly report from Jira',
    author='Martin Proffitt',
    author_email='mproffitt@jitsc.co.uk',
    url='http://www.jitsc.co.uk/weekly-report',

    packages=[
        'releaseessentials'
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
        'pyquery'
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

