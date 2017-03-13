#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# different source folders
version_info = sys.version_info[:2]
source_folder = "py" + str(version_info[0]) + str(version_info[1])
if not os.path.exists(source_folder):
    raise EnvironmentError(
        "unsupported version of Python, looking for " +
        repr(source_folder) + " in " +
        os.getcwd()
        )

# load in the project metadata
init_py = open(os.path.join(source_folder, 'bacpypes', '__init__.py')).read()
metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))

requirements = [
    # no external requirements
]

setup_requirements = [
    'pytest-runner',
    ]

test_requirements = [
    'pytest',
    'bacpypes',
]

setup(
    name="bacpypes",
    version=metadata['version'],
    description="BACnet Communications Library",
    long_description="BACpypes provides a BACnet application layer and network layer written in Python for daemons, scripting, and graphical interfaces.",
    author=metadata['author'],
    author_email=metadata['email'],
    url="https://github.com/JoelBender/bacpypes",
    packages=[
        'bacpypes',
        'bacpypes.service',
    ],
    package_dir={
        'bacpypes': os.path.join(source_folder, 'bacpypes'),
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],

    setup_requires=setup_requirements,

    test_suite='tests',
    tests_require=test_requirements,
)
