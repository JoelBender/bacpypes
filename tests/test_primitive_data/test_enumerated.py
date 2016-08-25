#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Enumerated
------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Enumerated, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def enumerated_tag(x):
    """Convert a hex string to an enumerated application tag."""
    if _debug: enumerated_tag._debug("enumerated_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.enumeratedAppTag, len(b), b)
    if _debug: enumerated_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def enumerated_encode(obj):
    """Encode an Enumerated object into a tag."""
    if _debug: enumerated_encode._debug("enumerated_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: enumerated_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def enumerated_decode(tag):
    """Decode an enumerated application tag into an enumerated."""
    if _debug: enumerated_decode._debug("enumerated_decode %r", tag)

    obj = Enumerated(tag)
    if _debug: enumerated_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def enumerated_endec(v, x):
    """Pass the value to Enumerated, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: enumerated_endec._debug("enumerated_endec %r %r", v, x)

    tag = enumerated_tag(x)
    if _debug: enumerated_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Enumerated(v)
    if _debug: enumerated_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert enumerated_encode(obj) == tag
    assert enumerated_decode(tag) == obj


@bacpypes_debugging
class TestEnumerated(unittest.TestCase):

    def test_enumerated(self):
        if _debug: TestEnumerated._debug("test_enumerated")

        obj = Enumerated()
        assert obj.value == 0

        with self.assertRaises(ValueError):
            Enumerated("label")
        with self.assertRaises(TypeError):
            Enumerated(1.0)

    def test_enumerated_int(self):
        if _debug: TestEnumerated._debug("test_enumerated_int")

        obj = Enumerated(1)
        assert obj.value == 1
        assert str(obj) == "Enumerated(1)"

        with self.assertRaises(ValueError):
            Enumerated(-1)

    def test_enumerated_tag(self):
        if _debug: TestEnumerated._debug("test_enumerated_tag")

        tag = Tag(Tag.applicationTagClass, Tag.enumeratedAppTag, 1, xtob('01'))
        obj = Enumerated(tag)
        assert obj.value == 1

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Enumerated(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Enumerated(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Enumerated(tag)

    def test_enumerated_copy(self):
        if _debug: TestEnumerated._debug("test_enumerated_copy")

        obj1 = Enumerated(12)
        obj2 = Enumerated(obj1)
        assert obj2.value == 12

    def test_enumerated_endec(self):
        if _debug: TestEnumerated._debug("test_enumerated_endec")

        with self.assertRaises(InvalidTag):
            obj = Enumerated(enumerated_tag(''))

        enumerated_endec(0, '00')
        enumerated_endec(1, '01')
        enumerated_endec(127, '7f')
        enumerated_endec(128, '80')
        enumerated_endec(255, 'ff')

        enumerated_endec(32767, '7fff')
        enumerated_endec(32768, '8000')

        enumerated_endec(8388607, '7fffff')
        enumerated_endec(8388608, '800000')

        enumerated_endec(2147483647, '7fffffff')
        enumerated_endec(2147483648, '80000000')