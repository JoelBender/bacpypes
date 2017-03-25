#!/usr/bin/python

"""
Application Layer Protocol Data Units
"""

from .errors import DecodingError, TooManyArguments
from .debugging import ModuleLogger, DebugContents, bacpypes_debugging

from .pdu import PCI, PDUData
from .primitivedata import Boolean, CharacterString, Enumerated, Integer, \
    ObjectIdentifier, ObjectType, OctetString, Real, TagList, Unsigned, \
    expand_enumerations
from .constructeddata import Any, Choice, Element, Sequence, SequenceOf
from .basetypes import ChannelValue, DateTime, DeviceAddress, ErrorType, \
    EventState, EventTransitionBits, EventType, LifeSafetyOperation, \
    NotificationParameters, NotifyType, ObjectPropertyReference, \
    PropertyIdentifier, PropertyReference, PropertyValue, RecipientProcess, \
    ResultFlags, Segmentation, TimeStamp, VTClass

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# a dictionary of message type values and classes
apdu_types = {}

def register_apdu_type(klass):
    apdu_types[klass.pduType] = klass

# a dictionary of confirmed request choices and classes
confirmed_request_types = {}

def register_confirmed_request_type(klass):
    confirmed_request_types[klass.serviceChoice] = klass

# a dictionary of complex ack choices and classes
complex_ack_types = {}

def register_complex_ack_type(klass):
    complex_ack_types[klass.serviceChoice] = klass

# a dictionary of unconfirmed request choices and classes
unconfirmed_request_types = {}

def register_unconfirmed_request_type(klass):
    unconfirmed_request_types[klass.serviceChoice] = klass

# a dictionary of unconfirmed request choices and classes
error_types = {}

def register_error_type(klass):
    error_types[klass.serviceChoice] = klass

#
#   encode_max_segments_accepted/decode_max_segments_accepted
#

def encode_max_segments_accepted(arg):
    """Encode the maximum number of segments the device will accept, Section
    20.1.2.4"""
    w = 0
    while (arg and not arg & 1):
        w += 1
        arg = (arg >> 1)
    return w

def decode_max_segments_accepted(arg):
    """Decode the maximum number of segments the device will accept, Section
    20.1.2.4"""
    return arg and (1 << arg) or None

#
#   encode_max_apdu_length_accepted/decode_max_apdu_length_accepted
#

_max_apdu_response_encoding = [50, 128, 206, 480, 1024, 1476, None, None,
    None, None, None, None, None, None, None, None]

def encode_max_apdu_length_accepted(arg):
    """Return the encoding of the highest encodable value less than the
    value of the arg."""
    for i in range(5, -1, -1):
        if (arg >= _max_apdu_response_encoding[i]):
            return i

    raise ValueError("invalid max APDU length accepted: {0}".format(arg))

def decode_max_apdu_length_accepted(arg):
    v = _max_apdu_response_encoding[arg]
    if not v:
        raise ValueError("invalid max APDU length accepted: {0}".format(arg))

    return v

#
#   APCI
#

