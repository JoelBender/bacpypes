#!/usr/bin/env python

from ..debugging import bacpypes_debugging, ModuleLogger
from ..capability import Capability

from ..pdu import GlobalBroadcast
from ..basetypes import ErrorType
from ..primitivedata import Atomic, Null, Unsigned, Date, Time, ObjectIdentifier
from ..constructeddata import Any, Array, ArrayOf

from ..apdu import Error, WhoIsRequest, IAmRequest, \
    SimpleAckPDU, ReadPropertyACK, ReadPropertyMultipleACK, \
    ReadAccessResult, ReadAccessResultElement, ReadAccessResultElementChoice
from ..errors import ExecutionError, InconsistentParameters, \
    MissingRequiredParameter, ParameterOutOfRange
    
from ..object import register_object_type, registered_object_types, \
    Property, PropertyError, DeviceObject, registered_object_types

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   CurrentDateProperty
#

class CurrentDateProperty(Property):

    def __init__(self, identifier):
        Property.__init__(self, identifier, Date, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        # access an array
        if arrayIndex is not None:
            raise TypeError("{0} is unsubscriptable".format(self.identifier))

        # get the value
        now = Date()
        now.now()
        return now.value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentTimeProperty
#

class CurrentTimeProperty(Property):

    def __init__(self, identifier):
        Property.__init__(self, identifier, Time, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        # access an array
        if arrayIndex is not None:
            raise TypeError("{0} is unsubscriptable".format(self.identifier))

        # get the value
        now = Time()
        now.now()
        return now.value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   LocalDeviceObject
#

@bacpypes_debugging
class LocalDeviceObject(DeviceObject):

    properties = \
        [ CurrentTimeProperty('localTime')
        , CurrentDateProperty('localDate')
        ]

    defaultProperties = \
        { 'maxApduLengthAccepted': 1024
        , 'segmentationSupported': 'segmentedBoth'
        , 'maxSegmentsAccepted': 16
        , 'apduSegmentTimeout': 5000
        , 'apduTimeout': 3000
        , 'numberOfApduRetries': 3
        }

    def __init__(self, **kwargs):
        if _debug: LocalDeviceObject._debug("__init__ %r", kwargs)

        # fill in default property values not in kwargs
        for attr, value in LocalDeviceObject.defaultProperties.items():
            if attr not in kwargs:
                kwargs[attr] = value

        # check for registration
        if self.__class__ not in registered_object_types.values():
            if 'vendorIdentifier' not in kwargs:
                raise RuntimeError("vendorIdentifier required to auto-register the LocalDeviceObject class")
            register_object_type(self.__class__, vendor_id=kwargs['vendorIdentifier'])

        # check for local time
        if 'localDate' in kwargs:
            raise RuntimeError("localDate is provided by LocalDeviceObject and cannot be overridden")
        if 'localTime' in kwargs:
            raise RuntimeError("localTime is provided by LocalDeviceObject and cannot be overridden")

        # check for a minimum value
        if kwargs['maxApduLengthAccepted'] < 50:
            raise ValueError("invalid max APDU length accepted")

        # dump the updated attributes
        if _debug: LocalDeviceObject._debug("    - updated kwargs: %r", kwargs)

        # proceed as usual
        DeviceObject.__init__(self, **kwargs)

        # create a default implementation of an object list for local devices.
        # If it is specified in the kwargs, that overrides this default.
        if ('objectList' not in kwargs):
            self.objectList = ArrayOf(ObjectIdentifier)([self.objectIdentifier])

            # if the object has a property list and one wasn't provided
            # in the kwargs, then it was created by default and the objectList
            # property should be included
            if ('propertyList' not in kwargs) and self.propertyList:
                # make sure it's not already there
                if 'objectList' not in self.propertyList:
                    self.propertyList.append('objectList')

#
#   Who-Is I-Am Services
#

@bacpypes_debugging
class WhoIsIAmServices(Capability):

    def __init__(self):
        if _debug: WhoIsIAmServices._debug("__init__")
        Capability.__init__(self)

    def who_is(self, low_limit=None, high_limit=None, address=None):
        if _debug: WhoIsIAmServices._debug("who_is")

        # build a request
        whoIs = WhoIsRequest()

        # defaults to a global broadcast
        if not address:
            address = GlobalBroadcast()

        # set the destination
        whoIs.pduDestination = address

        # check for consistent parameters
        if (low_limit is not None):
            if (high_limit is None):
                raise MissingRequiredParameter("high_limit required")
            if (low_limit < 0) or (low_limit > 4194303):
                raise ParameterOutOfRange("low_limit out of range")

            # low limit is fine
            whoIs.deviceInstanceRangeLowLimit = low_limit

        if (high_limit is not None):
            if (low_limit is None):
                raise MissingRequiredParameter("low_limit required")
            if (high_limit < 0) or (high_limit > 4194303):
                raise ParameterOutOfRange("high_limit out of range")

            # high limit is fine
            whoIs.deviceInstanceRangeHighLimit = high_limit

        if _debug: WhoIsIAmServices._debug("    - whoIs: %r", whoIs)

        ### put the parameters someplace where they can be matched when the
        ### appropriate I-Am comes in

        # away it goes
        self.request(whoIs)

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        if _debug: WhoIsIAmServices._debug("do_WhoIsRequest %r", apdu)

        # ignore this if there's no local device
        if not self.localDevice:
            if _debug: WhoIsIAmServices._debug("    - no local device")
            return

        # extract the parameters
        low_limit = apdu.deviceInstanceRangeLowLimit
        high_limit = apdu.deviceInstanceRangeHighLimit

        # check for consistent parameters
        if (low_limit is not None):
            if (high_limit is None):
                raise MissingRequiredParameter("deviceInstanceRangeHighLimit required")
            if (low_limit < 0) or (low_limit > 4194303):
                raise ParameterOutOfRange("deviceInstanceRangeLowLimit out of range")
        if (high_limit is not None):
            if (low_limit is None):
                raise MissingRequiredParameter("deviceInstanceRangeLowLimit required")
            if (high_limit < 0) or (high_limit > 4194303):
                raise ParameterOutOfRange("deviceInstanceRangeHighLimit out of range")

        # see we should respond
        if (low_limit is not None):
            if (self.localDevice.objectIdentifier[1] < low_limit):
                return
        if (high_limit is not None):
            if (self.localDevice.objectIdentifier[1] > high_limit):
                return

        # generate an I-Am
        self.i_am(address=apdu.pduSource)

    def i_am(self, address=None):
        if _debug: WhoIsIAmServices._debug("i_am")

        # this requires a local device
        if not self.localDevice:
            if _debug: WhoIsIAmServices._debug("    - no local device")
            return

        # create a I-Am "response" back to the source
        iAm = IAmRequest(
            iAmDeviceIdentifier=self.localDevice.objectIdentifier,
            maxAPDULengthAccepted=self.localDevice.maxApduLengthAccepted,
            segmentationSupported=self.localDevice.segmentationSupported,
            vendorID=self.localDevice.vendorIdentifier,
            )

        # defaults to a global broadcast
        if not address:
            address = GlobalBroadcast()
        iAm.pduDestination = address
        if _debug: WhoIsIAmServices._debug("    - iAm: %r", iAm)

        # away it goes
        self.request(iAm)

    def do_IAmRequest(self, apdu):
        """Respond to an I-Am request."""
        if _debug: WhoIsIAmServices._debug("do_IAmRequest %r", apdu)

        # check for required parameters
        if apdu.iAmDeviceIdentifier is None:
            raise MissingRequiredParameter("iAmDeviceIdentifier required")
        if apdu.maxAPDULengthAccepted is None:
            raise MissingRequiredParameter("maxAPDULengthAccepted required")
        if apdu.segmentationSupported is None:
            raise MissingRequiredParameter("segmentationSupported required")
        if apdu.vendorID is None:
            raise MissingRequiredParameter("vendorID required")

        # extract the device instance number
        device_instance = apdu.iAmDeviceIdentifier[1]
        if _debug: WhoIsIAmServices._debug("    - device_instance: %r", device_instance)

        # extract the source address
        device_address = apdu.pduSource
        if _debug: WhoIsIAmServices._debug("    - device_address: %r", device_address)

        ### check to see if the application is looking for this device
        ### and update the device info cache if it is

#
#   Who-Has I-Have Services
#

@bacpypes_debugging
class WhoHasIHaveServices(Capability):

    def __init__(self):
        if _debug: WhoHasIHaveServices._debug("__init__")
        Capability.__init__(self)

    def who_has(self, thing, address=None):
        if _debug: WhoHasIHaveServices._debug("who_has %r address=%r", thing, address)

        raise NotImplementedError("who_has")

    def do_WhoHasRequest(self, apdu):
        """Respond to a Who-Has request."""
        if _debug: WhoHasIHaveServices._debug("do_WhoHasRequest, %r", apdu)

        # ignore this if there's no local device
        if not self.localDevice:
            if _debug: WhoIsIAmServices._debug("    - no local device")
            return

        # find the object
        if apdu.object.objectIdentifier is not None:
            obj = self.objectIdentifier.get(apdu.object.objectIdentifier, None)
        elif apdu.object.objectName is not None:
            obj = self.objectName.get(apdu.object.objectName, None)
        else:
            raise InconsistentParameters("object identifier or object name required")
        if not obj:
            raise ExecutionError(errorClass='object', errorCode='unknownObject')

        # send out the response
        self.i_have(obj, address=apdu.pduSource)

    def i_have(self, thing, address=None):
        if _debug: WhoHasIHaveServices._debug("i_have %r address=%r", thing, address)

        # ignore this if there's no local device
        if not self.localDevice:
            if _debug: WhoIsIAmServices._debug("    - no local device")
            return

        # build the request
        iHave = IHaveRequest(
            deviceIdentifier=self.localDevice.objectIdentifier,
            objectIdentifier=thing.objectIdentifier,
            objectName=thing.objectName,
            )

        # defaults to a global broadcast
        if not address:
            address = GlobalBroadcast()
        iHave.pduDestination = address
        if _debug: WhoHasIHaveServices._debug("    - iHave: %r", iHave)

        # send it along
        self.request(iHave)

    def do_IHaveRequest(self, apdu):
        """Respond to a I-Have request."""
        if _debug: WhoHasIHaveServices._debug("do_IHaveRequest %r", apdu)

        # check for required parameters
        if apdu.deviceIdentifier is None:
            raise MissingRequiredParameter("deviceIdentifier required")
        if apdu.objectIdentifier is None:
            raise MissingRequiredParameter("objectIdentifier required")
        if apdu.objectName is None:
            raise MissingRequiredParameter("objectName required")

        ### check to see if the application is looking for this object

#
#   ReadProperty and WriteProperty Services
#

@bacpypes_debugging
class ReadWritePropertyServices(Capability):

    def __init__(self):
        if _debug: ReadWritePropertyServices._debug("__init__")
        Capability.__init__(self)

    def do_ReadPropertyRequest(self, apdu):
        """Return the value of some property of one of our objects."""
        if _debug: ReadWritePropertyServices._debug("do_ReadPropertyRequest %r", apdu)

        # extract the object identifier
        objId = apdu.objectIdentifier

        # check for wildcard
        if (objId == ('device', 4194303)) and self.localDevice is not None:
            if _debug: ReadWritePropertyServices._debug("    - wildcard device identifier")
            objId = self.localDevice.objectIdentifier

        # get the object
        obj = self.get_object_id(objId)
        if _debug: ReadWritePropertyServices._debug("    - object: %r", obj)

        if not obj:
            raise ExecutionError(errorClass='object', errorCode='unknownObject')

        try:
            # get the datatype
            datatype = obj.get_datatype(apdu.propertyIdentifier)
            if _debug: ReadWritePropertyServices._debug("    - datatype: %r", datatype)

            # get the value
            value = obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex)
            if _debug: ReadWritePropertyServices._debug("    - value: %r", value)
            if value is None:
                raise PropertyError(apdu.propertyIdentifier)

            # change atomic values into something encodeable
            if issubclass(datatype, Atomic):
                value = datatype(value)
            elif issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = Unsigned(value)
                elif issubclass(datatype.subtype, Atomic):
                    value = datatype.subtype(value)
                elif not isinstance(value, datatype.subtype):
                    raise TypeError("invalid result datatype, expecting {0} and got {1}" \
                        .format(datatype.subtype.__name__, type(value).__name__))
            elif not isinstance(value, datatype):
                raise TypeError("invalid result datatype, expecting {0} and got {1}" \
                    .format(datatype.__name__, type(value).__name__))
            if _debug: ReadWritePropertyServices._debug("    - encodeable value: %r", value)

            # this is a ReadProperty ack
            resp = ReadPropertyACK(context=apdu)
            resp.objectIdentifier = objId
            resp.propertyIdentifier = apdu.propertyIdentifier
            resp.propertyArrayIndex = apdu.propertyArrayIndex

            # save the result in the property value
            resp.propertyValue = Any()
            resp.propertyValue.cast_in(value)
            if _debug: ReadWritePropertyServices._debug("    - resp: %r", resp)

        except PropertyError:
            raise ExecutionError(errorClass='object', errorCode='unknownProperty')

        # return the result
        self.response(resp)

    def do_WritePropertyRequest(self, apdu):
        """Change the value of some property of one of our objects."""
        if _debug: ReadWritePropertyServices._debug("do_WritePropertyRequest %r", apdu)

        # get the object
        obj = self.get_object_id(apdu.objectIdentifier)
        if _debug: ReadWritePropertyServices._debug("    - object: %r", obj)
        if not obj:
            raise ExecutionError(errorClass='object', errorCode='unknownObject')

        try:
            # check if the property exists
            if obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex) is None:
                raise PropertyError(apdu.propertyIdentifier)

            # get the datatype, special case for null
            if apdu.propertyValue.is_application_class_null():
                datatype = Null
            else:
                datatype = obj.get_datatype(apdu.propertyIdentifier)
            if _debug: ReadWritePropertyServices._debug("    - datatype: %r", datatype)

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
            if _debug: ReadWritePropertyServices._debug("    - value: %r", value)

            # change the value
            value = obj.WriteProperty(apdu.propertyIdentifier, value, apdu.propertyArrayIndex, apdu.priority)

            # success
            resp = SimpleAckPDU(context=apdu)
            if _debug: ReadWritePropertyServices._debug("    - resp: %r", resp)

        except PropertyError:
            raise ExecutionError(errorClass='object', errorCode='unknownProperty')

        # return the result
        self.response(resp)

