#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Object Identifier
-------------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import ObjectIdentifier, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def object_identifier_tag(x):
    """Convert a hex string to an object_identifier application tag."""
    if _debug: object_identifier_tag._debug("object_identifier_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.objectIdentifierAppTag, len(b), b)
    if _debug: object_identifier_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def object_identifier_encode(obj):
    """Encode an ObjectIdentifier object into a tag."""
    if _debug: object_identifier_encode._debug("object_identifier_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: object_identifier_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def object_identifier_decode(tag):
    """Decode an object_identifier application tag into an object_identifier."""
    if _debug: object_identifier_decode._debug("object_identifier_decode %r", tag)

    obj = ObjectIdentifier(tag)
    if _debug: object_identifier_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def object_identifier_endec(v, x):
    """Pass the value to ObjectIdentifier, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: object_identifier_endec._debug("object_identifier_endec %r %r", v, x)

    tag = object_identifier_tag(x)
    if _debug: object_identifier_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = ObjectIdentifier(v)
    if _debug: object_identifier_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert object_identifier_encode(obj) == tag
    assert object_identifier_decode(tag) == obj


@bacpypes_debugging
class TestObjectIdentifier(unittest.TestCase):

    def test_object_identifier(self):
        if _debug: TestObjectIdentifier._debug("test_object_identifier")

        obj = ObjectIdentifier()
        assert obj.value == ('analogInput', 0)

        with self.assertRaises(TypeError):
            ObjectIdentifier("some string")
        with self.assertRaises(TypeError):
            ObjectIdentifier(1.0)

    def test_object_identifier_int(self):
        if _debug: TestObjectIdentifier._debug("test_object_identifier_int")

        obj = ObjectIdentifier(1)
        assert obj.value == ('analogInput', 1)
        assert str(obj) == "ObjectIdentifier(analogInput,1)"

        obj = ObjectIdentifier(0x0400002)
        assert obj.value == ('analogOutput', 2)
        assert str(obj) == "ObjectIdentifier(analogOutput,2)"

    def test_object_identifier_tuple(self):
        if _debug: TestObjectIdentifier._debug("test_object_identifier_tuple")

        with self.assertRaises(ValueError):
            ObjectIdentifier((0, -1))
        with self.assertRaises(ValueError):
            ObjectIdentifier((0, ObjectIdentifier.maximum_instance_number + 1))

    def test_object_identifier_tag(self):
        if _debug: TestObjectIdentifier._debug("test_object_identifier_tag")

        tag = Tag(Tag.applicationTagClass, Tag.objectIdentifierAppTag, 1, xtob('06000003'))
        obj = ObjectIdentifier(tag)
        assert obj.value == ('pulseConverter', 3)

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            ObjectIdentifier(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            ObjectIdentifier(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            ObjectIdentifier(tag)

    def test_object_identifier_copy(self):
        if _debug: TestObjectIdentifier._debug("test_object_identifier_copy")

        obj1 = ObjectIdentifier(('analogInput', 1))
        obj2 = ObjectIdentifier(obj1)
        assert obj2.value == ('analogInput', 1)

    def test_object_identifier_endec(self):
        if _debug: TestObjectIdentifier._debug("test_object_identifier_endec")

        with self.assertRaises(InvalidTag):
            obj = ObjectIdentifier(object_identifier_tag(''))

        # test standard types
        object_identifier_endec(('analogInput', 0), '00000000')

        # test vendor types