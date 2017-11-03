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

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class EmptySequence(Sequence):

    def __init__(self, *args, **kwargs):
        if _debug: EmptySequence._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)


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
class SimpleSequence(Sequence):

    sequenceElements = [
        Element('hydrogen', Boolean),
        ]

    def __init__(self, *args, **kwargs):
        if _debug: SimpleSequence._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)


@bacpypes_debugging
class TestSimpleSequence(unittest.TestCase):

    def test_simple_sequence_missing(self):
        if _debug: TestSimpleSequence._debug("test_simple_sequence_missing")

        # create a sequence with a missing required element
        seq = SimpleSequence()
        if _debug: TestSimpleSequence._debug("    - seq: %r", seq)

        # encode it in a tag list
        tag_list = TagList()
        with self.assertRaises(MissingRequiredParameter):
            seq.encode(tag_list)

    def test_simple_sequence(self):
        if _debug: TestSimpleSequence._debug("test_simple_sequence")

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

    def test_simple_sequence_wrong_type(self):
        if _debug: TestSimpleSequence._debug("test_simple_sequence_wrong_type")

        # create a sequence with wrong element value type
        seq = SimpleSequence(hydrogen=12)
        with self.assertRaises(TypeError):
            tag_list = TagList()
            seq.encode(tag_list)


@bacpypes_debugging
class CompoundSequenceOne(Sequence):

    sequenceElements = [
        Element('hydrogen', Boolean),
        Element('helium', Integer),
        ]

    def __init__(self, *args, **kwargs):
        if _debug: CompoundSequenceOne._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)


