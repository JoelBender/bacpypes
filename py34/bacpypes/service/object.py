#!/usr/bin/env python

from ..debugging import bacpypes_debugging, ModuleLogger
from ..capability import Capability

from ..basetypes import ErrorType
from ..primitivedata import Atomic, Null, Unsigned
from ..constructeddata import Any, Array

from ..apdu import Error, \
    SimpleAckPDU, ReadPropertyACK, ReadPropertyMultipleACK, \
    ReadAccessResult, ReadAccessResultElement, ReadAccessResultElementChoice
from ..errors import ExecutionError
from ..object import PropertyError

# some debugging
_debug = 0
_log = ModuleLogger(globals())

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
