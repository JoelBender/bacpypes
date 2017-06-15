#!/usr/bin/python

"""
Primitive Data
"""

import sys
import struct
import time
import re

from .debugging import ModuleLogger, btox

from .errors import DecodingError, InvalidTag, InvalidParameterDatatype
from .pdu import PDUData

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Tag
#

class Tag(object):

    applicationTagClass     = 0
    contextTagClass         = 1
    openingTagClass         = 2
    closingTagClass         = 3

    nullAppTag              = 0
    booleanAppTag           = 1
    unsignedAppTag          = 2
    integerAppTag           = 3
    realAppTag              = 4
    doubleAppTag            = 5
    octetStringAppTag       = 6
    characterStringAppTag   = 7
    bitStringAppTag         = 8
    enumeratedAppTag        = 9
    dateAppTag              = 10
    timeAppTag              = 11
    objectIdentifierAppTag  = 12
    reservedAppTag13        = 13
    reservedAppTag14        = 14
    reservedAppTag15        = 15

    _app_tag_name = \
        [ 'null', 'boolean', 'unsigned', 'integer'
        , 'real', 'double', 'octetString', 'characterString'
        , 'bitString', 'enumerated', 'date', 'time'
        , 'objectIdentifier', 'reserved13', 'reserved14', 'reserved15'
        ]
    _app_tag_class = [] # defined later

    def __init__(self, *args):
        self.tagClass = None
        self.tagNumber = None
        self.tagLVT = None
        self.tagData = None

        if args:
            if (len(args) == 1) and isinstance(args[0], PDUData):
                self.decode(args[0])
            elif (len(args) >= 2):
                self.set(*args)
            else:
                raise ValueError("invalid Tag ctor arguments")

    def set(self, tclass, tnum, tlvt=0, tdata=b''):
        """set the values of the tag."""
        if isinstance(tdata, bytearray):
            tdata = bytes(tdata)
        elif not isinstance(tdata, bytes):
            raise TypeError("tag data must be bytes or bytearray")

        self.tagClass = tclass
        self.tagNumber = tnum
        self.tagLVT = tlvt
        self.tagData = tdata

    def set_app_data(self, tnum, tdata):
        """set the values of the tag."""
        if isinstance(tdata, bytearray):
            tdata = bytes(tdata)
        elif not isinstance(tdata, bytes):
            raise TypeError("tag data must be bytes or bytearray")

        self.tagClass = Tag.applicationTagClass
        self.tagNumber = tnum
        self.tagLVT = len(tdata)
        self.tagData = tdata

    def encode(self, pdu):
        """Encode a tag on the end of the PDU."""
        # check for special encoding
        if (self.tagClass == Tag.contextTagClass):
            data = 0x08
        elif (self.tagClass == Tag.openingTagClass):
            data = 0x0E
        elif (self.tagClass == Tag.closingTagClass):
            data = 0x0F
        else:
            data = 0x00

        # encode the tag number part
        if (self.tagNumber < 15):
            data += (self.tagNumber << 4)
        else:
            data += 0xF0

        # encode the length/value/type part
        if (self.tagLVT < 5):
            data += self.tagLVT
        else:
            data += 0x05

        # save this and the extended tag value
        pdu.put( data )
        if (self.tagNumber >= 15):
            pdu.put(self.tagNumber)

        # really short lengths are already done
        if (self.tagLVT >= 5):
            if (self.tagLVT <= 253):
                pdu.put( self.tagLVT )
            elif (self.tagLVT <= 65535):
                pdu.put( 254 )
                pdu.put_short( self.tagLVT )
            else:
                pdu.put( 255 )
                pdu.put_long( self.tagLVT )

        # now put the data
        pdu.put_data(self.tagData)

    def decode(self, pdu):
        """Decode a tag from the PDU."""
        try:
            tag = pdu.get()

            # extract the type
            self.tagClass = (tag >> 3) & 0x01

            # extract the tag number
            self.tagNumber = (tag >> 4)
            if (self.tagNumber == 0x0F):
                self.tagNumber = pdu.get()

            # extract the length
            self.tagLVT = tag & 0x07
            if (self.tagLVT == 5):
                self.tagLVT = pdu.get()
                if (self.tagLVT == 254):
                    self.tagLVT = pdu.get_short()
                elif (self.tagLVT == 255):
                    self.tagLVT = pdu.get_long()
            elif (self.tagLVT == 6):
                self.tagClass = Tag.openingTagClass
                self.tagLVT = 0
            elif (self.tagLVT == 7):
                self.tagClass = Tag.closingTagClass
                self.tagLVT = 0

            # application tagged boolean has no more data
            if (self.tagClass == Tag.applicationTagClass) and (self.tagNumber == Tag.booleanAppTag):
                # tagLVT contains value
                self.tagData = b''
            else:
                # tagLVT contains length
                self.tagData = pdu.get_data(self.tagLVT)
        except DecodingError:
            raise InvalidTag("invalid tag encoding")

    def app_to_context(self, context):
        """Return a context encoded tag."""
        if self.tagClass != Tag.applicationTagClass:
            raise ValueError("application tag required")

        # application tagged boolean now has data
        if (self.tagNumber == Tag.booleanAppTag):
            return ContextTag(context, bytearray([self.tagLVT]))
        else:
            return ContextTag(context, self.tagData)

    def context_to_app(self, dataType):
        """Return an application encoded tag."""
        if self.tagClass != Tag.contextTagClass:
            raise ValueError("context tag required")

        # context booleans have value in data
        if (dataType == Tag.booleanAppTag):
            return Tag(Tag.applicationTagClass, Tag.booleanAppTag, struct.unpack('B', self.tagData)[0], b'')
        else:
            return ApplicationTag(dataType, self.tagData)

    def app_to_object(self):
        """Return the application object encoded by the tag."""
        if self.tagClass != Tag.applicationTagClass:
            raise ValueError("application tag required")

        # get the class to build
        klass = self._app_tag_class[self.tagNumber]
        if not klass:
            return None

        # build an object, tell it to decode this tag, and return it
        return klass(self)

    def __repr__(self):
        sname = self.__module__ + '.' + self.__class__.__name__
        try:
            if self.tagClass == Tag.openingTagClass:
                desc = "(open(%d))" % (self.tagNumber,)
            elif self.tagClass == Tag.closingTagClass:
                desc = "(close(%d))" % (self.tagNumber,)
            elif self.tagClass == Tag.contextTagClass:
                desc = "(context(%d))" % (self.tagNumber,)
            elif self.tagClass == Tag.applicationTagClass:
                desc = "(%s)" % (self._app_tag_name[self.tagNumber],)
            else:
                raise ValueError("invalid tag class")
        except:
            desc = "(?)"

        return '<' + sname + desc + ' instance at 0x%08x' % (id(self),) + '>'

    def __eq__(self, tag):
        return (self.tagClass == tag.tagClass) \
            and (self.tagNumber == tag.tagNumber) \
            and (self.tagLVT == tag.tagLVT) \
            and (self.tagData == tag.tagData)

    def __ne__(self,arg):
        return not self.__eq__(arg)

    def debug_contents(self, indent=1, file=sys.stdout, _ids=None):
        # object reference first
        file.write("%s%r\n" % ("    " * indent, self))
        indent += 1

        # tag class
        msg = "%stagClass = %s " % ("    " * indent, self.tagClass)
        if self.tagClass == Tag.applicationTagClass: msg += 'application'
        elif self.tagClass == Tag.contextTagClass: msg += 'context'
        elif self.tagClass == Tag.openingTagClass: msg += 'opening'
        elif self.tagClass == Tag.closingTagClass: msg += 'closing'
        else: msg += "?"
        file.write(msg + "\n")

        # tag number
        msg = "%stagNumber = %d " % ("    " * indent, self.tagNumber)
        if self.tagClass == Tag.applicationTagClass:
            try:
                msg += self._app_tag_name[self.tagNumber]
            except:
                msg += '?'
        file.write(msg + "\n")

        # length, value, type
        file.write("%stagLVT = %s\n" % ("    " * indent, self.tagLVT))

        # data
        file.write("%stagData = '%s'\n" % ("    " * indent, btox(self.tagData,'.')))

