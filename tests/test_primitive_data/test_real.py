#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Real
------------------------
"""

import unittest
import struct
import math

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Real, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def real_tag(x):
    """Convert a hex string to an real application tag."""
    if _debug: real_tag._debug("real_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.realAppTag, len(b), b)
    if _debug: real_tag._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def real_encode(obj):
    """Encode an Real object into a tag."""
    if _debug: real_encode._debug("real_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: real_encode._debug("    - tag: %r, %r", tag, tag.tagData)

    return tag


@bacpypes_debugging
def real_decode(tag):
    """Decode an real application tag into an real."""
    if _debug: real_decode._debug("real_decode %r", tag)

    obj = Real(tag)
    if _debug: real_decode._debug("    - obj: %r, %r", obj, obj.value)

    return obj


@bacpypes_debugging
def real_endec(v, x):
    """Pass the value to Real, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: real_endec._debug("real_endec %r %r", v, x)

    tag = real_tag(x)
    if _debug: real_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Real(v)
    if _debug: real_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert real_encode(obj) == tag
    if _debug: real_endec._debug("    - tags match")

    if math.isnan(v):
        assert math.isnan(real_decode(tag).value)
        if _debug: real_endec._debug("    - both NaN")
    else:
        assert real_decode(tag) == obj
        if _debug: real_endec._debug("    - objects match")


@bacpypes_debugging
class TestReal(unittest.TestCase):

    def test_real(self):
        if _debug: TestReal._debug("test_real")

        obj = Real()
        assert obj.value == 0.0

        with self.assertRaises(TypeError):
            Real("some string")

    def test_real_real(self):
        if _debug: TestReal._debug("test_real_real")

        obj = Real(1.0)
        assert obj.value == 1.0
        assert str(obj) == "Real(1)"

        obj = Real(73.5)
        assert obj.value == 73.5
        assert str(obj) == "Real(73.5)"

    def test_real_tag(self):
        if _debug: TestReal._debug("test_real_tag")

        tag = Tag(Tag.applicationTagClass, Tag.realAppTag, 1, xtob('3f800000'))
        obj = Real(tag)
        assert obj.value == 1.0

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Real(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Real(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Real(tag)

    def test_real_copy(self):
        if _debug: TestReal._debug("test_real_copy")

        obj1 = Real(12)
        obj2 = Real(obj1)
        assert obj2.value == 12

    def test_real_endec(self):
        if _debug: TestReal._debug("test_real_endec")

        with self.assertRaises(InvalidTag):
            obj = Real(real_tag(''))

        real_endec(0, '00000000')
        real_endec(1, '3f800000')
        real_endec(-1, 'bf800000')

        real_endec(73.5, '42930000')

        inf = float('inf')
        real_endec(inf, '7f800000')
        real_endec(-inf, 'ff800000')

        nan = float('nan')
        real_endec(nan, '7fc00000')