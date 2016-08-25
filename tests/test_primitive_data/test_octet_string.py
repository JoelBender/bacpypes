#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Octet String
--------------------------------
"""

import unittest
import struct

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import OctetString, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def octet_string_tag(x):
    """Convert a hex string to an octet_string application tag."""
    if _debug: octet_string_tag._debug("octet_string_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.octetStringAppTag, len(b), b)
    if _debug: octet_string_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def octet_string_encode(obj):
    """Encode an OctetString object into a tag."""
    if _debug: octet_string_encode._debug("octet_string_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: octet_string_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def octet_string_decode(tag):
    """Decode an octet_string application tag into an octet string."""
    if _debug: octet_string_decode._debug("octet_string_decode %r", tag)

    obj = OctetString(tag)
    if _debug: octet_string_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def octet_string_endec(x):
    """Pass the value to OctetString, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: octet_string_endec._debug("octet_string_endec %r", x)

    tag = octet_string_tag(x)
    if _debug: octet_string_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = OctetString(xtob(x))
    if _debug: octet_string_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert octet_string_encode(obj) == tag
    assert octet_string_decode(tag) == obj


@bacpypes_debugging
class TestOctetString(unittest.TestCase):

    def test_octet_string(self):
        if _debug: TestOctetString._debug("test_octet_string")

        obj = OctetString()
        assert obj.value == xtob('')

        with self.assertRaises(TypeError):
            OctetString(1)

    def test_octet_string_octet_string(self):
        if _debug: TestOctetString._debug("test_octet_string_octet_string")

        obj = OctetString(xtob('01'))
        assert obj.value == xtob('01')
        assert str(obj) == "OctetString(X'01')"

        obj = OctetString(xtob('01020304'))
        assert obj.value == xtob('01020304')
        assert str(obj) == "OctetString(X'01020304')"

    def test_octet_string_tag(self):
        if _debug: TestOctetString._debug("test_octet_string_tag")

        tag = Tag(Tag.applicationTagClass, Tag.octetStringAppTag, 1, xtob('00'))
        obj = OctetString(tag)
        assert obj.value == xtob('00')

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            OctetString(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            OctetString(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            OctetString(tag)

    def test_octet_string_copy(self):
        if _debug: TestOctetString._debug("test_octet_string_copy")

        obj1 = OctetString(xtob('01'))
        obj2 = OctetString(obj1)
        assert obj2.value == xtob('01')

    def test_octet_string_endec(self):
        if _debug: TestOctetString._debug("test_octet_string_endec")

        octet_string_endec('')
        octet_string_endec('01')
        octet_string_endec('0102')
        octet_string_endec('010203')
        octet_string_endec('01020304')