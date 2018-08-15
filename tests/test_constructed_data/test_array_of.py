#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Array
----------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.primitivedata import TagList, Integer, Time
from bacpypes.constructeddata import ArrayOf
from bacpypes.basetypes import TimeStamp

from .helpers import SimpleSequence

# some debugging
_debug = 0
_log = ModuleLogger(globals())


# array of integers
IntegerArray = ArrayOf(Integer)

@bacpypes_debugging
class TestIntegerArray(unittest.TestCase):

    def test_empty_array(self):
        if _debug: TestIntegerArray._debug("test_empty_array")

        # create an empty array
        ary = IntegerArray()
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # array sematics
        assert len(ary) == 0
        assert ary[0] == 0

        # encode it in a tag list
        tag_list = TagList()
        ary.encode(tag_list)
        if _debug: TestIntegerArray._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        ary = IntegerArray()
        ary.decode(tag_list)
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

    def test_append(self):
        if _debug: TestIntegerArray._debug("test_append")

        # create an empty array
        ary = IntegerArray()
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # append an integer
        ary.append(2)
        assert len(ary) == 1
        assert ary[0] == 1
        assert ary[1] == 2

    def test_delete_item(self):
        if _debug: TestIntegerArray._debug("test_delete_item")

        # create an array
        ary = IntegerArray([1, 2, 3])
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # delete something
        del ary[2]
        assert len(ary) == 2
        assert ary[0] == 2
        assert ary.value[1:] == [1, 3]

    def test_index_item(self):
        if _debug: TestIntegerArray._debug("test_index_item")

        # create an array
        ary = IntegerArray([1, 2, 3])
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # find something
        assert ary.index(3) == 3

        # not find something
        with self.assertRaises(ValueError):
            ary.index(4)

    def test_remove_item(self):
        if _debug: TestIntegerArray._debug("test_remove_item")

        # create an array
        ary = IntegerArray([1, 2, 3])
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # remove something
        ary.remove(2)
        assert ary.value[1:] == [1, 3]

        # not remove something
        with self.assertRaises(ValueError):
            ary.remove(4)

    def test_resize(self):
        if _debug: TestIntegerArray._debug("test_resize")

        # create an array
        ary = IntegerArray([1, 2, 3])
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # make it shorter
        ary[0] = 2
        assert ary.value[1:] == [1, 2]

        # make it longer
        ary[0] = 4
        assert ary.value[1:] == [1, 2, 0, 0]

    def test_get_item(self):
        if _debug: TestIntegerArray._debug("test_get_item")

        # create an array
        ary = IntegerArray([1, 2, 3])
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # BACnet semantics
        assert ary[1] == 1

    def test_set_item(self):
        if _debug: TestIntegerArray._debug("test_set_item")

        # create an array
        ary = IntegerArray([1, 2, 3])
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # BACnet semantics, no type checking
        ary[1] = 10
        assert ary[1] == 10

    def test_codec(self):
        if _debug: TestIntegerArray._debug("test_codec")

        # test array contents
        ary_value = [1, 2, 3]

        # create an array
        ary = IntegerArray(ary_value)
        if _debug: TestIntegerArray._debug("    - ary: %r", ary)

        # encode it in a tag list
        tag_list = TagList()
        ary.encode(tag_list)
        if _debug: TestIntegerArray._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        ary = IntegerArray()
        ary.decode(tag_list)
        if _debug: TestIntegerArray._debug("    - ary %r", ary)

        # value matches
        assert ary.value[1:] == ary_value


# fixed length array of integers
IntegerArray5 = ArrayOf(Integer, fixed_length=5)

