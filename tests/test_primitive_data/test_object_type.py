#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data ObjectType
------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import ObjectType, Tag, expand_enumerations

# some debugging
_debug = 0
_log = ModuleLogger(globals())


class MyObjectType(ObjectType):
    enumerations = {
        'myAnalogInput': 128,
        'myAnalogOutput': 129,
        'myAnalogValue': 130,
    }

expand_enumerations(MyObjectType)


@bacpypes_debugging
def object_type_tag(x):
    """Convert a hex string to an enumerated application tag."""
    if _debug: object_type_tag._debug("object_type_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.enumeratedAppTag, len(b), b)
    if _debug: object_type_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def object_type_encode(obj):
    """Encode an ObjectType object into a tag."""
    if _debug: object_type_encode._debug("object_type_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: object_type_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def object_type_decode(tag):
    """Decode an enumerated application tag into an object_type."""
    if _debug: object_type_decode._debug("object_type_decode %r", tag)

    obj = ObjectType(tag)
    if _debug: object_type_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def object_type_endec(v, x):
    """Pass the value to ObjectType, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: object_type_endec._debug("object_type_endec %r %r", v, x)

    tag = object_type_tag(x)
    if _debug: object_type_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = ObjectType(v)
    if _debug: object_type_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert object_type_encode(obj) == tag
    assert object_type_decode(tag) == obj


@bacpypes_debugging
class TestObjectType(unittest.TestCase):

    def test_object_type(self):
        if _debug: TestObjectType._debug("test_object_type")

        obj = ObjectType()
        assert obj.value == 0

        with self.assertRaises(ValueError):
            ObjectType("unknownType")
        with self.assertRaises(TypeError):
            ObjectType(1.0)

    def test_object_type_int(self):
        if _debug: TestObjectType._debug("test_object_type_int")

        # known values are translated into strings
        obj = ObjectType(0)
        assert obj.value == 'analogInput'
        assert str(obj) == "ObjectType(analogInput)"

        # unknown values are kept as integers
        obj = ObjectType(127)
        assert obj.value == 127
        assert str(obj) == "ObjectType(127)"

    def test_object_type_str(self):
        if _debug: TestObjectType._debug("test_object_type_str")

        # known strings are accepted
        obj = ObjectType('analogInput')
        assert obj.value == 'analogInput'

    def test_extended_object_type_int(self):
        if _debug: TestObjectType._debug("test_extended_object_type_int")

        # known values are translated into strings
        obj = MyObjectType(0)
        assert obj.value == 'analogInput'
        assert str(obj) == "MyObjectType(analogInput)"

        # unknown values are kept as integers
        obj = MyObjectType(128)
        assert obj.value == 'myAnalogInput'
        assert str(obj) == "MyObjectType(myAnalogInput)"

    def test_extended_object_type_str(self):
        if _debug: TestObjectType._debug("test_extended_object_type_str")

        # known strings are accepted
        obj = MyObjectType('myAnalogInput')
        assert obj.value == 'myAnalogInput'

        # unknown strings are rejected
        with self.assertRaises(ValueError):
            MyObjectType('snork')

    def test_object_type_tag(self):
        if _debug: TestObjectType._debug("test_object_type_tag")

        tag = Tag(Tag.applicationTagClass, Tag.enumeratedAppTag, 1, xtob('01'))
        obj = ObjectType(tag)
        assert obj.value == 'analogOutput'

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            ObjectType(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            ObjectType(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            ObjectType(tag)

    def test_object_type_copy(self):
        if _debug: TestObjectType._debug("test_object_type_copy")

        # known values are translated into strings
        obj1 = ObjectType(12)
        obj2 = ObjectType(obj1)
        assert obj2.value == 'loop'

    def test_object_type_endec(self):
        if _debug: TestObjectType._debug("test_object_type_endec")

        with self.assertRaises(InvalidTag):
            obj = ObjectType(object_type_tag(''))

        object_type_endec('analogInput', '00')
        object_type_endec('analogOutput', '01')

        object_type_endec(127, '7f')
        object_type_endec(128, '80')