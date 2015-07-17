#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
test_something
--------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0
_log = ModuleLogger(globals())


class TestSomething(unittest.TestCase):

    def setUp(self):
        if _debug: TestSomething._debug("setUp")

    def test_something(self):
        if _debug: TestSomething._debug("test_something")

    def tearDown(self):
        if _debug: TestSomething._debug("tearDown")

bacpypes_debugging(TestSomething)
