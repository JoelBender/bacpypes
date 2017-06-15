#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Null
------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.primitivedata import Null, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def null_tag(x):
    """Convert a hex string to an integer application tag."""
    if _debug: null_tag._debug("null_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.nullAppTag, len(b), b)
    if _debug: integer_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def null_encode(obj):
    """Encode an Integer object into a tag."""
    if _debug: null_encode._debug("null_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: null_encode._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def null_decode(tag):
    """Decode an integer application tag into an integer."""
    if _debug: null_decode._debug("null_decode %r", tag)

    obj = Null(tag)
    if _debug: null_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def null_endec(v, x):
    """Pass the value to Integer, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: null_endec._debug("null_endec %r %r", v, x)

    tag = null_tag(x)
    if _debug: null_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Null(v)
    if _debug: null_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert null_encode(obj) == tag
    assert null_decode(tag) == obj


@bacpypes_debugging
class TestNull(unittest.TestCase):

    def test_null(self):
        if _debug: TestInteger._debug("test_null")

        obj = Null()
        assert obj.value == ()

        with self.assertRaises(TypeError):
            Null("some string")
        with self.assertRaises(TypeError):
            Null(1.0)

    def test_null_null(self):
        if _debug: TestInteger._debug("test_null_null")

        obj = Null(())
        assert obj.value == ()

    def test_null_tag(self):
        if _debug: TestInteger._debug("test_null_tag")

        tag = Tag(Tag.applicationTagClass, Tag.nullAppTag, 0, xtob(''))
        obj = Null(tag)
        assert obj.value == ()

    def test_null_copy(self):
        if _debug: TestInteger._debug("test_null_copy")

        obj1 = Null()
        obj2 = Null(obj1)
        assert obj2.value == ()

    def test_null_endec(self):
        if _debug: TestInteger._debug("test_null_endec")

        null_endec((), '')