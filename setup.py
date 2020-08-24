#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='indigo-influx-receiver',
    author='daveb@smurfless.com',
    url='',
    versioning='dev',
    setup_requires=['setupmeta'],
    dependency_links=['https://pypi.org/project/setupmeta'],
    include_package_data=True,
    python_requires='>=3.7',
    install_requires=[
        'arrow',
        'betterproto',
        'click',
        'influxdb',
    ],
    extras_require={
        'dev': [
            'behave',
            'betterproto[compiler]',
            'flake8',
            'tox',
            'mypy',
            'pytest'
        ]
    },
    entry_points='''
        [console_scripts]
        indigo-influx-receiver=serve:main
    ''',
)