class APCI(PCI, DebugContents):

    _debug_contents = ('apduType', 'apduSeg', 'apduMor', 'apduSA', 'apduSrv'
        , 'apduNak', 'apduSeq', 'apduWin', 'apduMaxSegs', 'apduMaxResp'
        , 'apduService', 'apduInvokeID', 'apduAbortRejectReason'
        )

    def __init__(self, *args, **kwargs):
        if _debug: APCI._debug("__init__ %r %r", args, kwargs)
        super(APCI, self).__init__(*args, **kwargs)

        self.apduType = None
        self.apduSeg = None                 # segmented
        self.apduMor = None                 # more follows
        self.apduSA = None                  # segmented response accepted
        self.apduSrv = None                 # sent by server
        self.apduNak = None                 # negative acknowledgement
        self.apduSeq = None                 # sequence number
        self.apduWin = None                 # actual/proposed window size
        self.apduMaxSegs = None             # maximum segments accepted (decoded)
        self.apduMaxResp = None             # max response accepted (decoded)
        self.apduService = None             #
        self.apduInvokeID = None            #
        self.apduAbortRejectReason = None   #

    def update(self, apci):
        PCI.update(self, apci)
        self.apduType = apci.apduType
        self.apduSeg = apci.apduSeg
        self.apduMor = apci.apduMor
        self.apduSA = apci.apduSA
        self.apduSrv = apci.apduSrv
        self.apduNak = apci.apduNak
        self.apduSeq = apci.apduSeq
        self.apduWin = apci.apduWin
        self.apduMaxSegs = apci.apduMaxSegs
        self.apduMaxResp = apci.apduMaxResp
        self.apduService = apci.apduService
        self.apduInvokeID = apci.apduInvokeID
        self.apduAbortRejectReason = apci.apduAbortRejectReason

    def __repr__(self):
        """Return a string representation of the PDU."""
        # start with the class name
        sname = self.__module__ + '.' + self.__class__.__name__

        # expand the type if possible
        stype = apdu_types.get(self.apduType, None)
        if stype:
            stype = stype.__name__
        else:
            stype = '?'

        # add the invoke ID if it has one
        if self.apduInvokeID is not None:
            stype += ',' + str(self.apduInvokeID)

        # put it together
        return "<%s(%s) instance at %s>" % (sname, stype, hex(id(self)))

    def encode(self, pdu):
        """encode the contents of the APCI into the PDU."""
        if _debug: APCI._debug("encode %r", pdu)

        PCI.update(pdu, self)

        if (self.apduType == ConfirmedRequestPDU.pduType):
            # PDU type
            buff = self.apduType << 4
            if self.apduSeg:
                buff += 0x08
            if self.apduMor:
                buff += 0x04
            if self.apduSA:
                buff += 0x02
            pdu.put(buff)
            pdu.put((encode_max_segments_accepted(self.apduMaxSegs) << 4) + encode_max_apdu_length_accepted(self.apduMaxResp))
            pdu.put(self.apduInvokeID)
            if self.apduSeg:
                pdu.put(self.apduSeq)
                pdu.put(self.apduWin)
            pdu.put(self.apduService)

        elif (self.apduType == UnconfirmedRequestPDU.pduType):
            pdu.put(self.apduType << 4)
            pdu.put(self.apduService)

        elif (self.apduType == SimpleAckPDU.pduType):
            pdu.put(self.apduType << 4)
            pdu.put(self.apduInvokeID)
            pdu.put(self.apduService)

        elif (self.apduType == ComplexAckPDU.pduType):
            # PDU type
            buff = self.apduType << 4
            if self.apduSeg:
                buff += 0x08
            if self.apduMor:
                buff += 0x04
            pdu.put(buff)
            pdu.put(self.apduInvokeID)
            if self.apduSeg:
                pdu.put(self.apduSeq)
                pdu.put(self.apduWin)
            pdu.put(self.apduService)

        elif (self.apduType == SegmentAckPDU.pduType):
            # PDU type
            buff = self.apduType << 4
            if self.apduNak:
                buff += 0x02
            if self.apduSrv:
                buff += 0x01
            pdu.put(buff)
            pdu.put(self.apduInvokeID)
            pdu.put(self.apduSeq)
            pdu.put(self.apduWin)

        elif (self.apduType == ErrorPDU.pduType):
            pdu.put(self.apduType << 4)
            pdu.put(self.apduInvokeID)
            pdu.put(self.apduService)

        elif (self.apduType == RejectPDU.pduType):
            pdu.put(self.apduType << 4)
            pdu.put(self.apduInvokeID)
            pdu.put(self.apduAbortRejectReason)

        elif (self.apduType == AbortPDU.pduType):
            # PDU type
            buff = self.apduType << 4
            if self.apduSrv:
                buff += 0x01
            pdu.put(buff)
            pdu.put(self.apduInvokeID)
            pdu.put(self.apduAbortRejectReason)

        else:
            raise ValueError("invalid APCI.apduType")

    def decode(self, pdu):
        """decode the contents of the PDU into the APCI."""
        if _debug: APCI._debug("decode %r", pdu)

        PCI.update(self, pdu)

        # decode the first octet
        buff = pdu.get()

        # decode the APCI type
        self.apduType = (buff >> 4) & 0x0F

        if (self.apduType == ConfirmedRequestPDU.pduType):
            self.apduSeg = ((buff & 0x08) != 0)
            self.apduMor = ((buff & 0x04) != 0)
            self.apduSA  = ((buff & 0x02) != 0)
            buff = pdu.get()
            self.apduMaxSegs = decode_max_segments_accepted( (buff >> 4) & 0x07 )
            self.apduMaxResp = decode_max_apdu_length_accepted( buff & 0x0F )
            self.apduInvokeID = pdu.get()
            if self.apduSeg:
                self.apduSeq = pdu.get()
                self.apduWin = pdu.get()
            self.apduService = pdu.get()
            self.pduData = pdu.pduData

        elif (self.apduType == UnconfirmedRequestPDU.pduType):
            self.apduService = pdu.get()
            self.pduData = pdu.pduData

        elif (self.apduType == SimpleAckPDU.pduType):
            self.apduInvokeID = pdu.get()
            self.apduService = pdu.get()

        elif (self.apduType == ComplexAckPDU.pduType):
            self.apduSeg = ((buff & 0x08) != 0)
            self.apduMor = ((buff & 0x04) != 0)
            self.apduInvokeID = pdu.get()
            if self.apduSeg:
                self.apduSeq = pdu.get()
                self.apduWin = pdu.get()
            self.apduService = pdu.get()
            self.pduData = pdu.pduData

        elif (self.apduType == SegmentAckPDU.pduType):
            self.apduNak = ((buff & 0x02) != 0)
            self.apduSrv = ((buff & 0x01) != 0)
            self.apduInvokeID = pdu.get()
            self.apduSeq = pdu.get()
            self.apduWin = pdu.get()

        elif (self.apduType == ErrorPDU.pduType):
            self.apduInvokeID = pdu.get()
            self.apduService = pdu.get()
            self.pduData = pdu.pduData

        elif (self.apduType == RejectPDU.pduType):
            self.apduInvokeID = pdu.get()
            self.apduAbortRejectReason = pdu.get()

        elif (self.apduType == AbortPDU.pduType):
            self.apduSrv = ((buff & 0x01) != 0)
            self.apduInvokeID = pdu.get()
            self.apduAbortRejectReason = pdu.get()
            self.pduData = pdu.pduData

        else:
            raise DecodingError("invalid APDU type")

    def apci_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: APCI._debug("apci_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # copy the source and destination to make it easier to search
        if self.pduSource:
            use_dict.__setitem__('source', str(self.pduSource))
        if self.pduDestination:
            use_dict.__setitem__('destination', str(self.pduDestination))

        # loop through the elements
        for attr in APCI._debug_contents:
            value = getattr(self, attr, None)
            if value is None:
                continue

            if attr == 'apduType':
                mapped_value = apdu_types[self.apduType].__name__
            elif attr == 'apduService':
                if self.apduType in (ConfirmedRequestPDU.pduType, SimpleAckPDU.pduType, ComplexAckPDU.pduType):
                    mapped_value = confirmed_request_types[self.apduService].__name__
                elif (self.apduType == UnconfirmedRequestPDU.pduType):
                    mapped_value = unconfirmed_request_types[self.apduService].__name__
                elif (self.apduType == ErrorPDU.pduType):
                    mapped_value = error_types[self.apduService].__name__
            else:
                mapped_value = value

            # save the mapped value
            use_dict.__setitem__(attr, mapped_value)

        # return what we built/updated
        return use_dict

bacpypes_debugging(APCI)

#
#   APDU
#

class APDU(APCI, PDUData):

    def __init__(self, *args, **kwargs):
        if _debug: APDU._debug("__init__ %r %r", args, kwargs)
        super(APDU, self).__init__(*args, **kwargs)

    def encode(self, pdu):
        if _debug: APCI._debug("encode %s", str(pdu))
        APCI.encode(self, pdu)
        pdu.put_data(self.pduData)

    def decode(self, pdu):
        if _debug: APCI._debug("decode %s", str(pdu))
        APCI.decode(self, pdu)
        self.pduData = pdu.get_data(len(pdu.pduData))

    def apdu_contents(self, use_dict=None, as_class=dict):
        return PDUData.pdudata_contents(self, use_dict=use_dict, as_class=as_class)

    def dict_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: APDU._debug("dict_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # call the parent classes
        self.apci_contents(use_dict=use_dict, as_class=as_class)
        self.apdu_contents(use_dict=use_dict, as_class=as_class)

        # return what we built/updated
        return use_dict

bacpypes_debugging(APDU)

#------------------------------

#
#   _APDU
#
#   This class masks the encode() and decode() functions of the APDU
#   so that derived classes use the update function to copy the contents
#   between PDU's.  Otherwise the APCI content would be decoded twice.
#

class _APDU(APDU):

    def encode(self, pdu):
        APCI.update(pdu, self)
        pdu.put_data(self.pduData)

    def decode(self, pdu):
        APCI.update(self, pdu)
        self.pduData = pdu.get_data(len(pdu.pduData))

    def set_context(self, context):
        self.pduUserData = context.pduUserData
        self.pduDestination = context.pduSource
        self.pduExpectingReply = 0
        self.pduNetworkPriority = context.pduNetworkPriority
        self.apduInvokeID = context.apduInvokeID

    def __repr__(self):
        """Return a string representation of the APDU."""
        # start with the class name
        sname = self.__module__ + '.' + self.__class__.__name__

        # the type is the service
        stype = str(self.apduService)

        # add the invoke ID if it has one
        if self.apduInvokeID is not None:
            stype += ',' + str(self.apduInvokeID)

        # put it together
        return "<%s(%s) instance at %s>" % (sname, stype, hex(id(self)))

#
#   ConfirmedRequestPDU
#

class ConfirmedRequestPDU(_APDU):
    pduType = 0

    def __init__(self, choice=None, *args, **kwargs):
        if _debug: ConfirmedRequestPDU._debug("__init__ %r %r %r", choice, args, kwargs)
        super(ConfirmedRequestPDU, self).__init__(*args, **kwargs)

        self.apduType = ConfirmedRequestPDU.pduType
        self.apduService = choice
        self.pduExpectingReply = 1

bacpypes_debugging(ConfirmedRequestPDU)
register_apdu_type(ConfirmedRequestPDU)

#
#   UnconfirmedRequestPDU
#

class UnconfirmedRequestPDU(_APDU):
    pduType = 1

    def __init__(self, choice=None, *args, **kwargs):
        if _debug: UnconfirmedRequestPDU._debug("__init__ %r %r %r", choice, args, kwargs)
        super(UnconfirmedRequestPDU, self).__init__(*args, **kwargs)

        self.apduType = UnconfirmedRequestPDU.pduType
        self.apduService = choice

bacpypes_debugging(UnconfirmedRequestPDU)
register_apdu_type(UnconfirmedRequestPDU)

#
#   SimpleAckPDU
#

class SimpleAckPDU(_APDU):
    pduType = 2

    def __init__(self, choice=None, invokeID=None, context=None, *args, **kwargs):
        if _debug: SimpleAckPDU._debug("__init__ %r %r %r %r %r", choice, invokeID, context, args, kwargs)
        super(SimpleAckPDU, self).__init__(*args, **kwargs)

        self.apduType = SimpleAckPDU.pduType
        self.apduService = choice
        self.apduInvokeID = invokeID

        # use the context to fill in most of the fields
        if context is not None:
            self.apduService = context.apduService
            self.set_context(context)

bacpypes_debugging(SimpleAckPDU)
register_apdu_type(SimpleAckPDU)

#
#   ComplexAckPDU
#

class ComplexAckPDU(_APDU):
    pduType = 3

    def __init__(self, choice=None, invokeID=None, context=None, *args, **kwargs):
        if _debug: ComplexAckPDU._debug("__init__ %r %r %r %r %r", choice, invokeID, context, args, kwargs)
        super(ComplexAckPDU, self).__init__(*args, **kwargs)

        self.apduType = ComplexAckPDU.pduType
        self.apduService = choice
        self.apduInvokeID = invokeID

        # use the context to fill in most of the fields
        if context is not None:
            self.apduService = context.apduService
            self.set_context(context)

bacpypes_debugging(ComplexAckPDU)
register_apdu_type(ComplexAckPDU)

#
#   SegmentAckPDU
#

class SegmentAckPDU(_APDU):
    pduType = 4

    def __init__(self, nak=None, srv=None, invokeID=None, sequenceNumber=None, windowSize=None, *args, **kwargs):
        if _debug: SegmentAckPDU._debug("__init__ %r %r %r %r %r %r %r", nak, srv, invokeID, sequenceNumber, windowSize, args, kwargs)
        super(SegmentAckPDU, self).__init__(*args, **kwargs)

        self.apduType = SegmentAckPDU.pduType
        self.apduNak = nak
        self.apduSrv = srv
        self.apduInvokeID = invokeID
        self.apduSeq = sequenceNumber
        self.apduWin = windowSize

bacpypes_debugging(SegmentAckPDU)
register_apdu_type(SegmentAckPDU)

#
#   ErrorPDU
#

class ErrorPDU(_APDU):
    pduType = 5

    def __init__(self, choice=None, invokeID=None, context=None, *args, **kwargs):
        if _debug: ErrorPDU._debug("__init__ %r %r %r %r %r", choice, invokeID, context, args, kwargs)
        super(ErrorPDU, self).__init__(*args, **kwargs)

        self.apduType = ErrorPDU.pduType
        self.apduService = choice
        self.apduInvokeID = invokeID

        # use the context to fill in most of the fields
        if context is not None:
            self.apduService = context.apduService
            self.set_context(context)

bacpypes_debugging(ErrorPDU)
register_apdu_type(ErrorPDU)

#
#   RejectPDU
#

class RejectReason(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'other':0
        , 'bufferOverflow':1
        , 'inconsistentParameters':2
        , 'invalidParameterDatatype':3
        , 'invalidTag':4
        , 'missingRequiredParameter':5
        , 'parameterOutOfRange':6
        , 'tooManyArguments':7
        , 'undefinedEnumeration':8
        , 'unrecognizedService':9
        }

expand_enumerations(RejectReason)

class RejectPDU(_APDU):
    pduType = 6

    def __init__(self, invokeID=None, reason=None, context=None, *args, **kwargs):
        if _debug: RejectPDU._debug("__init__ %r %r %r %r %r", invokeID, reason, context, args, kwargs)
        super(RejectPDU, self).__init__(*args, **kwargs)

        self.apduType = RejectPDU.pduType
        self.apduInvokeID = invokeID
        if isinstance(reason, str):
            reason = RejectReason(reason).get_long()
        self.apduAbortRejectReason = reason

        # use the context to fill in most of the fields
        if context is not None:
            self.set_context(context)

bacpypes_debugging(RejectPDU)
register_apdu_type(RejectPDU)

#
#   AbortPDU
#

class AbortReason(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'other':0
        , 'bufferOverflow':1
        , 'invalidApduInThisState':2
        , 'preemptedByHigherPriorityTask':3  #wtm corrected spelling
        , 'segmentationNotSupported':4
        , 'securityError':5
        , 'insufficientSecurity':6
        , 'windowSizeOutOfRange':7
        , 'applicationExceededReplyTime':8
        , 'outOfResources':9
        , 'tsmTimeout':10
        , 'apduTooLong':11
        # 64..255 are available for vendor codes
        , 'serverTimeout':64
        , 'noResponse':65
        }

expand_enumerations(AbortReason)

class AbortPDU(_APDU):
    pduType = 7

    def __init__(self, srv=None, invokeID=None, reason=None, context=None, *args, **kwargs):
        if _debug: AbortPDU._debug("__init__ %r %r %r %r %r %r", srv, invokeID, reason, context, args, kwargs)
        super(AbortPDU, self).__init__(*args, **kwargs)

        self.apduType = AbortPDU.pduType
        self.apduSrv = srv
        self.apduInvokeID = invokeID
        if isinstance(reason, str):
            reason = AbortReason(reason).get_long()
        self.apduAbortRejectReason = reason

        # use the context to fill in most of the fields
        if context is not None:
            self.set_context(context)

    def __str__(self):
        try:
            reason = AbortReason._xlate_table[self.apduAbortRejectReason]
        except:
            reason = str(self.apduAbortRejectReason) + '?'
        return reason

bacpypes_debugging(AbortPDU)
register_apdu_type(AbortPDU)

#------------------------------

#
#   APCISequence
#

class APCISequence(APCI, Sequence):

    def __init__(self, *args, **kwargs):
        if _debug: APCISequence._debug("__init__ %r %r", args, kwargs)
        super(APCISequence, self).__init__(*args, **kwargs)

        # start with an empty tag list
        self._tag_list = None

    def encode(self, apdu):
        if _debug: APCISequence._debug("encode %r", apdu)

        # copy the header fields
        apdu.update(self)

        # create a tag list
        self._tag_list = TagList()
        Sequence.encode(self, self._tag_list)

        # encode the tag list
        self._tag_list.encode(apdu)

    def decode(self, apdu):
        if _debug: APCISequence._debug("decode %r", apdu)

        # copy the header fields
        self.update(apdu)

        # create a tag list and decode the rest of the data
        self._tag_list = TagList()
        self._tag_list.decode(apdu)

        # pass the taglist to the Sequence for additional decoding
        Sequence.decode(self, self._tag_list)

        # trailing unmatched tags
        if self._tag_list:
            if _debug: APCISequence._debug("    - trailing unmatched tags")
            raise TooManyArguments()

    def apdu_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: APCISequence._debug("apdu_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # set the function based on the class name
        use_dict.__setitem__('function', self.__class__.__name__)

        # fill in from the sequence contents
        Sequence.dict_contents(self, use_dict=use_dict, as_class=as_class)

        # return what we built/updated
        return use_dict

bacpypes_debugging(APCISequence)

#
#   ConfirmedRequestSequence
#

class ConfirmedRequestSequence(APCISequence, ConfirmedRequestPDU):

    serviceChoice = None

    def __init__(self, *args, **kwargs):
        if _debug: ConfirmedRequestSequence._debug("__init__ %r %r", args, kwargs)
        super(ConfirmedRequestSequence, self).__init__(*args, **dict(choice=self.serviceChoice, **kwargs))

bacpypes_debugging(ConfirmedRequestSequence)

#
#   ComplexAckSequence
#

class ComplexAckSequence(APCISequence, ComplexAckPDU):

    serviceChoice = None

    def __init__(self, *args, **kwargs):
        if _debug: ComplexAckSequence._debug("__init__ %r %r", args, kwargs)
        super(ComplexAckSequence, self).__init__(*args, **dict(choice=self.serviceChoice, **kwargs))

bacpypes_debugging(ComplexAckSequence)

#
#   UnconfirmedRequestSequence
#

class UnconfirmedRequestSequence(APCISequence, UnconfirmedRequestPDU):

    serviceChoice = None

    def __init__(self, *args, **kwargs):
        if _debug: UnconfirmedRequestSequence._debug("__init__ %r %r", args, kwargs)
        super(UnconfirmedRequestSequence, self).__init__(*args, **dict(choice=self.serviceChoice, **kwargs))

bacpypes_debugging(UnconfirmedRequestSequence)

#
#   ErrorSequence
#

class ErrorSequence(APCISequence, ErrorPDU):

    serviceChoice = None

    def __init__(self, *args, **kwargs):
        if _debug: ErrorSequence._debug("__init__ %r %r", args, kwargs)
        super(ErrorSequence, self).__init__(*args, **dict(choice=self.serviceChoice, **kwargs))

bacpypes_debugging(ErrorSequence)

#------------------------------

class Error(ErrorSequence):
    sequenceElements = ErrorType.sequenceElements

    def __str__(self):
        return str(self.errorClass) + ": " + str(self.errorCode)

error_types[12] = Error
error_types[14] = Error

class ChangeListError(ErrorSequence):
    sequenceElements = \
        [ Element('errorType', ErrorType, 0)
        , Element('firstFailedElementNumber', Unsigned, 1)
        ]

    def __str__(self):
        return "change list error, first failed element number " + str(self.firstFailedElementNumber)

error_types[8] = ChangeListError
error_types[9] = ChangeListError

class CreateObjectError(ErrorSequence):
    sequenceElements = \
        [ Element('errorType', ErrorType, 0)
        , Element('firstFailedElementNumber', Unsigned, 1)
        ]

    def __str__(self):
        return "create object error, first failed element number " + str(self.firstFailedElementNumber)

error_types[10] = CreateObjectError

class ConfirmedPrivateTransferError(ErrorSequence):
    sequenceElements = \
        [ Element('errorType', ErrorType, 0)
        , Element('vendorID', Unsigned, 1)
        , Element('serviceNumber', Unsigned, 2)
        , Element('errorParameters', Any, 3, True)
        ]

error_types[18] = ConfirmedPrivateTransferError

class WritePropertyMultipleError(ErrorSequence):
    sequenceElements = \
        [ Element('errorType', ErrorType, 0)
        , Element('firstFailedWriteAttempt', ObjectPropertyReference, 1)
        ]

error_types[16] = WritePropertyMultipleError

class VTCloseError(ErrorSequence):
    sequenceElements = \
        [ Element('errorType', ErrorType, 0)
        , Element('listOfVTSessionIdentifiers', SequenceOf(Unsigned), 1, True)
        ]

error_types[22] = VTCloseError

#-----

class ReadPropertyRequest(ConfirmedRequestSequence):
    serviceChoice = 12
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        ]

register_confirmed_request_type(ReadPropertyRequest)

class ReadPropertyACK(ComplexAckSequence):
    serviceChoice = 12
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('propertyValue', Any, 3)
        ]

register_complex_ack_type(ReadPropertyACK)

#-----

class ReadAccessSpecification(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('listOfPropertyReferences', SequenceOf(PropertyReference), 1)
        ]

class ReadPropertyMultipleRequest(ConfirmedRequestSequence):
    serviceChoice = 14
    sequenceElements = \
        [ Element('listOfReadAccessSpecs', SequenceOf(ReadAccessSpecification))
        ]

register_confirmed_request_type(ReadPropertyMultipleRequest)

class ReadAccessResultElementChoice(Choice):
    choiceElements = \
        [ Element('propertyValue', Any, 4)
        , Element('propertyAccessError', ErrorType, 5)
        ]

class ReadAccessResultElement(Sequence):
    sequenceElements = \
        [ Element('propertyIdentifier', PropertyIdentifier, 2)
        , Element('propertyArrayIndex', Unsigned, 3, True)
        , Element('readResult', ReadAccessResultElementChoice)
        ]

class ReadAccessResult(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('listOfResults', SequenceOf(ReadAccessResultElement), 1)
        ]

class ReadPropertyMultipleACK(ComplexAckSequence):
    serviceChoice = 14
    sequenceElements = \
        [ Element('listOfReadAccessResults', SequenceOf(ReadAccessResult))
        ]

register_complex_ack_type(ReadPropertyMultipleACK)

#-----

class RangeByPosition(Sequence):
    sequenceElements = \
        [ Element('referenceIndex', Unsigned)
        , Element('count', Integer)
        ]

class RangeBySequenceNumber(Sequence):
    sequenceElements = \
        [ Element('referenceIndex', Unsigned)
        , Element('count', Integer)
        ]

class RangeByTime(Sequence):
    sequenceElements = \
        [ Element('referenceTime', DateTime)
        , Element('count', Integer)
        ]

class Range(Choice):
    choiceElements = \
        [ Element('byPosition', RangeByPosition, 3)
        , Element('bySequenceNumber', RangeBySequenceNumber, 6)
        , Element('byTime', RangeByTime, 7)
        ]

class ReadRangeRequest(ConfirmedRequestSequence):
    serviceChoice = 26
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('range', Range, optional=True)
        ]

