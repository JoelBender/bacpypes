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


@bacpypes_debugging
class TestPDU(unittest.TestCase):

    def test_something(self):
        if _debug: TestPDU._debug("test_something")

    def test_something_else(self):
        if _debug: TestPDU._debug("test_something_else")
