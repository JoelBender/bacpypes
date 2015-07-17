#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Module Template
-------------------------

This module is a template for creating MongoTree test cases.  To create a
module of new tests, make a copy of this template and rename the
TestCaseTemplate and associated test_something functions.

In following with the nose testing methodology, setUpModule() will be called
before all of the tests in this module, setUpClass() will be called before
all of the tests in the class, and setUp() will be called before each test.
Similarly, tearDown() will be called after each test, tearDownClass() will be
called after all of the tests in the class, and tearDownModule() will be
called after all of the classes in the module.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from . import utilities

# some debugging
_debug = 0
_log = ModuleLogger(globals())


def setUpModule():
    if _debug: setUpModule._debug("setUpModule")

bacpypes_debugging(setUpModule)


def tearDownModule():
    if _debug: tearDownModule._debug("tearDownModule")

bacpypes_debugging(tearDownModule)


class TestCaseTemplate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if _debug: TestCaseTemplate._debug("setUpClass")

    @classmethod
    def tearDownClass(cls):
        if _debug: TestCaseTemplate._debug("tearDownClass")

    def setUp(self):
        if _debug: TestCaseTemplate._debug("setUp")

    def test_something(self):
        if _debug: TestCaseTemplate._debug("test_something")

    def test_something_else(self):
        if _debug: TestCaseTemplate._debug("test_something_else")

    def tearDown(self):
        if _debug: TestCaseTemplate._debug("tearDown")

bacpypes_debugging(TestCaseTemplate)
