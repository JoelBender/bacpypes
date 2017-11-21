#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Object Services
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import ExecutionError, InvalidParameterDatatype
from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import ArrayOf
from bacpypes.object import register_object_type, ReadableProperty, \
    WritableProperty, Object

from bacpypes.service.object import CurrentPropertyListMixIn

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestBasic(unittest.TestCase):

    def test_basic(self):
        """Test basic configuration of a network."""
        if _debug: TestBasic._debug("test_basic")

        # create an object, no properties
        obj = Object()


@bacpypes_debugging
@register_object_type(vendor_id=999)
class SampleReadableLocation(Object):

    objectType = 'sampleReadableLocation'
    properties = [
        ReadableProperty('location', CharacterString),
        ]

    def __init__(self, **kwargs):
        if _debug: SampleReadableLocation._debug("__init__ %r", kwargs)
        Object.__init__(self, **kwargs)


@bacpypes_debugging
class TestReadableLocation(unittest.TestCase):

    def test_sample(self):
        """Test basic configuration of a network."""
        if _debug: TestReadableLocation._debug("test_sample")

        # create an object, default property value is None
        obj = SampleReadableLocation()
        assert obj.location == None

        # create an object with a location
        obj = SampleReadableLocation(location="home")
        assert obj.ReadProperty('location') == "home"

        # not an array, write access denied
        with self.assertRaises(ExecutionError):
            obj.ReadProperty('location', 0)
        with self.assertRaises(ExecutionError):
            obj.WriteProperty('location', "work")


@bacpypes_debugging
@register_object_type(vendor_id=999)
class SampleWritableLocation(Object):

    objectType = 'sampleWritableLocation'
    properties = [
        WritableProperty('location', CharacterString),
        ]

    def __init__(self, **kwargs):
        if _debug: SampleWritableLocation._debug("__init__ %r", kwargs)
        Object.__init__(self, **kwargs)


@bacpypes_debugging
class TestWritableLocation(unittest.TestCase):

    def test_sample(self):
        """Test basic configuration of a network."""
        if _debug: TestWritableLocation._debug("test_sample")

        # create an object with a location
        obj = SampleWritableLocation(location="home")
        assert obj.ReadProperty('location') == "home"

        # not an array, write access denied
        with self.assertRaises(ExecutionError):
            obj.ReadProperty('location', 0)

        # write access successful
        obj.WriteProperty('location', "work")
        assert obj.location == "work"

        # wrong data type
        with self.assertRaises(InvalidParameterDatatype):
            obj.WriteProperty('location', 12)


# array of character strings
ArrayOfCharacterString = ArrayOf(CharacterString)

@bacpypes_debugging
@register_object_type(vendor_id=999)
class SampleWritableArray(Object):

    objectType = 'sampleWritableLocation'
    properties = [
        WritableProperty('location', ArrayOfCharacterString),
        ]

    def __init__(self, **kwargs):
        if _debug: SampleWritableArray._debug("__init__ %r", kwargs)
        Object.__init__(self, **kwargs)


@bacpypes_debugging
class TestWritableArray(unittest.TestCase):

    def test_empty_array(self):
        """Test basic configuration of a network."""
        if _debug: TestWritableArray._debug("test_empty_array")

        # create an object with a location
        obj = SampleWritableArray(location=ArrayOfCharacterString())
        if _debug: TestWritableArray._debug("    - obj.location: %r", obj.location)

        assert len(obj.location) == 0
        assert obj.location[0] == 0

    def test_short_array(self):
        if _debug: TestWritableArray._debug("test_short_array")

        # create an object with a location
        obj = SampleWritableArray(location=ArrayOfCharacterString(["home"]))
        if _debug: TestWritableArray._debug("    - obj.location: %r", obj.location)

        assert obj.ReadProperty('location', 0) == 1
        assert obj.ReadProperty('location', 1) == "home"

    def test_changing_length(self):
        if _debug: TestWritableArray._debug("test_changing_length")

        # create an object with a location
        obj = SampleWritableArray(location=ArrayOfCharacterString(["home"]))
        if _debug: TestWritableArray._debug("    - obj.location: %r", obj.location)

        # change the length of the array
        obj.WriteProperty('location', 2, arrayIndex=0)
        assert obj.ReadProperty('location', 0) == 2

        # array extended with none, should get property default value
        assert obj.ReadProperty('location', 2) == ""

        # wrong datatype
        with self.assertRaises(InvalidParameterDatatype):
            obj.WriteProperty('location', "nope", arrayIndex=0)

    def test_changing_item(self):
        if _debug: TestWritableArray._debug("test_changing_item")

        # create an object with a location
        obj = SampleWritableArray(location=ArrayOfCharacterString(["home"]))
        if _debug: TestWritableArray._debug("    - obj.location: %r", obj.location)

        # change the element
        obj.WriteProperty('location', "work", arrayIndex=1)
        assert obj.ReadProperty('location', 1) == "work"

        # wrong datatype
        with self.assertRaises(InvalidParameterDatatype):
            obj.WriteProperty('location', 12, arrayIndex=1)

    def test_replacing_array(self):
        if _debug: TestWritableArray._debug("test_replacing_array")

        # create an object with a location
        obj = SampleWritableArray()
        if _debug: TestWritableArray._debug("    - obj.location: %r", obj.location)

        # replace the array
        obj.WriteProperty('location', ArrayOfCharacterString(["home", "work"]))
        assert obj.ReadProperty('location', 0) == 2
        assert obj.ReadProperty('location', 1) == "home"
        assert obj.ReadProperty('location', 2) == "work"


@bacpypes_debugging
@register_object_type(vendor_id=999)
class SampleLocationObject(CurrentPropertyListMixIn, Object):

    objectType = 'sampleLocationObject'
    properties = [
        WritableProperty('location', CharacterString),
        ]

    def __init__(self, **kwargs):
        if _debug: SampleWritableArray._debug("__init__ %r", kwargs)
        Object.__init__(self, **kwargs)


@bacpypes_debugging
class TestCurrentPropertyListMixIn(unittest.TestCase):

    def test_with_location(self):
        if _debug: TestCurrentPropertyListMixIn._debug("test_with_location")

        # create an object without a location
        obj = SampleLocationObject(location="home")
        if _debug: TestCurrentPropertyListMixIn._debug("    - obj.location: %r", obj.location)

        assert obj.propertyList.value == [1, "location"]

    def test_without_location(self):
        if _debug: TestCurrentPropertyListMixIn._debug("test_property_list_1")

        # create an object without a location
        obj = SampleLocationObject()
        if _debug: TestCurrentPropertyListMixIn._debug("    - obj.location: %r", obj.location)

        assert obj.propertyList.value == [0]

    def test_location_appears(self):
        if _debug: TestCurrentPropertyListMixIn._debug("test_location_appears")

        # create an object without a location
        obj = SampleLocationObject()
        if _debug: TestCurrentPropertyListMixIn._debug("    - obj.location: %r", obj.location)

        # give it a location
        obj.location = "away"
        assert obj.propertyList.value == [1, "location"]

    def test_location_disappears(self):
        if _debug: TestCurrentPropertyListMixIn._debug("test_location_disappears")

        # create an object without a location
        obj = SampleLocationObject(location="home")
        if _debug: TestCurrentPropertyListMixIn._debug("    - obj.location: %r", obj.location)

        # location 'removed'
        obj.location = None

        assert obj.propertyList.value == [0]