register_confirmed_request_type(ReadRangeRequest)

class ReadRangeACK(ComplexAckSequence):
    serviceChoice = 26
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('resultFlags', ResultFlags, 3)
        , Element('itemCount', Unsigned, 4)
        , Element('itemData', SequenceOf(Any), 5)
        , Element('firstSequenceNumber', Unsigned, 6, True)
        ]

register_complex_ack_type(ReadRangeACK)

#-----

class WritePropertyRequest(ConfirmedRequestSequence):
    serviceChoice = 15
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('propertyValue', Any, 3)
        , Element('priority', Integer, 4, True)
        ]

register_confirmed_request_type(WritePropertyRequest)

#-----

class WriteAccessSpecification(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('listOfProperties', SequenceOf(PropertyValue), 1)
        ]

class WritePropertyMultipleRequest(ConfirmedRequestSequence):
    serviceChoice = 16
    sequenceElements = \
        [ Element('listOfWriteAccessSpecs', SequenceOf(WriteAccessSpecification))
        ]

register_confirmed_request_type(WritePropertyMultipleRequest)

#-----

class GroupChannelValue(Sequence):
    sequenceElements = \
        [ Element('channel', Unsigned, 0)
        , Element('overridingPriority', Unsigned, 1, True)
        , Element('value', ChannelValue)
        ]