#
#   ApplicationTag
#

class ApplicationTag(Tag):

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], PDUData):
            Tag.__init__(self, args[0])
            if self.tagClass != Tag.applicationTagClass:
                raise InvalidTag("application tag not decoded")
        elif len(args) == 2:
            tnum, tdata = args
            Tag.__init__(self, Tag.applicationTagClass, tnum, len(tdata), tdata)
        else:
            raise ValueError("ApplicationTag ctor requires a type and data or PDUData")

#
#   ContextTag
#

class ContextTag(Tag):

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], PDUData):
            Tag.__init__(self, args[0])
            if self.tagClass != Tag.contextTagClass:
                raise InvalidTag("context tag not decoded")
        elif len(args) == 2:
            tnum, tdata = args
            Tag.__init__(self, Tag.contextTagClass, tnum, len(tdata), tdata)
        else:
            raise ValueError("ContextTag ctor requires a type and data or PDUData")

#
#   OpeningTag
#

class OpeningTag(Tag):

    def __init__(self, context):
        if isinstance(context, PDUData):
            Tag.__init__(self, context)
            if self.tagClass != Tag.openingTagClass:
                raise InvalidTag("opening tag not decoded")
        elif isinstance(context, int):
            Tag.__init__(self, Tag.openingTagClass, context)
        else:
            raise TypeError("OpeningTag ctor requires an integer or PDUData")

#
#   ClosingTag
#

class ClosingTag(Tag):

    def __init__(self, context):
        if isinstance(context, PDUData):
            Tag.__init__(self, context)
            if self.tagClass != Tag.closingTagClass:
                raise InvalidTag("closing tag not decoded")
        elif isinstance(context, int):
            Tag.__init__(self, Tag.closingTagClass, context)
        else:
            raise TypeError("ClosingTag ctor requires an integer or PDUData")

#
#   TagList
#