#
#   read_property_to_any
#

@bacpypes_debugging
def read_property_to_any(obj, propertyIdentifier, propertyArrayIndex=None):
    """Read the specified property of the object, with the optional array index,
    and cast the result into an Any object."""
    if _debug: read_property_to_any._debug("read_property_to_any %s %r %r", obj, propertyIdentifier, propertyArrayIndex)

    # get the datatype
    datatype = obj.get_datatype(propertyIdentifier)
    if _debug: read_property_to_any._debug("    - datatype: %r", datatype)
    if datatype is None:
        raise ExecutionError(errorClass='property', errorCode='datatypeNotSupported')

    # get the value
    value = obj.ReadProperty(propertyIdentifier, propertyArrayIndex)
    if _debug: read_property_to_any._debug("    - value: %r", value)
    if value is None:
        raise ExecutionError(errorClass='property', errorCode='unknownProperty')

    # change atomic values into something encodeable
    if issubclass(datatype, Atomic):
        value = datatype(value)
    elif issubclass(datatype, Array) and (propertyArrayIndex is not None):
        if propertyArrayIndex == 0:
            value = Unsigned(value)
        elif issubclass(datatype.subtype, Atomic):
            value = datatype.subtype(value)
        elif not isinstance(value, datatype.subtype):
            raise TypeError("invalid result datatype, expecting %s and got %s" \
                % (datatype.subtype.__name__, type(value).__name__))
    elif not isinstance(value, datatype):
        raise TypeError("invalid result datatype, expecting %s and got %s" \
            % (datatype.__name__, type(value).__name__))
    if _debug: read_property_to_any._debug("    - encodeable value: %r", value)

    # encode the value
    result = Any()
    result.cast_in(value)
    if _debug: read_property_to_any._debug("    - result: %r", result)

    # return the object
    return result