class WriteGroupRequest(UnconfirmedRequestSequence):
    serviceChoice = 10
    sequenceElements = \
        [ Element('groupNumber', Unsigned, 0)
        , Element('writePriority', Unsigned, 1)
        , Element('changeList', SequenceOf(GroupChannelValue), 2)
        , Element('inhibitDelay', Boolean, 3, True)
        ]

register_unconfirmed_request_type(WriteGroupRequest)

#-----

class IAmRequest(UnconfirmedRequestSequence):
    serviceChoice = 0
    sequenceElements = \
        [ Element('iAmDeviceIdentifier', ObjectIdentifier)
        , Element('maxAPDULengthAccepted', Unsigned)
        , Element('segmentationSupported', Segmentation)
        , Element('vendorID', Unsigned)
        ]

register_unconfirmed_request_type(IAmRequest)

#-----

class IHaveRequest(UnconfirmedRequestSequence):
    serviceChoice = 1
    sequenceElements = \
        [ Element('deviceIdentifier', ObjectIdentifier)
        , Element('objectIdentifier', ObjectIdentifier)
        , Element('objectName', CharacterString)
        ]

register_unconfirmed_request_type(IHaveRequest)

#-----

class WhoHasLimits(Sequence):
    sequenceElements = \
        [ Element('deviceInstanceRangeLowLimit', Unsigned, 0)
        , Element('deviceInstanceRangeHighLimit', Unsigned, 1)
        ]

