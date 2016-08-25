#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Unsigned
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Unsigned, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def unsigned_tag(x):
    """Convert a hex string to an unsigned application tag."""
    if _debug: unsigned_tag._debug("unsigned_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.unsignedAppTag, len(b), b)
    if _debug: unsigned_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def unsigned_encode(obj):
    """Encode an Unsigned object into a tag."""
    if _debug: unsigned_encode._debug("unsigned_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: unsigned_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def unsigned_decode(tag):
    """Decode an unsigned application tag into an unsigned."""
    if _debug: unsigned_decode._debug("unsigned_decode %r", tag)

    obj = Unsigned(tag)
    if _debug: unsigned_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def unsigned_endec(v, x):
    """Pass the value to Unsigned, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: unsigned_endec._debug("unsigned_endec %r %r", v, x)

    tag = unsigned_tag(x)
    if _debug: unsigned_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Unsigned(v)
    if _debug: unsigned_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert unsigned_encode(obj) == tag
    assert unsigned_decode(tag) == obj


@bacpypes_debugging
class TestUnsigned(unittest.TestCase):

    def test_unsigned(self):
        if _debug: TestUnsigned._debug("test_unsigned")

        obj = Unsigned()
        assert obj.value == 0

        with self.assertRaises(TypeError):
            Unsigned("some string")
        with self.assertRaises(TypeError):
            Unsigned(1.0)

    def test_unsigned_int(self):
        if _debug: TestUnsigned._debug("test_unsigned_int")

        obj = Unsigned(1)
        assert obj.value == 1
        assert str(obj) == "Unsigned(1)"

        with self.assertRaises(ValueError):
            Unsigned(-1)

    def test_unsigned_tag(self):
        if _debug: TestUnsigned._debug("test_unsigned_tag")

        tag = Tag(Tag.applicationTagClass, Tag.unsignedAppTag, 1, xtob('01'))
        obj = Unsigned(tag)
        assert obj.value == 1

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Unsigned(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Unsigned(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Unsigned(tag)

    def test_unsigned_copy(self):
        if _debug: TestUnsigned._debug("test_unsigned_copy")

        obj1 = Unsigned(12)
        obj2 = Unsigned(obj1)
        assert obj2.value == 12

    def test_unsigned_endec(self):
        if _debug: TestUnsigned._debug("test_unsigned_endec")

        with self.assertRaises(InvalidTag):
            obj = Unsigned(unsigned_tag(''))

        unsigned_endec(0, '00')
        unsigned_endec(1, '01')
        unsigned_endec(127, '7f')
        unsigned_endec(128, '80')
        unsigned_endec(255, 'ff')

        unsigned_endec(32767, '7fff')
        unsigned_endec(32768, '8000')

        unsigned_endec(8388607, '7fffff')
        unsigned_endec(8388608, '800000')

        unsigned_endec(2147483647, '7fffffff')
        unsigned_endec(2147483648, '80000000')