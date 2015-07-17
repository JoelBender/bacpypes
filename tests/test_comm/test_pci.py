#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BACpypes PCI Testing
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import PCI

# some debugging
_debug = 0
_log = ModuleLogger(globals())


def setUpModule():
    if _debug: setUpModule._debug("setUpModule")

bacpypes_debugging(setUpModule)


def tearDownModule():
    if _debug: tearDownModule._debug("tearDownModule")

bacpypes_debugging(tearDownModule)


class TestPCI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if _debug: TestPCI._debug("setUpClass")

    @classmethod
    def tearDownClass(cls):
        if _debug: TestPCI._debug("tearDownClass")

    def setUp(self):
        if _debug: TestPCI._debug("setUp")

    def tearDown(self):
        if _debug: TestPCI._debug("tearDown")

    def test_something(self):
        if _debug: TestPCI._debug("test_something")

    def test_something_else(self):
        if _debug: TestPCI._debug("test_something_else")

bacpypes_debugging(TestPCI)
