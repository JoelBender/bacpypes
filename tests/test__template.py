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
    """This function is called once at the beginning of all of the tests
    in this module."""
    if _debug: setup_module._debug("setup_module")


@bacpypes_debugging
def teardown_module():
    """This function is called once at the end of the tests in this module."""
    if _debug: teardown_module._debug("teardown_module")


@bacpypes_debugging
def setup_function(function):
    """This function is called before each module level test function."""
    if _debug: setup_function._debug("setup_function %r", function)


@bacpypes_debugging
def teardown_function(function):
    """This function is called after each module level test function."""
    if _debug: teardown_function._debug("teardown_function %r", function)


@bacpypes_debugging
def test_some_function(*args, **kwargs):
    """This is a module level test function."""
    if _debug: setup_function._debug("test_some_function %r %r", args, kwargs)


@bacpypes_debugging
class TestCaseTemplate(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """This function is called once before the test case is instantiated
        for each of the tests."""
        if _debug: TestCaseTemplate._debug("setup_class")

    @classmethod
    def teardown_class(cls):
        """This function is called once at the end after the last instance
        of the test case has been abandon."""
        if _debug: TestCaseTemplate._debug("teardown_class")

    def setup_method(self, method):
        """This function is called before each test method is called as is
        given a reference to the test method."""
        if _debug: TestCaseTemplate._debug("setup_method %r", method)

    def teardown_method(self, method):
        """This function is called after each test method has been called and
        is given a reference to the test method."""
        if _debug: TestCaseTemplate._debug("teardown_method %r", method)

    def test_something(self):
        """This is a method level test function."""
        if _debug: TestCaseTemplate._debug("test_something")

    def test_something_else(self):
        """This is another method level test function."""
        if _debug: TestCaseTemplate._debug("test_something_else")

