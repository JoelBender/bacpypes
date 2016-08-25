#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Integer
---------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Integer, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def integer_tag(x):
    """Convert a hex string to an integer application tag."""
    if _debug: integer_tag._debug("integer_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.integerAppTag, len(b), b)
    if _debug: integer_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def integer_encode(obj):
    """Encode an Integer object into a tag."""
    if _debug: integer_encode._debug("integer_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: integer_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def integer_decode(tag):
    """Decode an integer application tag into an integer."""
    if _debug: integer_decode._debug("integer_decode %r", tag)

    obj = Integer(tag)
    if _debug: integer_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def integer_endec(v, x):
    """Pass the value to Integer, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: integer_endec._debug("integer_endec %r %r", v, x)

    tag = integer_tag(x)
    if _debug: integer_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Integer(v)
    if _debug: integer_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert integer_encode(obj) == tag
    assert integer_decode(tag) == obj


@bacpypes_debugging
class TestInteger(unittest.TestCase):

    def test_integer(self):
        if _debug: TestInteger._debug("test_integer")

        obj = Integer()
        assert obj.value == 0

        with self.assertRaises(TypeError):
            Integer("some string")
        with self.assertRaises(TypeError):
            Integer(1.0)

    def test_integer_int(self):
        if _debug: TestInteger._debug("test_integer_int")

        obj = Integer(1)
        assert obj.value == 1
        assert str(obj) == "Integer(1)"

        obj = Integer(-1)
        assert obj.value == -1
        assert str(obj) == "Integer(-1)"

    def test_integer_tag(self):
        if _debug: TestInteger._debug("test_integer_tag")

        tag = Tag(Tag.applicationTagClass, Tag.integerAppTag, 1, xtob('01'))
        obj = Integer(tag)
        assert obj.value == 1

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Integer(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Integer(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Integer(tag)

    def test_integer_copy(self):
        if _debug: TestInteger._debug("test_integer_copy")

        obj1 = Integer(12)
        obj2 = Integer(obj1)
        assert obj2.value == 12

    def test_integer_endec(self):
        if _debug: TestInteger._debug("test_integer_endec")

        with self.assertRaises(InvalidTag):
            obj = Integer(integer_tag(''))

        integer_endec(0, '00')
        integer_endec(1, '01')
        integer_endec(127, '7f')
        integer_endec(-128, '80')
        integer_endec(-1, 'ff')

        integer_endec(32767, '7fff')
        integer_endec(-32768, '8000')

        integer_endec(8388607, '7fffff')
        integer_endec(-8388608, '800000')

        integer_endec(2147483647, '7fffffff')
        integer_endec(-2147483648, '80000000')