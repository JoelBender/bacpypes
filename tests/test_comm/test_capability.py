#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Capability Module
----------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.capability import Capability, Collector

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class BaseCollector(Collector):

    def __init__(self):
        if _debug: BaseCollector._debug("__init__")
        Collector.__init__(self)

    def transform(self, value):
        if _debug: BaseCollector._debug("transform %r", value)

        for fn in self.capability_functions('transform'):
            print("    - fn: {}".format(fn))
            value = fn(self, value)

        return value

@bacpypes_debugging
class PlusOne(Capability):

    def __init__(self):
        if _debug: PlusOne._debug("__init__")

    def transform(self, value):
        if _debug: PlusOne._debug("transform %r", value)
        return value + 1


@bacpypes_debugging
class TimesTen(Capability):

    def __init__(self):
        if _debug: TimesTen._debug("__init__")

    def transform(self, value):
        if _debug: TimesTen._debug("transform %r", value)
        return value * 10


@bacpypes_debugging
class MakeList(Capability):

    def __init__(self):
        if _debug: MakeList._debug("__init__")

    def transform(self, value):
        if _debug: MakeList._debug("transform %r", value)
        return [value]


#
#   Example classes
#

class Example1(BaseCollector):
    pass

class Example2(BaseCollector, PlusOne):
    pass

class Example3(BaseCollector, TimesTen, PlusOne):
    pass

class Example4(BaseCollector, MakeList, TimesTen):
    pass


@bacpypes_debugging
class TestExamples(unittest.TestCase):

    def test_example_1(self):
        if _debug: TestExamples._debug("test_example_1")

        assert Example1().transform(1) == 1

    def test_example_2(self):
        if _debug: TestExamples._debug("test_example_2")

        assert Example2().transform(2) == 3

    def test_example_3(self):
        if _debug: TestExamples._debug("test_example_3")

        assert Example3().transform(3) == 31

    def test_example_4(self):
        if _debug: TestExamples._debug("test_example_4")

        assert Example4().transform(4) == [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]

    def test_example_5(self):
        if _debug: TestExamples._debug("test_example_5")

        obj = Example2()
        obj.add_capability(MakeList)

        assert obj.transform(5) == [6]