class WhoHasObject(Choice):
    choiceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 2)
        , Element('objectName', CharacterString, 3)
        ]

class WhoHasRequest(UnconfirmedRequestSequence):
    serviceChoice = 7
    sequenceElements = \
        [ Element('limits', WhoHasLimits, None, True)
        , Element('object', WhoHasObject)
        ]

register_unconfirmed_request_type(WhoHasRequest)

#-----

class WhoIsRequest(UnconfirmedRequestSequence):
    serviceChoice = 8
    sequenceElements = \
        [ Element('deviceInstanceRangeLowLimit', Unsigned, 0, True)
        , Element('deviceInstanceRangeHighLimit', Unsigned, 1, True)
        ]

register_unconfirmed_request_type(WhoIsRequest)

#-----

class EventNotificationParameters(Sequence):
    sequenceElements = \
        [ Element('processIdentifier', Unsigned, 0)
        , Element('initiatingDeviceIdentifier', ObjectIdentifier, 1)
        , Element('eventObjectIdentifier', ObjectIdentifier, 2)
        , Element('timeStamp', TimeStamp, 3)
        , Element('notificationClass', Unsigned, 4)
        , Element('priority', Unsigned, 5)
        , Element('eventType', EventType, 6)
        , Element('messageText', CharacterString, 7, True)
        , Element('notifyType', NotifyType, 8)
        , Element('ackRequired', Boolean, 9, True)
        , Element('fromState', EventState, 10, True)
        , Element('toState', EventState, 11)
        , Element('eventValues', NotificationParameters, 12, True)
        ]

class ConfirmedEventNotificationRequest(ConfirmedRequestSequence):
    serviceChoice = 2
    sequenceElements = EventNotificationParameters.sequenceElements

register_confirmed_request_type(ConfirmedEventNotificationRequest)

class UnconfirmedEventNotificationRequest(UnconfirmedRequestSequence):
    serviceChoice = 3
    sequenceElements = EventNotificationParameters.sequenceElements

register_unconfirmed_request_type(UnconfirmedEventNotificationRequest)

#-----

class COVNotificationParameters(Sequence):
    sequenceElements = \
        [ Element('subscriberProcessIdentifier', Unsigned, 0)
        , Element('initiatingDeviceIdentifier', ObjectIdentifier, 1)
        , Element('monitoredObjectIdentifier', ObjectIdentifier, 2)
        , Element('timeRemaining', Unsigned, 3)
        , Element('listOfValues', SequenceOf(PropertyValue), 4)
        ]

