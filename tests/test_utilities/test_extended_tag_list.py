#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities Extended Tag List
--------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.primitivedata import Tag, OpeningTag, ClosingTag, \
    Null, Boolean, Unsigned, Integer, Real, Double, OctetString, \
    CharacterString, BitString, Enumerated, Date, Time, ObjectIdentifier

from ..extended_tag_list import statement_to_tag, ExtendedTagList

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def tag_encode(obj, context=None):
    """Encode an atomic object into a tag."""
    if _debug: tag_encode._debug("tag_encode %r", obj)

    # encode it normally
    tag = Tag()
    obj.encode(tag)

    # check for context encoding
    if context is not None:
        tag = tag.app_to_context(context)

    if _debug: tag_encode._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def compare_tag_list(tag_string, *tags):
    """Compare the extended tag list interpretation of the string with
    the list of other tags provided."""
    if _debug: compare_tag_list._debug("compare_tag_list %r %r", tag_string, tags)

    tag_list = ExtendedTagList(tag_string)
    if _debug: compare_tag_list._debug("    - tag_list: %r", tag_list)

    # make sure they encode the same number of tags
    assert len(tag_list) == len(tags)

    # check each tag
    for x, y in zip(tag_list.tagList, tags):
        assert x == y


@bacpypes_debugging
class TestExtendedTagStatements(unittest.TestCase):

    def test_opening_closing_statements(self):
        if _debug: TestExtendedTagStatements._debug("test_opening_closing_statements")

        # test individual statements
        assert statement_to_tag("opening tag 1") == OpeningTag(1)
        assert statement_to_tag("closing tag 1") == ClosingTag(1)

    def test_null_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_null_statement")

        # test atomic tags
        assert statement_to_tag("null") == tag_encode(Null())
        assert statement_to_tag("null context 1") == tag_encode(Null(), context=1)

    def test_boolean_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_boolean_statement")

        assert statement_to_tag("boolean false") == tag_encode(Boolean(False))
        assert statement_to_tag("boolean true") == tag_encode(Boolean(True))
        assert statement_to_tag("boolean true context 2") == tag_encode(Boolean(True), context=2)

    def test_unsigned_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_unsigned_statement")

        assert statement_to_tag("unsigned 0") == tag_encode(Unsigned(0))
        assert statement_to_tag("unsigned 1") == tag_encode(Unsigned(1))
        assert statement_to_tag("unsigned 1 context 3") == tag_encode(Unsigned(1), context=3)

    def test_integer_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_integer_statement")

        assert statement_to_tag("integer 0") == tag_encode(Integer(0))
        assert statement_to_tag("integer 1") == tag_encode(Integer(1))
        assert statement_to_tag("integer -1") == tag_encode(Integer(-1))
        assert statement_to_tag("integer 1 context 4") == tag_encode(Integer(1), context=4)

    def test_real_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_real_statement")

        assert statement_to_tag("real 0.0") == tag_encode(Real(0.0))
        assert statement_to_tag("real 72.5") == tag_encode(Real(72.5))
        assert statement_to_tag("real 3.14 context 5") == tag_encode(Real(3.14), context=5)

    def test_double_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_double_statement")

        assert statement_to_tag("double 0.0") == tag_encode(Double(0.0))
        assert statement_to_tag("double 75.2") == tag_encode(Double(75.2))
        assert statement_to_tag("double 6.28 context 6") == tag_encode(Double(6.28), context=6)

    def test_octet_string_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_octet_string_statement")

        assert statement_to_tag("octet string 0102") == tag_encode(OctetString(xtob("0102")))
        assert statement_to_tag("octet string 01020304 context 7") == tag_encode(OctetString(xtob("01020304")), context=7)

    def test_character_string_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_character_string_statement")

        assert statement_to_tag("character string ''") == tag_encode(CharacterString(""))
        assert statement_to_tag("character string 'hello'") == tag_encode(CharacterString("hello"))
        assert statement_to_tag("character string 'hi' context 8") == tag_encode(CharacterString("hi"), context=8)

    def test_bit_string_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_bit_string_statement")

        assert statement_to_tag("bit string 101") == tag_encode(BitString([1, 0, 1]))
        assert statement_to_tag("bit string 10111 context 9") == tag_encode(BitString([1, 0, 1, 1, 1]), context=9)

    def test_enumerated_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_enumerated_statement")

        assert statement_to_tag("enumerated 5") == tag_encode(Enumerated(5))
        assert statement_to_tag("enumerated 5 context 10") == tag_encode(Enumerated(5), context=10)

    def test_date_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_date_statement")

        assert statement_to_tag("date 1/1/70") == tag_encode(Date((70, 1, 1, 4)))

        # note that the day of the week is not optional for date statements with a context
        assert statement_to_tag("date 2015-8-31 1 context 11") == tag_encode(Date((115, 8, 31, 1)), context=11)

    def test_time_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_time_statement")

        assert statement_to_tag("time 1:2") == tag_encode(Time((1, 2, 0, 0)))
        assert statement_to_tag("time 1:2:3.4 context 12") == tag_encode(Time((1, 2, 3, 40)), context=12)

    def test_object_identifier_statement(self):
        if _debug: TestExtendedTagStatements._debug("test_object_identifier_statement")

        assert statement_to_tag("object identifier analogInput 1") == tag_encode(ObjectIdentifier('analogInput', 1))
        assert statement_to_tag("object identifier 99 1 context 13") == tag_encode(ObjectIdentifier(99, 1), context=13)


@bacpypes_debugging
class TestExtendedTagList(unittest.TestCase):

    def test_tag_list(self):
        if _debug: TestExtendedTagList._debug("test_tag_list")

        compare_tag_list("""
            opening tag 1
            integer 2
            closing tag 3
            """,
            OpeningTag(1),
            tag_encode(Integer(2)),
            ClosingTag(3),
            )