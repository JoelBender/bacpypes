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


@bacpypes_debugging
class TestPCI(unittest.TestCase):

    def test_something(self):
        if _debug: TestPCI._debug("test_something")

    def test_something_else(self):
        if _debug: TestPCI._debug("test_something_else")