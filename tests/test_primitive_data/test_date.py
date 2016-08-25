#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Date
---------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import Date, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
def date_tag(x):
    """Convert a hex string to a date application tag."""
    if _debug: date_tag._debug("date_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.dateAppTag, len(b), b)
    if _debug: date_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def date_encode(obj):
    """Encode an Date object into a tag."""
    if _debug: date_encode._debug("date_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: date_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def date_decode(tag):
    """Decode a date application tag into a date."""
    if _debug: date_decode._debug("date_decode %r", tag)

    obj = Date(tag)
    if _debug: date_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def date_endec(v, x):
    """Pass the value to Date, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: date_endec._debug("date_endec %r %r", v, x)

    tag = date_tag(x)
    if _debug: date_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = Date(v)
    if _debug: date_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert date_encode(obj) == tag
    assert date_decode(tag) == obj


@bacpypes_debugging
class TestDate(unittest.TestCase):

    def test_date(self):
        if _debug: TestDate._debug("test_date")

        # default values is all dont care
        obj = Date()
        assert obj.value == (255, 255, 255, 255)

        with self.assertRaises(ValueError):
            Date("some string")
        with self.assertRaises(TypeError):
            Date(1.0)

    def test_date_tuple(self):
        if _debug: TestDate._debug("test_date_tuple")

        obj = Date((1,2,3,4))
        assert obj.value == (1,2,3,4)
        assert str(obj) == "Date(1901-2-3 thu)"

    def test_date_tag(self):
        if _debug: TestDate._debug("test_date_tag")

        tag = Tag(Tag.applicationTagClass, Tag.dateAppTag, 4, xtob('01020304'))
        obj = Date(tag)
        assert obj.value == (1, 2, 3, 4)

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            Date(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            Date(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            Date(tag)

    def test_date_copy(self):
        if _debug: TestDate._debug("test_date_copy")

        value = (1, 2, 3, 4)
        obj1 = Date(value)
        obj2 = Date(obj1)
        assert obj2.value == value

    def test_date_endec(self):
        if _debug: TestDate._debug("test_date_endec")

        with self.assertRaises(InvalidTag):
            obj = Date(date_tag(''))

    def old_tests(self):
        self.test_values = [
            #('1/2/3', 1903, 2, 1, 0),
            #('1/2/3', 1903, 2, 1, 0),
            ("1/2/2003", 2003, 2, 1, 6),
            ("1/20/2003", 2003, 1, 20, 1),
            ("01/20/2004", 2004, 1, 20, 2),
            ("11/12/2005", 2005, 12, 11, 7),
            ("30/1/2006", 2006, 1, 30, 1),
            ("30/1/1230", 1230, 1, 30, 255),
            ("30/1/98", 1998, 1, 30, 5),
            ("2015/8/31", 2015, 8, 31, 1),
            ("2015/08/30", 2015, 8, 30, 7),
            ("2015/*/30", 2015,255,30,255),
            ("2015/1/*",2015,1,255,255),
            ("*/1/*", 255,1,255,255),
            ("*/*/*",255,255,255,255),
            ("1-2-2003", 2003, 2, 1, 6),
            ("1-20-2003", 2003, 1, 20, 1),
            ("01-20-2004", 2004, 1, 20, 2),
            ("11-12-2005", 2005, 12, 11, 7),
            ("30-1-2006", 2006, 1, 30, 1),
            ("30-1-1230", 1230, 1, 30, 255),
            ("30-1-98", 1998, 1, 30, 5),
            ("2015-8-31", 2015, 8, 31, 1),
            ("2015-08-30", 2015, 8, 30, 7),
            ("2015-*-30", 2015,255,30,255),
            ("2015-1-*",2015,1,255,255),
            ("*-1-*", 255,1,255,255),
            ("*-*-*",255,255,255,255)
        ]

        self.notEnoughPreciseOrWrong = [
            ('1/31/1'),
            ('0/1/4'),
            ('99/13/41'),
            ("2015/30/*")        
        ]

        def test_Date_from_str(self):
            for each in self.test_values:
                new_date = Date(each[0])
                y, m, d, dow = new_date.value
                self.assertEqual(y,each[1])
                self.assertEqual(m,each[2])
                self.assertEqual(d,each[3])
                self.assertEqual(dow,each[4])
            
        def test_Wrong(self):
            with self.assertRaises(ValueError):        
                for each in self.notEnoughPreciseOrWrong:
                    new_date = Date(each[0])