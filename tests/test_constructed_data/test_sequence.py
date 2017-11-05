#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Constructed Data Sequence
------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import MissingRequiredParameter
from bacpypes.primitivedata import Boolean, Integer, Tag, TagList
from bacpypes.constructeddata import Element, Sequence

from .helpers import EmptySequence, SimpleSequence, CompoundSequence1, \
    CompoundSequence2

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestEmptySequence(unittest.TestCase):

    def test_empty_sequence(self):
        if _debug: TestEmptySequence._debug("test_empty_sequence")

        # create a sequence
        seq = EmptySequence()
        if _debug: TestEmptySequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        seq.encode(tag_list)
        if _debug: TestEmptySequence._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        seq = EmptySequence()
        seq.decode(tag_list)
        if _debug: TestEmptySequence._debug("    - seq: %r", seq)

    def test_no_elements(self):
        if _debug: TestEmptySequence._debug("test_no_elements")

        # create a sequence with an undefined element
        with self.assertRaises(TypeError):
            seq = EmptySequence(some_element=None)


@bacpypes_debugging
class TestSimpleSequence(unittest.TestCase):

    def test_missing_element(self):
        if _debug: TestSimpleSequence._debug("test_missing_element")

        # create a sequence with a missing required element
        seq = SimpleSequence()
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

    def test_wrong_type(self):
        if _debug: TestSimpleSequence._debug("test_wrong_type")

        # create a sequence with wrong element value type
        seq = SimpleSequence(hydrogen=12)
        with self.assertRaises(TypeError):
            tag_list = TagList()
            seq.encode(tag_list)

    def test_codec(self):
        if _debug: TestSimpleSequence._debug("test_codec")

        # create a sequence
        seq = SimpleSequence(hydrogen=False)
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        seq.encode(tag_list)
        if _debug: TestSimpleSequence._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        seq = SimpleSequence()
        seq.decode(tag_list)
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)


@bacpypes_debugging
class TestCompoundSequence1(unittest.TestCase):

    def test_missing_element(self):
        if _debug: TestCompoundSequence1._debug("test_missing_element")

        # create a sequence with a missing required element
        seq = CompoundSequence1()
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

        # create a sequence with a missing required element
        seq = CompoundSequence1(hydrogen=True)
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

        # create a sequence with a missing required element
        seq = CompoundSequence1(helium=2)
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

    def test_codec(self):
        if _debug: TestCompoundSequence1._debug("test_codec")

        # create a sequence
        seq = CompoundSequence1(hydrogen=True, helium=2)
        if _debug: TestCompoundSequence1._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        seq.encode(tag_list)
        if _debug: TestCompoundSequence1._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        seq = CompoundSequence1()
        seq.decode(tag_list)
        if _debug: TestCompoundSequence1._debug("    - seq: %r", seq)


@bacpypes_debugging
class TestCompoundSequence2(unittest.TestCase):

    def test_missing_element(self):
        if _debug: TestCompoundSequence2._debug("test_missing_element")

        # create a sequence with a missing required element
        seq = CompoundSequence2()
        if _debug: TestCompoundSequence2._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

        # create a sequence with a missing required element
        seq = CompoundSequence2(lithium=True)
        if _debug: TestCompoundSequence2._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

    def test_codec_1(self):
        if _debug: TestCompoundSequence2._debug("test_codec_1")

        # create a sequence
        seq = CompoundSequence2(beryllium=2)
        if _debug: TestCompoundSequence2._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        seq.encode(tag_list)
        if _debug: TestCompoundSequence2._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        seq = CompoundSequence2()
        seq.decode(tag_list)
        if _debug: TestCompoundSequence2._debug("    - seq: %r", seq)

    def test_codec_2(self):
        if _debug: TestCompoundSequence2._debug("test_codec_2")

        # create a sequence
        seq = CompoundSequence2(lithium=True, beryllium=3)
        if _debug: TestCompoundSequence2._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        seq.encode(tag_list)
        if _debug: TestCompoundSequence2._debug("    - tag_list: %r", tag_list)

        # create another sequence and decode the tag list
        seq = CompoundSequence2()
        seq.decode(tag_list)
        if _debug: TestCompoundSequence2._debug("    - seq: %r", seq)