class TagList(object):

    def __init__(self, arg=None):
        self.tagList = []

        if isinstance(arg, list):
            self.tagList = arg
        elif isinstance(arg, TagList):
            self.tagList = arg.tagList[:]
        elif isinstance(arg, PDUData):
            self.decode(arg)

    def append(self, tag):
        self.tagList.append(tag)

    def extend(self, taglist):
        self.tagList.extend(taglist)

    def __getitem__(self, item):
        return self.tagList[item]

    def __len__(self):
        return len(self.tagList)

    def Peek(self):
        """Return the tag at the front of the list."""
        if self.tagList:
            tag = self.tagList[0]
        else:
            tag = None

        return tag

    def push(self, tag):
        """Return a tag back to the front of the list."""
        self.tagList = [tag] + self.tagList

    def Pop(self):
        """Remove the tag from the front of the list and return it."""
        if self.tagList:
            tag = self.tagList[0]
            del self.tagList[0]
        else:
            tag = None

        return tag

    def get_context(self, context):
        """Return a tag or a list of tags context encoded."""
        # forward pass
        i = 0
        while i < len(self.tagList):
            tag = self.tagList[i]

            # skip application stuff
            if tag.tagClass == Tag.applicationTagClass:
                pass

            # check for context encoded atomic value
            elif tag.tagClass == Tag.contextTagClass:
                if tag.tagNumber == context:
                    return tag

            # check for context encoded group
            elif tag.tagClass == Tag.openingTagClass:
                keeper = tag.tagNumber == context
                rslt = []
                i += 1
                lvl = 0
                while i < len(self.tagList):
                    tag = self.tagList[i]
                    if tag.tagClass == Tag.openingTagClass:
                        lvl += 1
                    elif tag.tagClass == Tag.closingTagClass:
                        lvl -= 1
                        if lvl < 0: break

                    rslt.append(tag)
                    i += 1

                # make sure everything balances
                if lvl >= 0:
                    raise InvalidTag("mismatched open/close tags")

                # get everything we need?
                if keeper:
                    return TagList(rslt)
            else:
                raise InvalidTag("unexpected tag")

            # try the next tag
            i += 1

        # nothing found
        return None

    def encode(self, pdu):
        """encode the tag list into a PDU."""
        for tag in self.tagList:
            tag.encode(pdu)

    def decode(self, pdu):
        """decode the tags from a PDU."""
        while pdu.pduData:
            self.tagList.append( Tag(pdu) )

    def debug_contents(self, indent=1, file=sys.stdout, _ids=None):
        for tag in self.tagList:
            tag.debug_contents(indent+1, file, _ids)

#
#   Atomic
#

class Atomic(object):

    _app_tag = None

    def __cmp__(self, other):
        # hoop jump it
        if not isinstance(other, self.__class__):
            other = self.__class__(other)

        # now compare the values
        if (self.value < other.value):
            return -1
        elif (self.value > other.value):
            return 1
        else:
            return 0

    @classmethod
    def coerce(cls, arg):
        """Given an arg, return the appropriate value given the class."""
        try:
            return cls(arg).value
        except (ValueError, TypeError):
            raise InvalidParameterDatatype("%s coerce error" % (cls.__name__,))

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        raise NotImplementedError("call on a derived class of Atomic")

#
#   Null
#

class Null(Atomic):

    _app_tag = Tag.nullAppTag

    def __init__(self, arg=None):
        self.value = ()

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, tuple):
            if len(arg) != 0:
                raise ValueError("empty tuple required")
        elif isinstance(arg, Null):
            pass
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        tag.set_app_data(Tag.nullAppTag, b'')

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.nullAppTag):
            raise InvalidTag("null application tag required")
        if len(tag.tagData) != 0:
            raise InvalidTag("invalid tag length")

        self.value = ()

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return arg is None

    def __str__(self):
        return "Null"

#
#   Boolean
#

class Boolean(Atomic):

    _app_tag = Tag.booleanAppTag

    def __init__(self, arg=None):
        self.value = False

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, bool):
            self.value = arg
        elif isinstance(arg, Boolean):
            self.value = arg.value
        elif str(arg) == 'True' or str(arg) == 'true':
            self.value = True
        elif str(arg) == 'False' or str(arg) == 'false':
            self.value = False
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        tag.set(Tag.applicationTagClass, Tag.booleanAppTag, int(self.value), b'')

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.booleanAppTag):
            raise InvalidTag("boolean application tag required")
        if (tag.tagLVT > 1):
            raise InvalidTag("invalid tag value")

        # get the data
        self.value = bool(tag.tagLVT)

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, bool)

    def __str__(self):
        return "Boolean(%s)" % (str(self.value), )

#
#   Unsigned
#

class Unsigned(Atomic):

    _app_tag = Tag.unsignedAppTag

    def __init__(self,arg = None):
        self.value = 0L

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, int):
            if (arg < 0):
                raise ValueError("unsigned integer required")
            self.value = long(arg)
        elif isinstance(arg, long):
            if (arg < 0):
                raise ValueError("unsigned integer required")
            self.value = arg
        elif isinstance(arg, Unsigned):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # rip apart the number
        data = bytearray(struct.pack('>L', self.value))

        # reduce the value to the smallest number of octets
        while (len(data) > 1) and (data[0] == 0):
            del data[0]

        # encode the tag
        tag.set_app_data(Tag.unsignedAppTag, data)

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.unsignedAppTag):
            raise InvalidTag("unsigned application tag required")
        if len(tag.tagData) == 0:
            raise InvalidTag("invalid tag length")

        # get the data
        rslt = 0L
        for c in tag.tagData:
            rslt = (rslt << 8) + ord(c)

        # save the result
        self.value = rslt

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, (int, long)) and (arg >= 0)

    def __str__(self):
        return "Unsigned(%s)" % (self.value, )

