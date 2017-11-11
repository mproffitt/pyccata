#!/usr/bin/env python3

from setuptools import setup
from setuptools import find_packages

setup(
    name='pycatta',
    version='0.1.5',
    description='Collation and correlation of data',
    author='Martin Proffitt',
    author_email='mproffitt@jitsc.co.uk',
    license='MIT',
    url='https://bitbucket.org/mproffitt/pyccata',
    package_dir={
        'pyccata':'src/pyccata'
    },
    packages=[
        'pyccata'
    ],
    scripts=[
        'src/bin/releasenote.py',
        'src/bin/releaseinstructions.py'
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
        'pycurl',
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'mpltools',
        'matplotlib',
        'matplotlib-venn',
        'pyupset',
        'dask',
        'psutil'
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

