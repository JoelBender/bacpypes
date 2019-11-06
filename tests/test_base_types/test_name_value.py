#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Name Value Sequence
------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import MissingRequiredParameter
from bacpypes.primitivedata import Tag, TagList, Boolean, Integer, Real, Date, Time
from bacpypes.basetypes import DateTime, NameValue

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def name_value_encode(obj):
    """Encode a NameValue object into a tag list."""
    if _debug: name_value_encode._debug("name_value_encode %r", obj)

    tag_list = TagList()
    obj.encode(tag_list)
    if _debug: name_value_encode._debug("    - tag_list: %r", tag_list)

    return tag_list


@bacpypes_debugging
def name_value_decode(tag_list):
    """Decode a tag list into a NameValue."""
    if _debug: name_value_decode._debug("name_value_decode %r", tag_list)

    obj = NameValue()
    obj.decode(tag_list)
    if _debug: name_value_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def name_value_endec(name, value=None):
    """Pass the name and value to NameValue and compare the results of encoding
    and decoding."""
    if _debug: name_value_endec._debug("name_value_endec %r %r", name, value)

    obj1 = NameValue(name, value)
    if _debug: name_value_endec._debug("    - obj1: %r", obj1)

    tag_list = name_value_encode(obj1)
    if _debug: name_value_endec._debug("    - tag_list: %r", tag_list)

    obj2 = name_value_decode(tag_list)
    if _debug: name_value_endec._debug("    - obj2: %r", obj2)

    assert obj1.name == obj2.name
    if obj1.value is None:
        assert obj2.value is None
    elif isinstance(obj1.value, DateTime):
        assert obj1.value.date == obj2.value.date
        assert obj1.value.time == obj2.value.time
    else:
        assert obj1.value.value == obj2.value.value


@bacpypes_debugging
class TestNameValue(unittest.TestCase):

    def test_simple_tag(self):
        if _debug: TestNameValue._debug("test_simple_tag")

        # just the name
        name_value_endec("temp")

    def test_primitive_tag(self):
        if _debug: TestNameValue._debug("test_primitive_tag")

        # try the primitive types
        name_value_endec("status", Boolean(False))
        name_value_endec("age", Integer(3))
        name_value_endec("experience", Real(73.5))

    def test_date_time_tag(self):
        if _debug: TestNameValue._debug("test_date_time_tag")

        # BACnet Birthday (close)
        date_time = DateTime(date=(95, 1, 25, 3), time=(9, 0, 0, 0))
        if _debug: TestNameValue._debug("    - date_time: %r", date_time)

        # try the primitive types
        name_value_endec("start", date_time)

