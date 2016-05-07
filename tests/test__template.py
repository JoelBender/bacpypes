#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Module Template
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def setup_module():
    if _debug: setup_module._debug("setup_module")


@bacpypes_debugging
def teardown_module():
    if _debug: teardown_module._debug("teardown_module")


@bacpypes_debugging
def setup_function(function):
    if _debug: setup_function._debug("setup_function %r", function)


@bacpypes_debugging
def teardown_function(function):
    if _debug: teardown_function._debug("teardown_function %r", function)


@bacpypes_debugging
class TestCaseTemplate(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        if _debug: TestCaseTemplate._debug("setup_class")

    @classmethod
    def teardown_class(cls):
        if _debug: TestCaseTemplate._debug("teardown_class")

    def setup_method(self, method):
        if _debug: TestCaseTemplate._debug("setup_module %r", method)

    def teardown_method(self, method):
        if _debug: TestCaseTemplate._debug("teardown_method %r", method)

    def test_something(self):
        if _debug: TestCaseTemplate._debug("test_something")

    def test_something_else(self):
        if _debug: TestCaseTemplate._debug("test_something_else")