class ConfirmedCOVNotificationRequest(ConfirmedRequestSequence):
    serviceChoice = 1
    sequenceElements = COVNotificationParameters.sequenceElements

register_confirmed_request_type(ConfirmedCOVNotificationRequest)

class UnconfirmedCOVNotificationRequest(UnconfirmedRequestSequence):
    serviceChoice = 2
    sequenceElements = COVNotificationParameters.sequenceElements

register_unconfirmed_request_type(UnconfirmedCOVNotificationRequest)

#-----

class UnconfirmedPrivateTransferRequest(UnconfirmedRequestSequence):
    serviceChoice = 4
    sequenceElements = \
        [ Element('vendorID', Unsigned, 0)
        , Element('serviceNumber', Unsigned, 1)
        , Element('serviceParameters', Any, 2, True)
        ]

register_unconfirmed_request_type(UnconfirmedPrivateTransferRequest)

#-----

class UnconfirmedTextMessageRequestMessageClass(Choice):
    choiceElements = \
        [ Element('numeric', Unsigned, 0)
        , Element('character', CharacterString, 1)
        ]

class UnconfirmedTextMessageRequestMessagePriority(Enumerated):
    enumerations = \
        { 'normal':0
        , 'urgent':1
        }

class UnconfirmedTextMessageRequest(UnconfirmedRequestSequence):
    serviceChoice = 5
    sequenceElements = \
        [ Element('textMessageSourceDevice', ObjectIdentifier, 0)
        , Element('messageClass', UnconfirmedTextMessageRequestMessageClass, 1, True)
        , Element('messagePriority', UnconfirmedTextMessageRequestMessagePriority, 2)
        , Element('message', CharacterString, 3)
        ]

register_unconfirmed_request_type(UnconfirmedTextMessageRequest)

#-----

class TimeSynchronizationRequest(UnconfirmedRequestSequence):
    serviceChoice = 6
    sequenceElements = \
        [ Element('time', DateTime)
        ]

register_unconfirmed_request_type(TimeSynchronizationRequest)

#-----

class UTCTimeSynchronizationRequest(UnconfirmedRequestSequence):
    serviceChoice = 9
    sequenceElements = \
        [ Element('time', DateTime)
        ]

register_unconfirmed_request_type(UTCTimeSynchronizationRequest)

#-----

class AcknowledgeAlarmRequest(ConfirmedRequestSequence):
    serviceChoice = 0
    sequenceElements = \
        [ Element('acknowledgingProcessIdentifier', Unsigned, 0)
        , Element('eventObjectIdentifier', ObjectIdentifier, 1)
        , Element('eventStateAcknowledged', EventState, 2)
        , Element('timeStamp', TimeStamp, 3)
        , Element('acknowledgmentSource', CharacterString, 4)
        , Element('timeOfAcknowledgment', TimeStamp, 5)
        ]

register_confirmed_request_type(AcknowledgeAlarmRequest)

#-----

class GetAlarmSummaryRequest(ConfirmedRequestSequence):
    serviceChoice = 3
    sequenceElements = \
        [
        ]

register_confirmed_request_type(GetAlarmSummaryRequest)

class GetAlarmSummaryAlarmSummary(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier,)
        , Element('alarmState', EventState,)
        , Element('acknowledgedTransitions', EventTransitionBits)
        ]

class GetAlarmSummaryACK(ComplexAckSequence):
    serviceChoice = 3
    sequenceElements = \
        [ Element('listOfAlarmSummaries', SequenceOf(GetAlarmSummaryAlarmSummary))
        ]

register_complex_ack_type(GetAlarmSummaryACK)

#-----

class GetEnrollmentSummaryRequestAcknowledgmentFilterType(Enumerated):
    enumerations = \
        { 'all':0
        , 'acked':1
        , 'notAcked':2
        }

class GetEnrollmentSummaryRequestEventStateFilterType(Enumerated):
    enumerations = \
        { 'offnormal':0
        , 'fault':1
        , 'normal':2
        , 'all':3
        , 'active':4
        }

class GetEnrollmentSummaryRequestPriorityFilterType:
    sequenceElements = \
        [ Element('minPriority', Unsigned, 0)
        , Element('maxPriority', Unsigned, 1)
        ]

class GetEnrollmentSummaryRequest(ConfirmedRequestSequence):
    serviceChoice = 4
    sequenceElements = \
        [ Element('acknowledgmentFilter', GetEnrollmentSummaryRequestAcknowledgmentFilterType, 0)
        , Element('enrollmentFilter', RecipientProcess, 1, True)
        , Element('eventStateFilter', GetEnrollmentSummaryRequestEventStateFilterType, 2, True)
        , Element('eventTypeFilter', EventType, 3, True)
        , Element('priorityFilter', GetEnrollmentSummaryRequestPriorityFilterType, 4, True)
        , Element('notificationClassFilter', Unsigned, 5, True)
        ]

register_confirmed_request_type(GetEnrollmentSummaryRequest)

class GetEnrollmentSummaryEnrollmentSummary(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier)
        , Element('eventType', EventType)
        , Element('eventState', EventState)
        , Element('priority', Unsigned)
        , Element('notificationClass', Unsigned, optional=True)
        ]

class GetEnrollmentSummaryACK(ComplexAckSequence):
    serviceChoice = 4
    sequenceElements = \
        [ Element('listOfEnrollmentSummaries', SequenceOf(GetEnrollmentSummaryEnrollmentSummary))
        ]

register_complex_ack_type(GetEnrollmentSummaryACK)

#-----

class GetEventInformationRequest(ConfirmedRequestSequence):
    serviceChoice = 29
    sequenceElements = \
        [ Element('lastReceivedObjectIdentifier', ObjectIdentifier, 0, True)
        ]

register_confirmed_request_type(GetEventInformationRequest)

class GetEventInformationEventSummary(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('eventState', EventState, 1)
        , Element('acknowledgedTransitions', EventTransitionBits, 2)
        , Element('eventTimeStamps', SequenceOf(TimeStamp), 3)
        , Element('notifyType', NotifyType, 4)
        , Element('eventEnable', EventTransitionBits, 5)
        , Element('eventPriorities', SequenceOf(Unsigned), 6)
        ]

class GetEventInformationACK(ComplexAckSequence):
    serviceChoice = 29
    sequenceElements = \
        [ Element('listOfEventSummaries', SequenceOf(GetEventInformationEventSummary), 0)
        , Element('moreEvents', Boolean, 1)
        ]

register_complex_ack_type(GetEventInformationACK)

#-----

