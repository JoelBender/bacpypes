#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BACpypes PDU Testing
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import PDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())


def setUpModule():
    if _debug: setUpModule._debug("setUpModule")

bacpypes_debugging(setUpModule)


def tearDownModule():
    if _debug: tearDownModule._debug("tearDownModule")

bacpypes_debugging(tearDownModule)


class TestPDU(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if _debug: TestPDU._debug("setUpClass")

    @classmethod
    def tearDownClass(cls):
        if _debug: TestPDU._debug("tearDownClass")

    def setUp(self):
        if _debug: TestPDU._debug("setUp")

    def tearDown(self):
        if _debug: TestPDU._debug("tearDown")

    def test_something(self):
        if _debug: TestPDU._debug("test_something")

    def test_something_else(self):
        if _debug: TestPDU._debug("test_something_else")

bacpypes_debugging(TestPDU)