#
#   Integer
#

class Integer(Atomic):

    _app_tag = Tag.integerAppTag

    def __init__(self,arg = None):
        self.value = 0

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, int):
            self.value = arg
        elif isinstance(arg, long):
            self.value = arg
        elif isinstance(arg, Integer):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # rip apart the number
        data = bytearray(struct.pack('>I', self.value & 0xFFFFFFFF))

        # reduce the value to the smallest number of bytes, be
        # careful about sign extension
        if self.value < 0:
            while (len(data) > 1):
                if (data[0] != 255):
                    break
                if (data[1] < 128):
                    break
                del data[0]
        else:
            while (len(data) > 1):
                if (data[0] != 0):
                    break
                if (data[1] >= 128):
                    break
                del data[0]

        # encode the tag
        tag.set_app_data(Tag.integerAppTag, data)

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.integerAppTag):
            raise InvalidTag("integer application tag required")
        if len(tag.tagData) == 0:
            raise InvalidTag("invalid tag length")

        # byte array easier to deal with
        tag_data = bytearray(tag.tagData)

        # get the data
        rslt = tag_data[0]
        if (rslt & 0x80) != 0:
            rslt = (-1 << 8) | rslt
        for c in tag_data[1:]:
            rslt = (rslt << 8) | c

        # save the result
        self.value = rslt

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, (int, long))

    def __str__(self):
        return "Integer(%s)" % (self.value, )

#
#   Real
#

class Real(Atomic):

    _app_tag = Tag.realAppTag

    def __init__(self, arg=None):
        self.value = 0.0

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, float):
            self.value = arg
        elif isinstance(arg, (int, long)):
            self.value = float(arg)
        elif isinstance(arg, Real):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.realAppTag, struct.pack('>f',self.value))

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.realAppTag):
            raise InvalidTag("real application tag required")
        if len(tag.tagData) != 4:
            raise InvalidTag("invalid tag length")

        # extract the data
        self.value = struct.unpack('>f',tag.tagData)[0]

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, float)

    def __str__(self):
        return "Real(%g)" % (self.value,)

#
#   Double
#

class Double(Atomic):

    _app_tag = Tag.doubleAppTag

    def __init__(self,arg = None):
        self.value = 0.0

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, float):
            self.value = arg
        elif isinstance(arg, (int, long)):
            self.value = float(arg)
        elif isinstance(arg, Double):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.doubleAppTag, struct.pack('>d',self.value))

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.doubleAppTag):
            raise InvalidTag("double application tag required")
        if len(tag.tagData) != 8:
            raise InvalidTag("invalid tag length")

        # extract the data
        self.value = struct.unpack('>d',tag.tagData)[0]

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, float)

    def __str__(self):
        return "Double(%g)" % (self.value,)

#
#   OctetString
#

class OctetString(Atomic):

    _app_tag = Tag.octetStringAppTag

    def __init__(self, arg=None):
        self.value = ''

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, (bytes, bytearray)):
            self.value = bytes(arg)
        elif isinstance(arg, OctetString):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.octetStringAppTag, self.value)

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.octetStringAppTag):
            raise InvalidTag("octet string application tag required")

        self.value = tag.tagData

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, (bytes, bytearray))

    def __str__(self):
        return "OctetString(X'" + btox(self.value) + "')"

#
#   CharacterString
#

class CharacterString(Atomic):

    _app_tag = Tag.characterStringAppTag

    def __init__(self, arg=None):
        self.value = ''
        self.strEncoding = 0
        self.strValue = ''

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, (str, unicode)):
            self.strValue = self.value = str(arg)
        elif isinstance(arg, CharacterString):
            self.value = arg.value
            self.strEncoding = arg.strEncoding
            self.strValue = arg.strValue
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.characterStringAppTag, chr(self.strEncoding)+self.strValue)

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.characterStringAppTag):
            raise InvalidTag("character string application tag required")
        if len(tag.tagData) == 0:
            raise InvalidTag("invalid tag length")

        # byte array easier to deal with
        tag_data = bytearray(tag.tagData)

        # extract the data
        self.strEncoding = tag_data[0]
        self.strValue = tag_data[1:]

        # normalize the value
        if (self.strEncoding == 0):
            udata = self.strValue.decode('utf_8')
            self.value = str(udata.encode('ascii', 'backslashreplace'))
        elif (self.strEncoding == 3):
            udata = self.strValue.decode('utf_32be')
            self.value = str(udata.encode('ascii', 'backslashreplace'))
        elif (self.strEncoding == 4):
            udata = self.strValue.decode('utf_16be')
            self.value = str(udata.encode('ascii', 'backslashreplace'))
        elif (self.strEncoding == 5):
            udata = self.strValue.decode('latin_1')
            self.value = str(udata.encode('ascii', 'backslashreplace'))
        else:
            self.value = '### unknown encoding: %d ###' % (self.strEncoding,)

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, (str, unicode))

    def __str__(self):
        return "CharacterString(%d,X'%s')" % (self.strEncoding, btox(self.strValue))

