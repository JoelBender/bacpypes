#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Time
---------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Time, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def time_tag(x):
    """Convert a hex string to an time application tag."""
    if _debug: time_tag._debug("time_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.timeAppTag, len(b), b)
    if _debug: time_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def time_encode(obj):
    """Encode an Time object into a tag."""
    if _debug: time_encode._debug("time_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: time_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def time_decode(tag):
    """Decode an time application tag into an time."""
    if _debug: time_decode._debug("time_decode %r", tag)

    obj = Time(tag)
    if _debug: time_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def time_endec(v, x):
    """Pass the value to Time, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: time_endec._debug("time_endec %r %r", v, x)

    tag = time_tag(x)
    if _debug: time_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Time(v)
    if _debug: time_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert time_encode(obj) == tag
    assert time_decode(tag) == obj


@bacpypes_debugging
class TestTime(unittest.TestCase):

    def test_time(self):
        if _debug: TestTime._debug("test_time")

        # default values is all dont care
        obj = Time()
        assert obj.value == (255, 255, 255, 255)

        with self.assertRaises(ValueError):
            Time("some string")
        with self.assertRaises(TypeError):
            Time(1.0)

    def test_time_tuple(self):
        if _debug: TestTime._debug("test_time_tuple")

        obj = Time((1,2,3,4))
        assert obj.value == (1, 2, 3, 4)
        assert str(obj) == "Time(01:02:03.04)"

        assert Time("1:2").value == (1, 2, 0, 0)
        assert Time("1:2:3").value == (1, 2, 3, 0)
        assert Time("1:2:3.4").value == (1, 2, 3, 40)
        assert Time("1:*").value == (1, 255, 255, 255)
        assert Time("1:2:*").value == (1, 2, 255, 255)
        assert Time("1:2:3.*").value == (1, 2, 3, 255)

    def test_time_tag(self):
        if _debug: TestTime._debug("test_time_tag")

        tag = Tag(Tag.applicationTagClass, Tag.timeAppTag, 1, xtob('01020304'))
        obj = Time(tag)
        assert obj.value == (1, 2, 3, 4)

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Time(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Time(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Time(tag)

    def test_time_copy(self):
        if _debug: TestTime._debug("test_time_copy")

        time_value = (2, 3, 4, 5)
        obj1 = Time(time_value)
        obj2 = Time(obj1)
        assert obj2.value == time_value

    def test_time_now(self):
        if _debug: TestTime._debug("test_time_now")

        # obj = Time().now()
        ### how to test?

    def test_time_endec(self):
        if _debug: TestTime._debug("test_time_endec")

        with self.assertRaises(InvalidTag):
            obj = Time(time_tag(''))

        time_endec((0, 0, 0, 0), '00000000')
        time_endec((1, 0, 0, 0), '01000000')
        time_endec((0, 2, 0, 0), '00020000')
        time_endec((0, 0, 3, 0), '00000300')
        time_endec((0, 0, 0, 4), '00000004')