@bacpypes_debugging
class TestIntegerArray5(unittest.TestCase):

    def test_empty_array(self):
        if _debug: TestIntegerArray5._debug("test_empty_array")

        # create an empty array
        ary = IntegerArray5()
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # array sematics
        assert len(ary) == 5
        assert ary[0] == 5

        # value correct
        assert ary.value[1:] == [0, 0, 0, 0, 0]

    def test_append(self):
        if _debug: TestIntegerArray5._debug("test_append")

        # create an empty array
        ary = IntegerArray5()
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # append an integer
        with self.assertRaises(TypeError):
            ary.append(2)

    def test_delete_item(self):
        if _debug: TestIntegerArray5._debug("test_delete_item")

        # create an array
        ary = IntegerArray5([1, 2, 3, 4, 5])
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # delete something
        with self.assertRaises(TypeError):
            del ary[2]

    def test_index_item(self):
        if _debug: TestIntegerArray5._debug("test_index_item")

        # create an array
        ary = IntegerArray5([1, 2, 3, 4, 5])
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # find something
        assert ary.index(3) == 3

        # not find something
        with self.assertRaises(ValueError):
            ary.index(100)

    def test_remove_item(self):
        if _debug: TestIntegerArray5._debug("test_remove_item")

        # create an array
        ary = IntegerArray5([1, 2, 3, 4, 5])
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # remove something
        with self.assertRaises(TypeError):
            ary.remove(4)

    def test_resize(self):
        if _debug: TestIntegerArray5._debug("test_resize")

        # create an array
        ary = IntegerArray5([1, 2, 3, 4, 5])
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # make it the same length (noop)
        ary[0] = 5

        # changing it to something else fails
        with self.assertRaises(TypeError):
            ary[0] = 4

    def test_get_item(self):
        if _debug: TestIntegerArray5._debug("test_get_item")

        # create an array
        ary = IntegerArray5([1, 2, 3, 4, 5])
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # BACnet semantics
        assert ary[1] == 1

    def test_set_item(self):
        if _debug: TestIntegerArray5._debug("test_set_item")

        # create an array
        ary = IntegerArray5([1, 2, 3, 4, 5])
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # BACnet semantics, no type checking
        ary[1] = 10
        assert ary[1] == 10

    def test_codec(self):
        if _debug: TestIntegerArray5._debug("test_codec")

        # test array contents
        ary_value = [1, 2, 3, 4, 5]

        # create an array
        ary = IntegerArray5(ary_value)
        if _debug: TestIntegerArray5._debug("    - ary: %r", ary)

        # encode it in a tag list
        tag_list = TagList()
        ary.encode(tag_list)
        if _debug: TestIntegerArray5._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        ary = IntegerArray()
        ary.decode(tag_list)
        if _debug: TestIntegerArray5._debug("    - ary %r", ary)

        # value matches
        assert ary.value[1:] == ary_value


# array of a sequence
SimpleSequenceArray = ArrayOf(SimpleSequence)

@bacpypes_debugging
class TestSimpleSequenceArray(unittest.TestCase):

    def test_codec(self):
        if _debug: TestSimpleSequenceArray._debug("test_codec")

        # test array contents
        ary_value = [
            SimpleSequence(hydrogen=True),
            SimpleSequence(hydrogen=False),
            SimpleSequence(hydrogen=True),
            ]

        # create an array
        ary = SimpleSequenceArray(ary_value)
        if _debug: TestSimpleSequenceArray._debug("    - ary: %r", ary)

        # encode it in a tag list
        tag_list = TagList()
        ary.encode(tag_list)
        if _debug: TestSimpleSequenceArray._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        ary = SimpleSequenceArray()
        ary.decode(tag_list)
        if _debug: TestSimpleSequenceArray._debug("    - ary %r", ary)

        # value matches
        assert ary.value[1:] == ary_value


# fixed length array of TimeStamps
ArrayOfTimeStamp = ArrayOf(TimeStamp, fixed_length=16,
    prototype=TimeStamp(time=Time().value),
    )

@bacpypes_debugging
class TestArrayOfTimeStamp(unittest.TestCase):

    def test_empty_array(self):
        if _debug: TestArrayOfTimeStamp._debug("test_empty_array")

        # create an empty array
        ary = ArrayOfTimeStamp()
        if _debug: TestArrayOfTimeStamp._debug("    - ary: %r", ary)

        # array sematics
        assert len(ary) == 16
        assert ary[0] == 16

