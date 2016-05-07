#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Bit String
-------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import BitString, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


class SampleBitString(BitString):
    bitLen = 13
    bitNames = {
        'b0': 0,
        'b1': 1,
        'b4': 4,
        'b7': 7,
        'b8': 8,
        'b12': 12,
        }


@bacpypes_debugging
def bit_string_tag(x):
    """Convert a hex string to an bit_string application tag."""
    if _debug: bit_string_tag._debug("bit_string_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.bitStringAppTag, len(b), b)
    if _debug: bit_string_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def bit_string_encode(obj):
    """Encode an BitString object into a tag."""
    if _debug: bit_string_encode._debug("bit_string_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: bit_string_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def bit_string_decode(tag):
    """Decode an bit_string application tag into an bit_string."""
    if _debug: bit_string_decode._debug("bit_string_decode %r", tag)

    obj = BitString(tag)
    if _debug: bit_string_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def bit_string_endec(v, x):
    """Pass the value to BitString, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: bit_string_endec._debug("bit_string_endec %r %r", v, x)

    tag = bit_string_tag(x)
    if _debug: bit_string_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = BitString(v)
    if _debug: bit_string_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert bit_string_encode(obj) == tag
    assert bit_string_decode(tag) == obj


@bacpypes_debugging
class TestBitString(unittest.TestCase):

    def test_bit_string(self):
        if _debug: TestBitString._debug("test_bit_string")

        obj = BitString()
        assert obj.value == []
        assert str(obj) == "BitString()"

        obj = BitString([0])
        assert obj.value == [0]
        assert str(obj) == "BitString(0)"

        obj = BitString([0, 1])
        assert obj.value == [0, 1]
        assert str(obj) == "BitString(0,1)"

        with self.assertRaises(TypeError):
            BitString("some string")
        with self.assertRaises(TypeError):
            BitString(1.0)

    def test_bit_string_sample(self):
        if _debug: TestBitString._debug("test_bit_string_sample")

        obj = SampleBitString()
        assert obj.value == [0] * SampleBitString.bitLen

        obj = SampleBitString([1])
        assert str(obj) == "BitString(b0)"

        obj = SampleBitString(['b4'])
        assert str(obj) == "BitString(!b0,!b1,0,0,b4,0,0,!b7,!b8,0,0,0,!b12)"

        with self.assertRaises(TypeError):
            SampleBitString(["x1"])

    def test_bit_string_tag(self):
        if _debug: TestBitString._debug("test_bit_string_tag")

        tag = Tag(Tag.applicationTagClass, Tag.bitStringAppTag, 1, xtob('08'))
        obj = BitString(tag)
        if _debug: TestBitString._debug("    - obj.value: %r", obj.value)
        assert obj.value == []

        tag = Tag(Tag.applicationTagClass, Tag.bitStringAppTag, 2, xtob('0102'))
        obj = BitString(tag)
        if _debug: TestBitString._debug("    - obj.value: %r", obj.value)
        assert obj.value == [0, 0, 0, 0, 0, 0, 1]

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            BitString(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            BitString(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            BitString(tag)

    def test_bit_string_copy(self):
        if _debug: TestBitString._debug("test_bit_string_copy")

        sample_value = [0, 1, 0, 1]
        obj1 = BitString(sample_value)
        obj2 = BitString(obj1)
        assert obj2.value == sample_value

    def test_bit_string_endec(self):
        if _debug: TestBitString._debug("test_bit_string_endec")

        bit_string_endec([], '00')
        bit_string_endec([0], '0700')
        bit_string_endec([1], '0780')
        bit_string_endec([0] * 2, '0600')
        bit_string_endec([1] * 2, '06c0')
        bit_string_endec([0] * 10, '060000')
        bit_string_endec([1] * 10, '06ffc0')