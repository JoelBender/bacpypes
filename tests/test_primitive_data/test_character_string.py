#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Character String
------------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import InvalidTag
from bacpypes.primitivedata import CharacterString, Tag

# some debugging
_debug = 0
_log = ModuleLogger(globals())


# globals
fox_message = "the quick brown fox jumped over the lazy dog"

@bacpypes_debugging
def character_string_tag(x):
    """Convert a hex string to an character_string application tag."""
    if _debug: character_string_tag._debug("character_string_tag %r", x)

    b = xtob(x)
    tag = Tag(Tag.applicationTagClass, Tag.characterStringAppTag, len(b), b)
    if _debug: character_string_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def character_string_encode(obj):
    """Encode an CharacterString object into a tag."""
    if _debug: character_string_encode._debug("character_string_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    if _debug: character_string_endec._debug("    - tag: %r", tag)

    return tag


@bacpypes_debugging
def character_string_decode(tag):
    """Decode an character_string application tag into an character_string."""
    if _debug: character_string_decode._debug("character_string_decode %r", tag)

    obj = CharacterString(tag)
    if _debug: character_string_decode._debug("    - obj: %r", obj)

    return obj


@bacpypes_debugging
def character_string_endec(v, x):
    """Pass the value to CharacterString, construct a tag from the hex string,
    and compare results of encode and decoding each other."""
    if _debug: character_string_endec._debug("character_string_endec %r %r", v, x)

    tag = character_string_tag(x)
    if _debug: character_string_endec._debug("    - tag: %r, %r", tag, tag.tagData)

    obj = CharacterString(v)
    if _debug: character_string_endec._debug("    - obj: %r, %r", obj, obj.value)

    assert character_string_encode(obj) == tag
    assert character_string_decode(tag) == obj


@bacpypes_debugging
class TestCharacterString(unittest.TestCase):

    def test_character_string(self):
        if _debug: TestCharacterString._debug("test_character_string")

        obj = CharacterString()
        assert obj.value == ''

        with self.assertRaises(TypeError):
            CharacterString(1)
        with self.assertRaises(TypeError):
            CharacterString(1.0)

    def test_character_string_str(self):
        if _debug: TestCharacterString._debug("test_character_string_str")

        obj = CharacterString("hello")
        assert obj.value == "hello"
        assert str(obj) == "CharacterString(0,X'68656c6c6f')"

    def test_character_string_tag(self):
        if _debug: TestCharacterString._debug("test_character_string_tag")

        tag = Tag(Tag.applicationTagClass, Tag.characterStringAppTag, 1, xtob('00'))
        obj = CharacterString(tag)
        assert obj.value == ''

        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0, xtob(''))
        with self.assertRaises(InvalidTag):
            CharacterString(tag)

        tag = Tag(Tag.contextTagClass, 0, 1, xtob('ff'))
        with self.assertRaises(InvalidTag):
            CharacterString(tag)

        tag = Tag(Tag.openingTagClass, 0)
        with self.assertRaises(InvalidTag):
            CharacterString(tag)

    def test_character_string_copy(self):
        if _debug: TestCharacterString._debug("test_character_string_copy")

        obj1 = CharacterString(fox_message)
        obj2 = CharacterString(obj1)
        assert obj2.value == fox_message

    def test_character_string_endec(self):
        if _debug: TestCharacterString._debug("test_character_string_endec")

        with self.assertRaises(InvalidTag):
            obj = CharacterString(character_string_tag(''))

        character_string_endec("", '00')
        character_string_endec("abc", '00616263')