#
#   read_property_to_result_element
#

@bacpypes_debugging
def read_property_to_result_element(obj, propertyIdentifier, propertyArrayIndex=None):
    """Read the specified property of the object, with the optional array index,
    and cast the result into an Any object."""
    if _debug: read_property_to_result_element._debug("read_property_to_result_element %s %r %r", obj, propertyIdentifier, propertyArrayIndex)

    # save the result in the property value
    read_result = ReadAccessResultElementChoice()

    try:
        read_result.propertyValue = read_property_to_any(obj, propertyIdentifier, propertyArrayIndex)
        if _debug: read_property_to_result_element._debug("    - success")
    except PropertyError as error:
        if _debug: read_property_to_result_element._debug("    - error: %r", error)
        read_result.propertyAccessError = ErrorType(errorClass='property', errorCode='unknownProperty')
    except ExecutionError as error:
        if _debug: read_property_to_result_element._debug("    - error: %r", error)
        read_result.propertyAccessError = ErrorType(errorClass=error.errorClass, errorCode=error.errorCode)

    # make an element for this value
    read_access_result_element = ReadAccessResultElement(
        propertyIdentifier=propertyIdentifier,
        propertyArrayIndex=propertyArrayIndex,
        readResult=read_result,
        )
    if _debug: read_property_to_result_element._debug("    - read_access_result_element: %r", read_access_result_element)

    # fini
    return read_access_result_element

