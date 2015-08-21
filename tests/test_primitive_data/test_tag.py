#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Tag
-----------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.primitivedata import Tag, ApplicationTag, ContextTag, \
    OpeningTag, ClosingTag, TagList, DecodingError
from bacpypes.pdu import PDUData

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def tag(tag_class, tag_number, x):
    """Create a tag object with the given class, number, and data."""
    if _debug: tag._debug("tag %r %r %r", tag_class, tag_number, x)

    b = xtob(x)
    tag = Tag(tag_class, tag_number, len(b), b)
    if _debug: tag_tuple._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
class TestTag(unittest.TestCase):

    def test_tag(self):
        if _debug: TestTag._debug("test_tag")

        ### test tag construction


@bacpypes_debugging
class TestApplicationTag(unittest.TestCase):

    def test_application_tag(self):
        if _debug: TestApplicationTag._debug("test_application_tag")

        ### test application tag construction, encoding, and decoding
        ### test tag conversion from application to context
        ### test tag conversion from context to application
        ### test application tag to primitive object


@bacpypes_debugging
class TestContextTag(unittest.TestCase):

    def test_context_tag(self):
        if _debug: TestContextTag._debug("test_context_tag")

        ### test context tag construction, encoding, and decoding


@bacpypes_debugging
class TestOpeningTag(unittest.TestCase):

    def test_opening_tag(self):
        if _debug: TestOpeningTag._debug("test_opening_tag")

        ### test opening tag construction, encoding, and decoding


@bacpypes_debugging
class TestClosingTag(unittest.TestCase):

    def test_closing_tag(self):
        if _debug: TestClosingTag._debug("test_closing_tag")

        ### test closing tag construction, encoding, and decoding


@bacpypes_debugging
class TestTagList(unittest.TestCase):

    def test_tag_list(self):
        if _debug: TestTagList._debug("test_tag_list")

        ### test tag list construction, encoding, and decoding
