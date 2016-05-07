#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Boolean
---------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Boolean, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def boolean_tag(value):
    """Convert an integer to an boolean application tag."""
    if _debug: boolean_tag._debug("boolean_tag %r", value)

    tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, int(value), xtob(''))
    if _debug: boolean_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def boolean_encode(obj):
    """Encode an Boolean object into a tag."""
    if _debug: boolean_encode._debug("boolean_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: boolean_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def boolean_decode(tag):
    """Decode an boolean application tag into an boolean."""
    if _debug: boolean_decode._debug("boolean_decode %r", tag)

    obj = Boolean(tag)
    if _debug: boolean_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def boolean_endec(v, x):
    """Pass the value to Boolean, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: boolean_endec._debug("boolean_endec %r %r", v, x)

    tag = boolean_tag(x)
    if _debug: boolean_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Boolean(v)
    if _debug: boolean_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert boolean_encode(obj) == tag
    assert boolean_decode(tag) == obj


@bacpypes_debugging
class TestBoolean(unittest.TestCase):

    def test_boolean(self):
        if _debug: TestBoolean._debug("test_boolean")

        obj = Boolean()
        assert obj.value == False

        with self.assertRaises(TypeError):
            Boolean("some string")
        with self.assertRaises(TypeError):
            Boolean(1.0)

    def test_boolean_bool(self):
        if _debug: TestBoolean._debug("test_boolean_bool")

        obj = Boolean(False)
        assert obj.value == False
        assert str(obj) == "Boolean(False)"

        obj = Boolean(True)
        assert obj.value == True
        assert str(obj) == "Boolean(True)"

    def test_boolean_tag(self):
        if _debug: TestBoolean._debug("test_boolean_tag")

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 1, xtob('01'))
        obj = Boolean(tag)
        assert obj.value == 1

        tag = Tag(Tag.applicationTagClass, Tag.integerAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Boolean(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Boolean(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Boolean(tag)

    def test_boolean_copy(self):
        if _debug: TestBoolean._debug("test_boolean_copy")

        obj1 = Boolean(True)
        obj2 = Boolean(obj1)
        assert obj2.value == True

    def test_boolean_endec(self):
        if _debug: TestBoolean._debug("test_boolean_endec")

        boolean_endec(False, False)
        boolean_endec(True, True)