#
#   ReadWritePropertyMultipleServices
#

@bacpypes_debugging
class ReadWritePropertyMultipleServices(Capability):

    def __init__(self):
        if _debug: ReadWritePropertyMultipleServices._debug("__init__")
        Capability.__init__(self)

    def do_ReadPropertyMultipleRequest(self, apdu):
        """Respond to a ReadPropertyMultiple Request."""
        if _debug: ReadWritePropertyMultipleServices._debug("do_ReadPropertyMultipleRequest %r", apdu)

        # response is a list of read access results (or an error)
        resp = None
        read_access_result_list = []

        # loop through the request
        for read_access_spec in apdu.listOfReadAccessSpecs:
            # get the object identifier
            objectIdentifier = read_access_spec.objectIdentifier
            if _debug: ReadWritePropertyMultipleServices._debug("    - objectIdentifier: %r", objectIdentifier)

            # check for wildcard
            if (objectIdentifier == ('device', 4194303)) and self.localDevice is not None:
                if _debug: ReadWritePropertyMultipleServices._debug("    - wildcard device identifier")
                objectIdentifier = self.localDevice.objectIdentifier

            # get the object
            obj = self.get_object_id(objectIdentifier)
            if _debug: ReadWritePropertyMultipleServices._debug("    - object: %r", obj)

            # make sure it exists
            if not obj:
                resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
                if _debug: ReadWritePropertyMultipleServices._debug("    - unknown object error: %r", resp)
                break

            # build a list of result elements
            read_access_result_element_list = []

            # loop through the property references
            for prop_reference in read_access_spec.listOfPropertyReferences:
                # get the property identifier
                propertyIdentifier = prop_reference.propertyIdentifier
                if _debug: ReadWritePropertyMultipleServices._debug("    - propertyIdentifier: %r", propertyIdentifier)

                # get the array index (optional)
                propertyArrayIndex = prop_reference.propertyArrayIndex
                if _debug: ReadWritePropertyMultipleServices._debug("    - propertyArrayIndex: %r", propertyArrayIndex)

                # check for special property identifiers
                if propertyIdentifier in ('all', 'required', 'optional'):
                    for propId, prop in obj._properties.items():
                        if _debug: ReadWritePropertyMultipleServices._debug("    - checking: %r %r", propId, prop.optional)

                        if (propertyIdentifier == 'all'):
                            pass
                        elif (propertyIdentifier == 'required') and (prop.optional):
                            if _debug: ReadWritePropertyMultipleServices._debug("    - not a required property")
                            continue
                        elif (propertyIdentifier == 'optional') and (not prop.optional):
                            if _debug: ReadWritePropertyMultipleServices._debug("    - not an optional property")
                            continue

                        # read the specific property
                        read_access_result_element = read_property_to_result_element(obj, propId, propertyArrayIndex)

                        # check for undefined property
                        if read_access_result_element.readResult.propertyAccessError \
                            and read_access_result_element.readResult.propertyAccessError.errorCode == 'unknownProperty':
                            continue

                        # add it to the list
                        read_access_result_element_list.append(read_access_result_element)

                else:
                    # read the specific property
                    read_access_result_element = read_property_to_result_element(obj, propertyIdentifier, propertyArrayIndex)

                    # add it to the list
                    read_access_result_element_list.append(read_access_result_element)

            # build a read access result
            read_access_result = ReadAccessResult(
                objectIdentifier=objectIdentifier,
                listOfResults=read_access_result_element_list
                )
            if _debug: ReadWritePropertyMultipleServices._debug("    - read_access_result: %r", read_access_result)

            # add it to the list
            read_access_result_list.append(read_access_result)

        # this is a ReadPropertyMultiple ack
        if not resp:
            resp = ReadPropertyMultipleACK(context=apdu)
            resp.listOfReadAccessResults = read_access_result_list
            if _debug: ReadWritePropertyMultipleServices._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

#   def do_WritePropertyMultipleRequest(self, apdu):
#       """Respond to a WritePropertyMultiple Request."""
#       if _debug: ReadWritePropertyMultipleServices._debug("do_ReadPropertyMultipleRequest %r", apdu)
#
#       raise NotImplementedError()
