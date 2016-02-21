#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# different source folders
version_info = sys.version_info[:2]
source_folder = "py" + str(version_info[0]) + str(version_info[1])
if not os.path.exists(source_folder):
    raise EnvironmentError("unsupported version of Python, looking for " + repr(source_folder))

requirements = [
    # no external requirements
]

test_requirements = [
    'nose',
]

setup(
    name="bacpypes",
    version="0.13.8",
    description="Testing multiple versions of python",
    long_description="This is a long line of text",
    author="Joel Bender",
    author_email="joel@carrickbender.com",
    url="https://github.com/JoelBender/bacpypes",
    packages=[
        'bacpypes',
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
    test_suite='nose.collector',
    tests_require=test_requirements
)