class LifeSafetyOperationRequest(ConfirmedRequestSequence):
    serviceChoice = 27
    sequenceElements = \
        [ Element('requestingProcessIdentifier', Unsigned, 0)
        , Element('requestingSource', CharacterString, 1)
        , Element('request', LifeSafetyOperation, 2)
        , Element('objectIdentifier', ObjectIdentifier, 3)
        ]

register_confirmed_request_type(LifeSafetyOperationRequest)

#-----

class SubscribeCOVRequest(ConfirmedRequestSequence):
    serviceChoice = 5
    sequenceElements = \
        [ Element('subscriberProcessIdentifier', Unsigned, 0)
        , Element('monitoredObjectIdentifier', ObjectIdentifier, 1)
        , Element('issueConfirmedNotifications', Boolean, 2, True)
        , Element('lifetime', Unsigned, 3, True)
        ]

register_confirmed_request_type(SubscribeCOVRequest)

#-----

class SubscribeCOVPropertyRequest(ConfirmedRequestSequence):
    serviceChoice = 28
    sequenceElements = \
        [ Element('subscriberProcessIdentifier', Unsigned, 0)
        , Element('monitoredObjectIdentifier', ObjectIdentifier, 1)
        , Element('issueConfirmedNotifications', Boolean, 2, True)
        , Element('lifetime', Unsigned, 3, True)
        , Element('monitoredPropertyIdentifier', PropertyReference, 4)
        , Element('covIncrement', Real, 5, True)
        ]

register_confirmed_request_type(SubscribeCOVPropertyRequest)

#-----

class AtomicReadFileRequestAccessMethodChoiceStreamAccess(Sequence):
    sequenceElements = \
        [ Element('fileStartPosition', Integer)
        , Element('requestedOctetCount', Unsigned)
        ]

class AtomicReadFileRequestAccessMethodChoiceRecordAccess(Sequence):
    sequenceElements = \
        [ Element('fileStartRecord', Integer)
        , Element('requestedRecordCount', Unsigned)
        ]

class AtomicReadFileRequestAccessMethodChoice(Choice):
    choiceElements = \
        [ Element('streamAccess', AtomicReadFileRequestAccessMethodChoiceStreamAccess, 0)
        , Element('recordAccess', AtomicReadFileRequestAccessMethodChoiceRecordAccess, 1)
        ]

class AtomicReadFileRequest(ConfirmedRequestSequence):
    serviceChoice = 6
    sequenceElements = \
        [ Element('fileIdentifier', ObjectIdentifier)
        , Element('accessMethod', AtomicReadFileRequestAccessMethodChoice)
        ]

register_confirmed_request_type(AtomicReadFileRequest)

class AtomicReadFileACKAccessMethodStreamAccess(Sequence):
    sequenceElements = \
        [ Element('fileStartPosition', Integer)
        , Element('fileData', OctetString)
        ]

class AtomicReadFileACKAccessMethodRecordAccess(Sequence):
    sequenceElements = \
        [ Element('fileStartRecord', Integer)
        , Element('returnedRecordCount', Unsigned)
        , Element('fileRecordData', SequenceOf(OctetString))
        ]

class AtomicReadFileACKAccessMethodChoice(Choice):
    choiceElements = \
        [ Element('streamAccess', AtomicReadFileACKAccessMethodStreamAccess, 0)
        , Element('recordAccess', AtomicReadFileACKAccessMethodRecordAccess, 1)
        ]

class AtomicReadFileACK(ComplexAckSequence):
    serviceChoice = 6
    sequenceElements = \
        [ Element('endOfFile', Boolean)
        , Element('accessMethod', AtomicReadFileACKAccessMethodChoice)
        ]

register_complex_ack_type(AtomicReadFileACK)

#-----

class AtomicWriteFileRequestAccessMethodChoiceStreamAccess(Sequence):
    sequenceElements = \
        [ Element('fileStartPosition', Integer)
        , Element('fileData', OctetString)
        ]

class AtomicWriteFileRequestAccessMethodChoiceRecordAccess(Sequence):
    sequenceElements = \
        [ Element('fileStartRecord', Integer)
        , Element('recordCount', Unsigned)
        , Element('fileRecordData', SequenceOf(OctetString))
        ]

class AtomicWriteFileRequestAccessMethodChoice(Choice):
    choiceElements = \
        [ Element('streamAccess', AtomicWriteFileRequestAccessMethodChoiceStreamAccess, 0)
        , Element('recordAccess', AtomicWriteFileRequestAccessMethodChoiceRecordAccess, 1)
        ]

class AtomicWriteFileRequest(ConfirmedRequestSequence):
    serviceChoice = 7
    sequenceElements = \
        [ Element('fileIdentifier', ObjectIdentifier)
        , Element('accessMethod', AtomicWriteFileRequestAccessMethodChoice)
        ]

register_confirmed_request_type(AtomicWriteFileRequest)

class AtomicWriteFileACK(ComplexAckSequence):
    serviceChoice = 7
    sequenceElements = \
        [ Element('fileStartPosition', Integer, 0, True)
        , Element('fileStartRecord', Integer, 1, True)
        ]

register_complex_ack_type(AtomicWriteFileACK)

#-----

class AddListElementRequest(ConfirmedRequestSequence):
    serviceChoice = 8
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('listOfElements', Any, 3)
        ]

register_confirmed_request_type(AddListElementRequest)

#-----

class CreateObjectRequestObjectSpecifier(Choice):
    choiceElements = \
        [ Element('objectType', ObjectType, 0)
        , Element('objectIdentifier',ObjectIdentifier, 1)
        ]

class CreateObjectRequest(ConfirmedRequestSequence):
    serviceChoice = 10
    sequenceElements = \
        [ Element('objectSpecifier', CreateObjectRequestObjectSpecifier, 0)
        , Element('listOfInitialValues', SequenceOf(PropertyValue), 1, True)
        ]

register_confirmed_request_type(CreateObjectRequest)

class CreateObjectACK(ComplexAckSequence):
    serviceChoice = 10
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier)
        ]

register_complex_ack_type(CreateObjectACK)

#-----

class DeleteObjectRequest(ConfirmedRequestSequence):
    serviceChoice = 11
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier)
        ]

register_confirmed_request_type(DeleteObjectRequest)

#-----

class RemoveListElementRequest(ConfirmedRequestSequence):
    serviceChoice = 9
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2)
        , Element('listOfElements', Any, 3)
        ]

register_confirmed_request_type(RemoveListElementRequest)

#-----

class DeviceCommunicationControlRequestEnableDisable(Enumerated):
    enumerations = \
        { 'enable':0
        , 'disable':1
        , 'defaultInitiation':2
        }

