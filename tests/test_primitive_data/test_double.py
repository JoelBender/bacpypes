#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Double
--------------------------
"""

import unittest
import struct
import math

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Double, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def double_tag(x):
    """Convert a hex string to an double application tag."""
    if _debug: double_tag._debug("double_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.doubleAppTag, len(b), b)
    if _debug: double_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def double_encode(obj):
    """Encode an Double object into a tag."""
    if _debug: double_encode._debug("double_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: double_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def double_decode(tag):
    """Decode an double application tag into a double."""
    if _debug: double_decode._debug("double_decode %r", tag)

    obj = Double(tag)
    if _debug: double_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def double_endec(v, x):
    """Pass the value to Double, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: double_endec._debug("double_endec %r %r", v, x)

    tag = double_tag(x)
    if _debug: double_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Double(v)
    if _debug: double_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert double_encode(obj) == tag
    if _debug: real_endec._debug("    - tags match")

    if math.isnan(v):
        assert math.isnan(double_decode(tag).value)
        if _debug: double_endec._debug("    - both NaN")
    else:
        assert double_decode(tag) == obj
        if _debug: double_endec._debug("    - objects match")

@bacpypes_debugging
class TestDouble(unittest.TestCase):

    def test_double(self):
        if _debug: TestDouble._debug("test_double")

        obj = Double()
        assert obj.value == 0.0

        with self.assertRaises(TypeError):
            Double("some string")

    def test_double_double(self):
        if _debug: TestDouble._debug("test_double_double")

        obj = Double(1.0)
        assert obj.value == 1.0
        assert str(obj) == "Double(1)"

        obj = Double(73.5)
        assert obj.value == 73.5
        assert str(obj) == "Double(73.5)"

    def test_double_tag(self):
        if _debug: TestDouble._debug("test_double_tag")

        tag = Tag(Tag.applicationTagClass, Tag.doubleAppTag, 8, xtob('3ff0000000000000'))
        obj = Double(tag)
        assert obj.value == 1.0

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Double(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Double(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Double(tag)

    def test_double_copy(self):
        if _debug: TestDouble._debug("test_double_copy")

        obj1 = Double(12)
        obj2 = Double(obj1)
        assert obj2.value == 12

    def test_double_endec(self):
        if _debug: TestDouble._debug("test_double_endec")

        with self.assertRaises(InvalidTag):
            obj = Double(double_tag(''))

        double_endec(0, '0000000000000000')
        double_endec(1, '3ff0000000000000')
        double_endec(-1, 'bff0000000000000')

        double_endec(73.5, '4052600000000000')

        inf = float('inf')
        double_endec(inf, '7ff0000000000000')
        double_endec(-inf, 'fff0000000000000')

        nan = float('nan')
        double_endec(nan, '7ff8000000000000')