#
#   BitString
#

class BitString(Atomic):

    _app_tag = Tag.bitStringAppTag
    bitNames = {}
    bitLen = 0

    def __init__(self, arg = None):
        self.value = [0] * self.bitLen

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, list):
            allInts = allStrings = True
            for elem in arg:
                allInts = allInts and ((elem == 0) or (elem == 1))
                allStrings = allStrings and elem in self.bitNames

            if allInts:
                self.value = arg
            elif allStrings:
                for bit in arg:
                    bit = self.bitNames[bit]
                    if (bit < 0) or (bit > len(self.value)):
                        raise IndexError("constructor element out of range")
                    self.value[bit] = 1
            else:
                raise TypeError("invalid constructor list element(s)")
        elif isinstance(arg,BitString):
            self.value = arg.value[:]
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, tag):
        # compute the unused bits to fill out the string
        _, used = divmod(len(self.value), 8)
        unused = used and (8 - used) or 0

        # start with the number of unused bits
        data = bytearray([unused])

        # build and append each packed octet
        bits = self.value + [0] * unused
        for i in range(0,len(bits),8):
            x = 0
            for j in range(0,8):
                x |= bits[i + j] << (7 - j)
            data.append(x)

        # encode the tag
        tag.set_app_data(Tag.bitStringAppTag, data)

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.bitStringAppTag):
            raise InvalidTag("bit string application tag required")
        if len(tag.tagData) == 0:
            raise InvalidTag("invalid tag length")

        tag_data = bytearray(tag.tagData)

        # extract the number of unused bits
        unused = tag_data[0]

        # extract the data
        data = []
        for x in tag_data[1:]:
            for i in range(8):
                if (x & (1 << (7 - i))) != 0:
                    data.append( 1 )
                else:
                    data.append( 0 )

        # trim off the unused bits
        if unused:
            self.value = data[:-unused]
        else:
            self.value = data

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        if isinstance(arg, list):
            allInts = allStrings = True
            for elem in arg:
                allInts = allInts and ((elem == 0) or (elem == 1))
                allStrings = allStrings and elem in cls.bitNames

            if allInts or allStrings:
                return True
        return False

    def __str__(self):
        # flip the bit names
        bitNames = {}
        for key, value in self.bitNames.items():
            bitNames[value] = key

        # build a list of values and/or names
        valueList = []
        for value, index in zip(self.value,range(len(self.value))):
            if index in bitNames:
                if value:
                    valueList.append(bitNames[index])
                else:
                    valueList.append('!' + bitNames[index])
            else:
                valueList.append(str(value))

        # bundle it together
        return "BitString(" + ','.join(valueList) + ")"

    def __getitem__(self, bit):
        if isinstance(bit, int):
            pass
        elif isinstance(bit, str):
            if bit not in self.bitNames:
                raise IndexError("unknown bit name '%s'" % (bit,))

            bit = self.bitNames[bit]
        else:
            raise TypeError("bit index must be an integer or bit name")

        if (bit < 0) or (bit > len(self.value)):
            raise IndexError("list index out of range")

        return self.value[bit]

    def __setitem__(self, bit, value):
        if isinstance(bit, int):
            pass
        elif isinstance(bit, str):
            if bit not in self.bitNames:
                raise IndexError("unknown bit name '%s'" % (bit,))

            bit = self.bitNames[bit]
        else:
            raise TypeError("bit index must be an integer or bit name")

        if (bit < 0) or (bit > len(self.value)):
            raise IndexError("list index out of range")

        # funny cast to a bit
        self.value[bit] = value and 1 or 0

#
#   Enumerated
#

