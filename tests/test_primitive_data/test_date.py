#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Date
---------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.primitivedata import Date, Tag, DecodingError

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def date_tag(x):
    """Convert a hex string to an date application tag."""
    if _debug: date_tag._debug("date_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.dateAppTag, len(b), b)
    if _debug: date_endec._debug("    - tag: %r", tag)

    return tag

@bacpypes_debugging
def date_encode(obj):
    """Encode an Date object into a tag."""
    if _debug: date_encode._debug("date_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: date_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def date_decode(tag):
    """Decode an date application tag into an date."""
    if _debug: date_decode._debug("date_decode %r", tag)

    obj = Date(tag)
    if _debug: date_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def date_endec(v, x):
    """Pass the value to Date, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: date_endec._debug("date_endec %r %r", v, x)

    tag = date_tag(x)
    if _debug: date_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Date(v)
    if _debug: date_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert date_encode(obj) == tag
    assert date_decode(tag) == obj


@bacpypes_debugging
class TestDate(unittest.TestCase):

    def test_date(self):
        if _debug: TestDate._debug("test_date")

        # default values is all dont care
        obj = Date()
        assert obj.value == (255, 255, 255, 255)

        with self.assertRaises(ValueError):
            Date("some string")
        with self.assertRaises(TypeError):
            Date(1.0)

    def test_date_tuple(self):
        if _debug: TestDate._debug("test_date_tuple")

        obj = Date((1,2,3,4))
        assert obj.value == (1, 2, 3, 4)
        assert str(obj) == "Date(2/3/1901 Thu)"

        ### issue-48
        # obj = Date("1/2/3")
        # assert obj.value == (1, 2, x, y)

        # obj = Date("*/2/3")
        # assert obj.value == (255, 2, x, 255)

        # obj = Date("1/*/3")
        # assert obj.value == (1, 255, x, 255)

        # obj = Date("1/2/*")
        # assert obj.value == (1, 2, 255, 255)

        # obj = Date("1/2/3 *")
        # assert obj.value == (1, 2, 3, 255)

    def test_date_tag(self):
        if _debug: TestDate._debug("test_date_tag")

        tag = Tag(Tag.applicationTagClass, Tag.dateAppTag, 1, xtob('01020304'))
        obj = Date(tag)
        assert obj.value == (1, 2, 3, 4)

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(ValueError):
            Date(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(ValueError):
            Date(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(ValueError):
            Date(tag)

    def test_date_copy(self):
        if _debug: TestDate._debug("test_date_copy")

        date_value = (2, 3, 4, 5)
        obj1 = Date(date_value)
        obj2 = Date(obj1)
        assert obj2.value == date_value

    def test_date_now(self):
        if _debug: TestDate._debug("test_date_now")

        # obj = Date().now()
        ### how to test?

    def test_date_endec(self):
        if _debug: TestDate._debug("test_date_endec")

#       with self.assertRaises(DecodingError):
#           obj = Date(date_tag(''))

        date_endec((0, 0, 0, 0), '00000000')
        date_endec((1, 0, 0, 0), '01000000')
        date_endec((0, 2, 0, 0), '00020000')
        date_endec((0, 0, 3, 0), '00000300')
        date_endec((0, 0, 0, 4), '00000004')
