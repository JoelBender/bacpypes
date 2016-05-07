#!/usr/bin/python

"""
Glue routines to simulate package setup and teardown.
"""

from .utilities import setup_package, teardown_package

def pytest_configure(config):
    setup_package()


def pytest_unconfigure():
    teardown_package()