class Enumerated(Atomic):

    _app_tag = Tag.enumeratedAppTag

    enumerations = {}
    _xlate_table = {}

    def __init__(self, arg=None):
        self.value = 0L

        # see if the class has a translate table
        if '_xlate_table' not in self.__class__.__dict__:
            expand_enumerations(self.__class__)

        # initialize the object
        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, (int, long)):
            if (arg < 0):
                raise ValueError("unsigned integer required")

            # convert it to a string if you can
            self.value = self._xlate_table.get(arg, arg)

        elif isinstance(arg, str):
            if arg not in self._xlate_table:
                raise ValueError("undefined enumeration '%s'" % (arg,))
            self.value = arg
        elif isinstance(arg, Enumerated):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def __getitem__(self, item):
        return self._xlate_table.get(item)

    def get_long(self):
        if isinstance(self.value, (int, long)):
            return self.value
        elif isinstance(self.value, str):
            return long(self._xlate_table[self.value])
        else:
            raise TypeError("%s is an invalid enumeration value datatype" % (type(self.value),))

    def keylist(self):
        """Return a list of names in order by value."""
        items = self.enumerations.items()
        items.sort(lambda a, b: cmp(a[1], b[1]))

        # last item has highest value
        rslt = [None] * (items[-1][1] + 1)

        # map the values
        for key, value in items:
            rslt[value] = key

        # return the result
        return rslt

    def __cmp__(self, other):
        """Special function to make sure comparisons are done in enumeration
        order, not alphabetic order."""
        # hoop jump it
        if not isinstance(other, self.__class__):
            other = self.__class__(other)

        # get the numeric version
        a = self.get_long()
        b = other.get_long()

        # now compare the values
        if (a < b):
            return -1
        elif (a > b):
            return 1
        else:
            return 0

    def encode(self, tag):
        if isinstance(self.value, int):
            value = long(self.value)
        elif isinstance(self.value, long):
            value = self.value
        elif isinstance(self.value, str):
            value = self._xlate_table[self.value]
        else:
            raise TypeError("%s is an invalid enumeration value datatype" % (type(self.value),))

        # rip apart the number
        data = bytearray(struct.pack('>L', value))

        # reduce the value to the smallest number of octets
        while (len(data) > 1) and (data[0] == 0):
            del data[0]

        # encode the tag
        tag.set_app_data(Tag.enumeratedAppTag, data)

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.enumeratedAppTag):
            raise InvalidTag("enumerated application tag required")
        if len(tag.tagData) == 0:
            raise InvalidTag("invalid tag length")

        # get the data
        rslt = 0L
        for c in tag.tagData:
            rslt = (rslt << 8) + ord(c)

        # translate to a string if possible
        rslt = self._xlate_table.get(rslt, rslt)

        # save the result
        self.value = rslt

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class.  If the string
        value is wrong for the enumeration, the encoding will fail.
        """
        return (isinstance(arg, (int, long)) and (arg >= 0)) or \
            isinstance(arg, str)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.value)

#
#   expand_enumerations
#

def expand_enumerations(klass):
    # build a value dictionary
    xlateTable = {}

    for c in klass.__mro__:
        enumerations = getattr(c, 'enumerations', {})
        if enumerations:
            for name, value in enumerations.items():
                # save the results
                xlateTable[name] = value
                xlateTable[value] = name

                # save the name in the class
                setattr(klass, name, value)

    # save the dictionary in the class
    setattr(klass, '_xlate_table', xlateTable)


#
#   Date
#

_mm = r'(?P<month>0?[1-9]|1[0-4]|odd|even|255|[*])'
_dd = r'(?P<day>[0-3]?\d|last|odd|even|255|[*])'
_yy = r'(?P<year>\d{2}|255|[*])'
_yyyy = r'(?P<year>\d{4}|255|[*])'
_dow = r'(?P<dow>[1-7]|mon|tue|wed|thu|fri|sat|sun|255|[*])'

_special_mon = {'*': 255, 'odd': 13, 'even': 14, None: 255}
_special_mon_inv = {255: '*', 13: 'odd', 14: 'even'}

_special_day = {'*': 255, 'last': 32, 'odd': 33, 'even': 34, None: 255}
_special_day_inv = {255: '*', 32: 'last', 33: 'odd', 34: 'even'}

_special_dow = {'*': 255, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 7}
_special_dow_inv = {255: '*', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat', 7: 'sun'}


def _merge(*args):
    """Create a composite pattern and compile it."""
    return re.compile(r'^' + r'[/-]'.join(args) + r'(?:\s+' + _dow + ')?$')


# make a list of compiled patterns
_date_patterns = [
    _merge(_yyyy, _mm, _dd),
    _merge(_mm, _dd, _yyyy),
    _merge(_dd, _mm, _yyyy),
    _merge(_yy, _mm, _dd),
    _merge(_mm, _dd, _yy),
    _merge(_dd, _mm, _yy),
    ]


class Date(Atomic):

    _app_tag = Tag.dateAppTag

    def __init__(self, arg=None, year=255, month=255, day=255, day_of_week=255):
        self.value = (year, month, day, day_of_week)

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, tuple):
            self.value = arg
        elif isinstance(arg, str):
            # lower case everything
            arg = arg.lower()

            # make a list of the contents from matching patterns
            matches = []
            for p in _date_patterns:
                m = p.match(arg)
                if m:
                    matches.append(m.groupdict())

            # try to find a good one
            match = None
            if not matches:
                raise ValueError("unmatched")

            # if there is only one, success
            if len(matches) == 1:
                match = matches[0]
            else:
                # check to see if they really are the same
                for a, b in zip(matches[:-1],matches[1:]):
                    if a != b:
                        raise ValueError("ambiguous")
                        break
                else:
                    match = matches[0]

            # extract the year and normalize
            year = match['year']
            if (year == '*') or (not year):
                year = 255
            else:
                year = int(year)
                if (year == 255):
                    pass
                elif year < 35:
                    year += 2000
                elif year < 100:
                    year += 1900
                elif year < 1900:
                    raise ValueError("invalid year")

            # extract the month and normalize
            month = match['month']
            if month in _special_mon:
                month = _special_mon[month]
            else:
                month = int(month)
                if (month == 255):
                    pass
                elif (month == 0) or (month > 14):
                    raise ValueError("invalid month")

            # extract the day and normalize
            day = match['day']
            if day in _special_day:
                day = _special_day[day]
            else:
                day = int(day)
                if (day == 255):
                    pass
                elif (day == 0) or (day > 34):
                    raise ValueError("invalid day")

            # extract the day-of-week and normalize
            day_of_week = match['dow']
            if day_of_week in _special_dow:
                day_of_week = _special_dow[day_of_week]
            elif not day_of_week:
                pass
            else:
                day_of_week = int(day_of_week)
                if (day_of_week == 255):
                    pass
                elif day_of_week > 7:
                    raise ValueError("invalid day of week")

            # year becomes the correct octet
            if year != 255:
                year -= 1900

            # save the value
            self.value = (year, month, day, day_of_week)

            # calculate the day of the week
            if not day_of_week:
                self.CalcDayOfWeek()

        elif isinstance(arg, Date):
            self.value = arg.value

        else:
            raise TypeError("invalid constructor datatype")

    def CalcDayOfWeek(self):
        """Calculate the correct day of the week."""
        # rip apart the value
        year, month, day, day_of_week = self.value

        # assume the worst
        day_of_week = 255

        # check for special values
        if year == 255:
            pass
        elif month in _special_mon_inv:
            pass
        elif day in _special_day_inv:
            pass
        else:
            try:
                today = time.mktime( (year + 1900, month, day, 0, 0, 0, 0, 0, -1) )
                day_of_week = time.gmtime(today)[6] + 1
            except OverflowError:
                pass

        # put it back together
        self.value = (year, month, day, day_of_week)

    def now(self):
        tup = time.localtime()
        self.value = (tup[0]-1900, tup[1], tup[2], tup[6] + 1)
        return self

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.dateAppTag, bytearray(self.value))

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.dateAppTag):
            raise InvalidTag("date application tag required")
        if len(tag.tagData) != 4:
            raise InvalidTag("invalid tag length")

        # rip apart the data
        self.value = tuple(ord(c) for c in tag.tagData)

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, tuple) and (len(arg) == 4)

    def __str__(self):
        """String representation of the date."""
        # rip it apart
        year, month, day, day_of_week = self.value

        if year == 255:
            year = "*"
        else:
            year = str(year + 1900)

        month = _special_mon_inv.get(month, str(month))
        day = _special_day_inv.get(day, str(day))
        day_of_week = _special_dow_inv.get(day_of_week, str(day_of_week))

        return "%s(%s-%s-%s %s)" % (self.__class__.__name__, year, month, day, day_of_week)


#
#   Time
#

class Time(Atomic):

    _app_tag = Tag.timeAppTag
    _time_regex = re.compile("^([*]|[0-9]+)[:]([*]|[0-9]+)(?:[:]([*]|[0-9]+)(?:[.]([*]|[0-9]+))?)?$")

    DONT_CARE = 255

    def __init__(self, arg=None, hour=255, minute=255, second=255, hundredth=255):
        # put it together
        self.value = (hour, minute, second, hundredth)

        if arg is None:
            pass
        elif isinstance(arg,Tag):
            self.decode(arg)
        elif isinstance(arg, tuple):
            self.value = arg
        elif isinstance(arg, str):
            tup_match = Time._time_regex.match(arg)
            if not tup_match:
                raise ValueError("invalid time pattern")

            tup_list = []
            tup_items = list(tup_match.groups())
            for s in tup_items:
                if s == '*':
                    tup_list.append(255)
                elif s is None:
                    if '*' in tup_items:
                        tup_list.append(255)
                    else:
                        tup_list.append(0)
                else:
                    tup_list.append(int(s))

            # fix the hundredths if necessary
            if (tup_list[3] > 0) and (tup_list[3] < 10):
                tup_list[3] = tup_list[3] * 10

            self.value = tuple(tup_list)
        elif isinstance(arg, Time):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")

    def now(self):
        now = time.time()
        tup = time.localtime(now)

        self.value = (tup[3], tup[4], tup[5], int((now - int(now)) * 100))

        return self

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.timeAppTag, bytearray(self.value))

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.timeAppTag):
            raise InvalidTag("time application tag required")
        if len(tag.tagData) != 4:
            raise InvalidTag("invalid tag length")

        # rip apart the data
        self.value = tuple(ord(c) for c in tag.tagData)

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, tuple) and (len(arg) == 4)

    def __str__(self):
        # rip it apart
        hour, minute, second, hundredth = self.value

        rslt = "Time("
        if hour == 255:
            rslt += "*:"
        else:
            rslt += "%02d:" % (hour,)
        if minute == 255:
            rslt += "*:"
        else:
            rslt += "%02d:" % (minute,)
        if second == 255:
            rslt += "*."
        else:
            rslt += "%02d." % (second,)
        if hundredth == 255:
            rslt += "*)"
        else:
            rslt += "%02d)" % (hundredth,)

        return rslt

#
#   ObjectType
#

class ObjectType(Enumerated):
    vendor_range = (128, 1023)
    enumerations = \
        { 'accessDoor':30
        , 'accessPoint':33
        , 'accessRights':34
        , 'accessUser':35
        , 'accessZone':36
        , 'accumulator':23
        , 'analogInput':0
        , 'analogOutput':1
        , 'analogValue':2
        , 'averaging':18
        , 'binaryInput':3
        , 'binaryOutput':4
        , 'binaryValue':5
        , 'bitstringValue':39
        , 'calendar':6
        , 'characterstringValue':40
        , 'command':7
        , 'credentialDataInput':37
        , 'datePatternValue':41
        , 'dateValue':42
        , 'datetimePatternValue':43
        , 'datetimeValue':44
        , 'device':8
        , 'eventEnrollment':9
        , 'eventLog':25
        , 'file':10
        , 'globalGroup':26
        , 'group':11
        , 'integerValue':45
        , 'largeAnalogValue':46
        , 'lifeSafetyPoint':21
        , 'lifeSafetyZone':22
        , 'loadControl':28
        , 'loop':12
        , 'multiStateInput':13
        , 'multiStateOutput':14
        , 'multiStateValue':19
        , 'networkSecurity':38
        , 'notificationClass':15
        , 'octetstringValue':47
        , 'positiveIntegerValue':48
        , 'program':16
        , 'pulseConverter':24
        , 'schedule':17
        , 'structuredView':29
        , 'timePatternValue':49
        , 'timeValue':50
        , 'trendLog':20
        , 'trendLogMultiple':27
        }

expand_enumerations(ObjectType)

#
#   ObjectIdentifier
#

class ObjectIdentifier(Atomic):

    _app_tag = Tag.objectIdentifierAppTag
    objectTypeClass = ObjectType

    maximum_instance_number = 0x003FFFFF

    def __init__(self, *args):
        self.value = ('analogInput', 0)

        if len(args) == 0:
            pass
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, Tag):
                self.decode(arg)
            elif isinstance(arg, int):
                self.set_long(long(arg))
            elif isinstance(arg, long):
                self.set_long(arg)
            elif isinstance(arg, tuple):
                self.set_tuple(*arg)
            elif isinstance(arg, ObjectIdentifier):
                self.value = arg.value
            else:
                raise TypeError("invalid constructor datatype")
        elif len(args) == 2:
            self.set_tuple(*args)
        else:
            raise ValueError("invalid constructor parameters")

    def set_tuple(self, objType, objInstance):
        # allow a type name as well as an integer
        if isinstance(objType, int):
            # try and make it pretty
            objType = self.objectTypeClass._xlate_table.get(objType, objType)
        elif isinstance(objType, long):
            objType = self.objectTypeClass._xlate_table.get(objType, int(objType))
        elif isinstance(objType, str):
            # make sure the type is known
            if objType not in self.objectTypeClass._xlate_table:
                raise ValueError("unrecognized object type '%s'" % (objType,))
        else:
            raise TypeError("invalid datatype for objType: %r, %r" % (type(objType), objType))

        # check for valid instance number
        if (objInstance < 0) or (objInstance > ObjectIdentifier.maximum_instance_number):
            raise ValueError("instance number out of range")

        # pack the components together
        self.value = (objType, objInstance)

    def get_tuple(self):
        """Return the unsigned integer tuple of the identifier."""
        objType, objInstance = self.value

        if isinstance(objType, int):
            pass
        elif isinstance(objType, long):
            objType = int(objType)
        elif isinstance(objType, str):
            # turn it back into an integer
            objType = self.objectTypeClass()[objType]
        else:
            raise TypeError("invalid datatype for objType")

        # pack the components together
        return (objType, objInstance)

    def set_long(self, value):
        # suck out the type
        objType = (value >> 22) & 0x03FF

        # try and make it pretty
        objType = self.objectTypeClass()[objType] or objType

        # suck out the instance
        objInstance = value & 0x003FFFFF

        # save the result
        self.value = (objType, objInstance)

    def get_long(self):
        """Return the unsigned integer representation of the identifier."""
        objType, objInstance = self.get_tuple()

        # pack the components together
        return ((objType << 22) + objInstance)

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.objectIdentifierAppTag, struct.pack('>L', self.get_long()))

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.objectIdentifierAppTag):
            raise InvalidTag("object identifier application tag required")
        if len(tag.tagData) != 4:
            raise InvalidTag("invalid tag length")

        # extract the data
        self.set_long(struct.unpack('>L',tag.tagData)[0])

    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return isinstance(arg, tuple) and (len(arg) == 2)

    def __str__(self):
        # rip it apart
        objType, objInstance = self.value

        if isinstance(objType, str):
            typestr = objType
        elif objType < 0:
            typestr = "Bad %d" % (objType,)
        elif objType in self.objectTypeClass._xlate_table:
            typestr = self.objectTypeClass._xlate_table[objType]
        elif (objType < 128):
            typestr = "Reserved %d" % (objType,)
        else:
            typestr = "Vendor %d" % (objType,)
        return "ObjectIdentifier(%s,%d)" % (typestr, objInstance)

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        """Special function to make sure comparisons are done in enumeration
        order, not alphabetic order."""
        # hoop jump it
        if not isinstance(other, self.__class__):
            other = self.__class__(other)

        # get the numeric version
        a = self.get_long()
        b = other.get_long()

        # now compare the values
        return (a < b)

#
#   Application Tag Classes
#
#   This list is set in the Tag class so that the app_to_object
#   function can return one of the appliction datatypes.  It
#   can't be provided in the Tag class definition because the
#   classes aren't defined yet.
#

Tag._app_tag_class = \
    [ Null, Boolean, Unsigned, Integer
    , Real, Double, OctetString, CharacterString
    , BitString, Enumerated, Date, Time
    , ObjectIdentifier, None, None, None
    ]

