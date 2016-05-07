#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Primitive Data Tag
-----------------------
"""

import unittest

from bacpypes.errors import InvalidTag
from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob, btox
from bacpypes.primitivedata import Tag, ApplicationTag, ContextTag, \
    OpeningTag, ClosingTag, TagList, \
    Null, Boolean, Unsigned, Integer, Real, Double, OctetString, \
    CharacterString, BitString, Enumerated, Date, Time, ObjectIdentifier
from bacpypes.pdu import PDUData


# some debugging
_debug = 0
_log = ModuleLogger(globals())


def tag_tuple(tag):
    """Simple function to decompose a tag for debugging."""
    return (tag.tagClass, tag.tagNumber, tag.tagLVT, tag.tagData)


@bacpypes_debugging
def IntegerTag(v):
    """Return an application encoded integer tag with the appropriate value.
    """
    obj = Integer(v)
    tag = Tag()
    obj.encode(tag)
    return tag


@bacpypes_debugging
def obj_decode(blob):
    """Build PDU from the string, decode the tag, convert to an object."""
    if _debug: obj_decode._debug("obj_decode %r", blob)

    data = PDUData(blob)
    tag = Tag(data)
    obj = tag.app_to_object()
    return obj


@bacpypes_debugging
def obj_encode(obj):
    """Encode the object into a tag, encode it in a PDU, return the data."""
    if _debug: obj_encode._debug("obj_encode %r", obj)

    tag = Tag()
    obj.encode(tag)
    data = PDUData()
    tag.encode(data)
    return data.pduData


@bacpypes_debugging
def obj_endec(obj, x):
    """Convert the value (a primitive object) to a hex encoded string, 
    convert the hex encoded string to and object, and compare the results to
    each other."""
    if _debug: obj_endec._debug("obj_endec %r %r", obj, x)

    # convert the hex string to a blob
    blob = xtob(x)

    # decode the blob into an object
    obj2 = obj_decode(blob)
    if _debug: obj_endec._debug("    - obj: %r, %r", obj, obj.value)

    # encode the object into a blob
    blob2 = obj_encode(obj)
    if _debug: obj_endec._debug("    - blob2: %r", blob2)

    # compare the results
    assert obj == obj2
    assert blob == blob2


@bacpypes_debugging
def context_decode(blob):
    """Build PDU from the string, decode the tag, convert to an object."""
    if _debug: context_decode._debug("context_decode %r", blob)

    data = PDUData(blob)
    tag = ContextTag(data)
    return tag


@bacpypes_debugging
def context_encode(tag):
    """Encode the object into a tag, encode it in a PDU, return the data."""
    if _debug: context_encode._debug("context_encode %r", tag)

    data = PDUData()
    tag.encode(data)
    return data.pduData


@bacpypes_debugging
def context_endec(tnum, x, y):
    """Convert the value (a primitive object) to a hex encoded string, 
    convert the hex encoded string to and object, and compare the results to
    each other."""
    if _debug: context_endec._debug("context_endec %r %r %r", tnum, x, y)

    # convert the hex strings to a blobs
    tdata = xtob(x)
    blob1 = xtob(y)

    # make a context tag
    tag1 = ContextTag(tnum, tdata)

    # decode the blob into a tag
    tag2 = context_decode(blob1)
    if _debug: context_endec._debug("    - tag: %r", tag)

    # encode the tag into a blob
    blob2 = context_encode(tag1)
    if _debug: context_endec._debug("    - blob2: %r", blob2)

    # compare the results
    assert tag1 == tag2
    assert blob1 == blob2


@bacpypes_debugging
def opening_decode(blob):
    """Build PDU from the string, decode the tag, convert to an object."""
    if _debug: opening_decode._debug("opening_decode %r", blob)

    data = PDUData(blob)
    tag = OpeningTag(data)
    return tag


@bacpypes_debugging
def opening_encode(tag):
    """Encode the object into a tag, encode it in a PDU, return the data."""
    if _debug: opening_encode._debug("opening_encode %r", tag)

    data = PDUData()
    tag.encode(data)
    return data.pduData


@bacpypes_debugging
def opening_endec(tnum, x):
    """Convert the value (a primitive object) to a hex encoded string, 
    convert the hex encoded string to and object, and compare the results to
    each other."""
    if _debug: opening_endec._debug("opening_endec %r %r", tnum, x)

    # convert the hex string to a blob
    blob1 = xtob(x)

    # make a context tag
    tag1 = OpeningTag(tnum)
    if _debug: opening_endec._debug("    - tag1: %r", tag1)

    # decode the blob into a tag
    tag2 = opening_decode(blob1)
    if _debug: opening_endec._debug("    - tag2: %r", tag2)

    # encode the tag into a blob
    blob2 = opening_encode(tag1)
    if _debug: opening_endec._debug("    - blob2: %r", blob2)

    # compare the results
    assert tag1 == tag2
    assert blob1 == blob2


@bacpypes_debugging
def closing_decode(blob):
    """Build PDU from the string, decode the tag, convert to an object."""
    if _debug: closing_decode._debug("closing_decode %r", blob)

    data = PDUData(blob)
    tag = ClosingTag(data)
    return tag


@bacpypes_debugging
def closing_encode(tag):
    """Encode the object into a tag, encode it in a PDU, return the data."""
    if _debug: closing_encode._debug("closing_encode %r", tag)

    data = PDUData()
    tag.encode(data)
    return data.pduData


@bacpypes_debugging
def closing_endec(tnum, x):
    """Convert the value (a primitive object) to a hex encoded string, 
    convert the hex encoded string to and object, and compare the results to
    each other."""
    if _debug: closing_endec._debug("closing_endec %r %r", tnum, x)

    # convert the hex string to a blob
    blob1 = xtob(x)

    # make a context tag
    tag1 = ClosingTag(tnum)
    if _debug: closing_endec._debug("    - tag1: %r", tag1)

    # decode the blob into a tag
    tag2 = closing_decode(blob1)
    if _debug: closing_endec._debug("    - tag2: %r", tag2)

    # encode the tag into a blob
    blob2 = closing_encode(tag1)
    if _debug: closing_endec._debug("    - blob2: %r", blob2)

    # compare the results
    assert tag1 == tag2
    assert blob1 == blob2


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

        # test tag construction
        tag = Tag()
        assert (tag.tagClass, tag.tagNumber) == (None, None)

        # must have a valid encoded tag to extract from the data
        data = PDUData(xtob(''))
        with self.assertRaises(InvalidTag):
            tag = Tag(data)

        # must have two values, class and number
        with self.assertRaises(ValueError):
            tag = Tag(0)

        tag = Tag(0, 1)
        assert (tag.tagClass, tag.tagNumber) == (0, 1)

        tag = Tag(0, 1, 2)
        assert (tag.tagClass, tag.tagNumber, tag.tagLVT) == (0, 1, 2)

        # tag data must be bytes or bytearray
        with self.assertRaises(TypeError):
            tag = Tag(0, 1, 2, 3)

@bacpypes_debugging
class TestApplicationTag(unittest.TestCase):

    def test_application_tag(self):
        if _debug: TestApplicationTag._debug("test_application_tag")

        # application tag construction, encoding, and decoding
        tag = ApplicationTag(0, xtob(''))
        if _debug: TestApplicationTag._debug("    - tag: %r", tag_tuple(tag))

        with self.assertRaises(ValueError):
            tag = ApplicationTag(0)

    def test_generic_application_to_context(self):
        if _debug: TestApplicationTag._debug("test_generic_application_to_context")

        # create an application
        tag = ApplicationTag(0, xtob('01'))
        if _debug: TestApplicationTag._debug("    - tag: %r", tag_tuple(tag))

        # convert it to context tagged, context 0
        ctag = tag.app_to_context(0)
        if _debug: TestApplicationTag._debug("    - ctag: %r", tag_tuple(ctag))

        # create a context tag with the same shape
        ttag = ContextTag(0, xtob('01'))
        if _debug: TestApplicationTag._debug("    - ttag: %r", tag_tuple(ttag))

        # check to see they are the same
        assert ctag == ttag

        # convert the context tag back to an application tag
        dtag = ctag.context_to_app(0)
        if _debug: TestApplicationTag._debug("    - dtag: %r", tag_tuple(dtag))

        # check to see it round-tripped
        assert dtag == tag

    def test_boolean_application_to_context(self):
        if _debug: TestApplicationTag._debug("test_boolean_application_to_context")

        # create an application
        tag = Tag(Tag.applicationTagClass, Tag.booleanAppTag, 0)
        if _debug: TestApplicationTag._debug("    - tag: %r", tag_tuple(tag))

        # convert it to context tagged, context 0
        ctag = tag.app_to_context(0)
        if _debug: TestApplicationTag._debug("    - ctag: %r", tag_tuple(ctag))

        # create a context tag with the same shape
        ttag = ContextTag(0, xtob('00'))
        if _debug: TestApplicationTag._debug("    - ttag: %r", tag_tuple(ttag))

        # check to see they are the same
        assert ctag == ttag

        # convert the context tag back to an application tag
        dtag = ctag.context_to_app(Tag.booleanAppTag)
        if _debug: TestApplicationTag._debug("    - dtag: %r", tag_tuple(dtag))

        # check to see it round-tripped
        assert dtag == tag

    def test_boolean_application_to_object(self):
        if _debug: TestApplicationTag._debug("test_boolean_application_to_object")

        # null
        obj_endec(Null(), '00')

        # boolean
        obj_endec(Boolean(True), '11')
        obj_endec(Boolean(False), '10')

        # unsigned
        obj_endec(Unsigned(0), '2100')
        obj_endec(Unsigned(1), '2101')
        obj_endec(Unsigned(127), '217F')
        obj_endec(Unsigned(128), '2180')

        # integer
        obj_endec(Integer(0), '3100')
        obj_endec(Integer(1), '3101')
        obj_endec(Integer(-1), '31FF')
        obj_endec(Integer(128), '320080')
        obj_endec(Integer(-128), '3180')

        # real
        obj_endec(Real(0), '4400000000')
        obj_endec(Real(1), '443F800000')
        obj_endec(Real(-1), '44BF800000')
        obj_endec(Real(73.5), '4442930000')

        # double
        obj_endec(Double(0), '55080000000000000000')
        obj_endec(Double(1), '55083FF0000000000000')
        obj_endec(Double(-1), '5508BFF0000000000000')
        obj_endec(Double(73.5), '55084052600000000000')

        # octet string
        obj_endec(OctetString(xtob('')), '60')
        obj_endec(OctetString(xtob('01')), '6101')
        obj_endec(OctetString(xtob('0102')), '620102')
        obj_endec(OctetString(xtob('010203040506')), '6506010203040506')

        # character string
        obj_endec(CharacterString(''), '7100')
        obj_endec(CharacterString('a'), '720061')
        obj_endec(CharacterString('abcde'), '7506006162636465')

        # bit string
        obj_endec(BitString([]), '8100')
        obj_endec(BitString([0]), '820700')
        obj_endec(BitString([1]), '820780')
        obj_endec(BitString([1, 1, 1, 1, 1]), '8203F8')
        obj_endec(BitString([1] * 10), '8306FFC0')

        # enumerated
        obj_endec(Enumerated(0), '9100')
        obj_endec(Enumerated(1), '9101')
        obj_endec(Enumerated(127), '917F')
        obj_endec(Enumerated(128), '9180')

        # date
        obj_endec(Date((1,2,3,4)), 'A401020304')
        obj_endec(Date((255,2,3,4)), 'A4FF020304')
        obj_endec(Date((1,255,3,4)), 'A401FF0304')
        obj_endec(Date((1,2,255,4)), 'A40102FF04')
        obj_endec(Date((1,2,3,255)), 'A4010203FF')

        # time
        obj_endec(Time((1,2,3,4)), 'B401020304')
        obj_endec(Time((255,2,3,4)), 'B4FF020304')
        obj_endec(Time((1,255,3,4)), 'B401FF0304')
        obj_endec(Time((1,2,255,4)), 'B40102FF04')
        obj_endec(Time((1,2,3,255)), 'B4010203FF')

        # object identifier
        obj_endec(ObjectIdentifier(0,0), 'C400000000')
        obj_endec(ObjectIdentifier(1,0), 'C400400000')
        obj_endec(ObjectIdentifier(0,2), 'C400000002')
        obj_endec(ObjectIdentifier(3,4), 'C400C00004')


@bacpypes_debugging
class TestContextTag(unittest.TestCase):

    def test_context_tag(self):
        if _debug: TestContextTag._debug("test_context_tag")

        # test context tag construction
        tag = ContextTag(0, xtob(''))
        with self.assertRaises(ValueError):
            tag = ContextTag()

        # test encoding and decoding
        context_endec(0, '', '08')
        context_endec(1, '01', '1901')
        context_endec(2, '0102', '2A0102')
        context_endec(3, '010203', '3B010203')
        context_endec(14, '010203', 'EB010203')
        context_endec(15, '010203', 'FB0F010203')

@bacpypes_debugging
class TestOpeningTag(unittest.TestCase):

    def test_opening_tag(self):
        if _debug: TestOpeningTag._debug("test_opening_tag")

        # test opening tag construction
        tag = OpeningTag(0)
        with self.assertRaises(TypeError):
            tag = OpeningTag()

        # test encoding, and decoding
        opening_endec(0, '0E')
        opening_endec(1, '1E')
        opening_endec(2, '2E')
        opening_endec(3, '3E')
        opening_endec(14, 'EE')
        opening_endec(15, 'FE0F')
        opening_endec(254, 'FEFE')


@bacpypes_debugging
class TestClosingTag(unittest.TestCase):

    def test_closing_tag(self):
        if _debug: TestClosingTag._debug("test_closing_tag")

        # test closing tag construction
        tag = ClosingTag(0)
        with self.assertRaises(TypeError):
            tag = ClosingTag()

        # test encoding, and decoding
        closing_endec(0, '0F')
        closing_endec(1, '1F')
        closing_endec(2, '2F')
        closing_endec(3, '3F')
        closing_endec(14, 'EF')
        closing_endec(15, 'FF0F')
        closing_endec(254, 'FFFE')


@bacpypes_debugging
class TestTagList(unittest.TestCase):

    def test_tag_list(self):
        if _debug: TestTagList._debug("test_tag_list")

        # test tag list construction
        tag_list = TagList()
        tag_list = TagList([])

    def test_peek(self):
        if _debug: TestTagList._debug("test_peek")

        tag0 = IntegerTag(0)
        taglist = TagList([tag0])

        # peek at the first tag
        assert tag0 == taglist.Peek()

        # pop of the front
        tag1 = taglist.Pop()
        assert taglist.tagList == []

        # push it back on the front
        taglist.push(tag1)
        assert taglist.tagList == [tag1]

    def test_get_context(self):
        """Test extracting specific context encoded content.
        """
        if _debug: TestTagList._debug("test_get_context")

        tag_list_data = [
            ContextTag(0, xtob('00')),
            ContextTag(1, xtob('01')),
            OpeningTag(2),
            IntegerTag(3),
            OpeningTag(0),
            IntegerTag(4),
            ClosingTag(0),
            ClosingTag(2),
        ]
        taglist = TagList(tag_list_data)

        # known to be a simple context encoded element
        context_0 = taglist.get_context(0)
        if _debug: TestTagList._debug("    - context_0: %r", context_0)
        assert context_0 == tag_list_data[0]

        # known to be a simple context encoded list of element(s)
        context_2 = taglist.get_context(2)
        if _debug: TestTagList._debug("    - context_2: %r", context_2)
        assert context_2.tagList == tag_list_data[3:7]

        # known missing context
        context_3 = taglist.get_context(3)
        if _debug: TestTagList._debug("    - context_3: %r", context_3)
        assert taglist.get_context(3) is None

    def test_endec_0(self):
        """Test empty tag list encoding and decoding.
        """
        if _debug: TestTagList._debug("test_endec_0")

        taglist = TagList([])

        data = PDUData()
        taglist.encode(data)
        assert data.pduData == xtob('')

        taglist = TagList()
        taglist.decode(data)
        assert taglist.tagList == []

    def test_endec_1(self):
        """Test short tag list encoding and decoding, application tags.
        """
        if _debug: TestTagList._debug("test_endec_1")

        tag0 = IntegerTag(0x00)
        tag1 = IntegerTag(0x01)
        taglist = TagList([tag0, tag1])

        data = PDUData()
        taglist.encode(data)
        assert data.pduData == xtob('31003101')

        taglist = TagList()
        taglist.decode(data)
        assert taglist.tagList == [tag0, tag1]

    def test_endec_2(self):
        """Test short tag list encoding and decoding, context tags.
        """
        if _debug: TestTagList._debug("test_endec_2")

        tag0 = ContextTag(0, xtob('00'))
        tag1 = ContextTag(1, xtob('01'))
        taglist = TagList([tag0, tag1])

        data = PDUData()
        taglist.encode(data)
        assert data.pduData == xtob('09001901')

        taglist = TagList()
        taglist.decode(data)
        assert taglist.tagList == [tag0, tag1]

    def test_endec_3(self):
        """Test bracketed application tagged integer encoding and decoding."""
        if _debug: TestTagList._debug("test_endec_2")

        tag0 = OpeningTag(0)
        tag1 = IntegerTag(0x0102)
        tag2 = ClosingTag(0)
        taglist = TagList([tag0, tag1, tag2])

        data = PDUData()
        taglist.encode(data)
        assert data.pduData == xtob('0E3201020F')

        taglist = TagList()
        taglist.decode(data)
        assert taglist.tagList == [tag0, tag1, tag2]