class DeviceCommunicationControlRequest(ConfirmedRequestSequence):
    serviceChoice = 17
    sequenceElements = \
        [ Element('timeDuration', Unsigned, 0, True)
        , Element('enableDisable', DeviceCommunicationControlRequestEnableDisable, 1, True)
        , Element('password', CharacterString, 2, True)
        ]

register_confirmed_request_type(DeviceCommunicationControlRequest)

class ConfirmedPrivateTransferRequest(ConfirmedRequestSequence):
    serviceChoice = 18
    sequenceElements = \
        [ Element('vendorID', Unsigned, 0)
        , Element('serviceNumber', Unsigned, 1)
        , Element('serviceParameters', Any, 2, True)
        ]

register_confirmed_request_type(ConfirmedPrivateTransferRequest)

class ConfirmedPrivateTransferACK(ComplexAckSequence):
    serviceChoice = 18
    sequenceElements = \
        [ Element('vendorID', Unsigned, 0)
        , Element('serviceNumber', Unsigned, 1)
        , Element('resultBlock', Any, 2, True)
        ]

register_complex_ack_type(ConfirmedPrivateTransferACK)

#-----

class ConfirmedTextMessageRequestMessageClass(Choice):
    choiceElements = \
        [ Element('numeric', Unsigned, 0)
        , Element('character', CharacterString, 1)
        ]

class ConfirmedTextMessageRequestMessagePriority(Enumerated):
    enumerations = \
        { 'normal':0
        , 'urgent':1
        }

class ConfirmedTextMessageRequest(ConfirmedRequestSequence):
    serviceChoice = 19
    sequenceElements = \
        [ Element('textMessageSourceDevice', ObjectIdentifier, 0)
        , Element('messageClass', ConfirmedTextMessageRequestMessageClass, 1, True)
        , Element('messagePriority', ConfirmedTextMessageRequestMessagePriority, 2)
        , Element('message', CharacterString, 3)
        ]

register_confirmed_request_type(ConfirmedTextMessageRequest)

#-----

class ReinitializeDeviceRequestReinitializedStateOfDevice(Enumerated):
    enumerations = \
        { 'coldstart':0
        , 'warmstart':1
        , 'startbackup':2
        , 'endbackup':3
        , 'startrestore':4
        , 'endrestore':5
        , 'abortrestore':6
        }

class ReinitializeDeviceRequest(ConfirmedRequestSequence):
    serviceChoice = 20
    sequenceElements = \
        [ Element('reinitializedStateOfDevice', ReinitializeDeviceRequestReinitializedStateOfDevice, 0)
        , Element('password', CharacterString, 1, True)
        ]

register_confirmed_request_type(ReinitializeDeviceRequest)

#-----

class VTOpenRequest(ConfirmedRequestSequence):
    serviceChoice = 21
    sequenceElements = \
        [ Element('vtClass', VTClass,)
        , Element('localVTSessionIdentifier', Unsigned)
        ]

register_confirmed_request_type(VTOpenRequest)

class VTOpenACK(ComplexAckSequence):
    serviceChoice = 21
    sequenceElements = \
        [ Element('remoteVTSessionIdentifier', Unsigned)
        ]

register_complex_ack_type(VTOpenACK)

class VTCloseRequest(ConfirmedRequestSequence):
    serviceChoice = 22
    sequenceElements = \
        [ Element('listOfRemoteVTSessionIdentifiers', SequenceOf(Unsigned))
        ]

register_confirmed_request_type(VTCloseRequest)
class VTDataRequest(ConfirmedRequestSequence):
    serviceChoice = 23
    sequenceElements = \
        [ Element('vtSessionIdentifier', Unsigned,)
        , Element('vtNewData', OctetString)
        , Element('vtDataFlag', Unsigned)
        ]

register_confirmed_request_type(VTDataRequest)

class VTDataACK(ComplexAckSequence):
    serviceChoice = 23
    sequenceElements = \
        [ Element('allNewDataAccepted', Boolean, 0)
        , Element('acceptedOctetCount', Unsigned, 1)
        ]

register_complex_ack_type(VTDataACK)

#-----

# removed in version 1, revision 11
class AuthenticateRequest(ConfirmedRequestSequence):
    serviceChoice = 24
    sequenceElements = \
        [ Element('pseudoRandomNumber', Unsigned, 0)
        , Element('expectedInvokeID', Unsigned, 1)
        , Element('operatorName', CharacterString, 2)
        , Element('operatorPassword', CharacterString, 3)
        , Element('startEncipheredSession', Boolean, 4)
        ]

# removed in version 1, revision 11
class AuthenticateACK(ComplexAckSequence):
    serviceChoice = 24
    sequenceElements = \
        [ Element('modifiedRandomNumber', Unsigned)
        ]

# removed in version 1, revision 11
class RequestKeyRequest(ConfirmedRequestSequence):
    serviceChoice = 25
    sequenceElements = \
        [ Element('requestingDeviceIdentifier', ObjectIdentifier)
        , Element('requestingDeviceAddress', DeviceAddress)
        , Element('remoteDeviceIdentifier', ObjectIdentifier)
        , Element('remoteDeviceAddress', DeviceAddress)
        ]

#-----------------------------------

class ConfirmedServiceChoice(Enumerated):
    enumerations = {
    # Alarm and Event Services
        'acknowledgeAlarm':0,
        'confirmedCOVNotification':1,
        'confirmedEventNotification':2,
        'getAlarmSummary':3,
        'getEnrollmentSummary':4,
        'getEventInformation':29,
        'subscribeCOV':5,
        'subscribeCOVProperty':28,
        'lifeSafetyOperation':27,

    # File Access Services
        'atomicReadFile':6,
        'atomicWriteFile':7,

    # Object Access Services
        'addListElement':8,
        'removeListElement':9,
        'createObject':10,
        'deleteObject':11,
        'readProperty':12,
        'readPropertyMultiple':14,
        'readRange':26,
        'writeProperty':15,
        'writePropertyMultiple':16,

    # Remote Device Management Services
        'deviceCommunicationControl':17,
        'confirmedPrivateTransfer':18,
        'confirmedTextMessage':19,
        'reinitializeDevice':20,

    # Virtual Terminal Services
        'vtOpen':21,
        'vtClose':22,
        'vtData':23,
        }

expand_enumerations(ConfirmedServiceChoice)

class UnconfirmedServiceChoice(Enumerated):
    enumerations = {
        'iAm':0,
        'iHave':1,
        'unconfirmedCOVNotification':2,
        'unconfirmedEventNotification':3,
        'unconfirmedPrivateTransfer':4,
        'unconfirmedTextMessage':5,
        'timeSynchronization':6,
        'whoHas':7,
        'whoIs':8,
        'utcTimeSynchronization':9,
        'writeGroup':10,
        }

expand_enumerations(UnconfirmedServiceChoice)
