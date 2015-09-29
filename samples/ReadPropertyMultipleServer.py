#!/usr/bin/python

"""
This sample application shows how to extend the basic functionality of a device 
to support the ReadPropertyMultiple service.
"""

import random

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Atomic, Real, Unsigned
from bacpypes.constructeddata import Array, Any
from bacpypes.basetypes import ServicesSupported, ErrorType
from bacpypes.apdu import ReadPropertyMultipleACK, ReadAccessResult, ReadAccessResultElement, ReadAccessResultElementChoice
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import AnalogValueObject, Property, PropertyError, register_object_type
from bacpypes.apdu import Error
from bacpypes.errors import ExecutionError

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None

#
#   RandomValueProperty
#

@bacpypes_debugging
class RandomValueProperty(Property):

    def __init__(self, identifier):
        if _debug: RandomValueProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, Real, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: RandomValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # return a random value
        value = random.random() * 100.0
        if _debug: RandomValueProperty._debug("    - value: %r", value)

        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: RandomValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   Random Value Object Type
#

@bacpypes_debugging
class RandomAnalogValueObject(AnalogValueObject):

    properties = [
        RandomValueProperty('presentValue'),
        ]

    def __init__(self, **kwargs):
        if _debug: RandomAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

register_object_type(RandomAnalogValueObject)

#
#   ReadPropertyToAny
#

@bacpypes_debugging
def ReadPropertyToAny(obj, propertyIdentifier, propertyArrayIndex=None):
    """Read the specified property of the object, with the optional array index,
    and cast the result into an Any object."""
    if _debug: ReadPropertyToAny._debug("ReadPropertyToAny %s %r %r", obj, propertyIdentifier, propertyArrayIndex)

    # get the datatype
    datatype = obj.get_datatype(propertyIdentifier)
    if _debug: ReadPropertyToAny._debug("    - datatype: %r", datatype)
    if datatype is None:
        raise ExecutionError(errorClass='property', errorCode='datatypeNotSupported')

    # get the value
    value = obj.ReadProperty(propertyIdentifier, propertyArrayIndex)
    if _debug: ReadPropertyToAny._debug("    - value: %r", value)
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
            raise TypeError, "invalid result datatype, expecting %s and got %s" \
                % (datatype.subtype.__name__, type(value).__name__)
    elif not isinstance(value, datatype):
        raise TypeError, "invalid result datatype, expecting %s and got %s" \
            % (datatype.__name__, type(value).__name__)
    if _debug: ReadPropertyToAny._debug("    - encodeable value: %r", value)

    # encode the value
    result = Any()
    result.cast_in(value)
    if _debug: ReadPropertyToAny._debug("    - result: %r", result)

    # return the object
    return result

#
#   ReadPropertyToResultElement
#

@bacpypes_debugging
def ReadPropertyToResultElement(obj, propertyIdentifier, propertyArrayIndex=None):
    """Read the specified property of the object, with the optional array index,
    and cast the result into an Any object."""
    if _debug: ReadPropertyToResultElement._debug("ReadPropertyToResultElement %s %r %r", obj, propertyIdentifier, propertyArrayIndex)

    # save the result in the property value
    read_result = ReadAccessResultElementChoice()

    try:
        read_result.propertyValue = ReadPropertyToAny(obj, propertyIdentifier, propertyArrayIndex)
        if _debug: ReadPropertyToResultElement._debug("    - success")
    except PropertyError, error:
        if _debug: ReadPropertyToResultElement._debug("    - error: %r", error)
        read_result.propertyAccessError = ErrorType(errorClass='property', errorCode='unknownProperty')
    except ExecutionError, error:
        if _debug: ReadPropertyToResultElement._debug("    - error: %r", error)
        read_result.propertyAccessError = ErrorType(errorClass=error.errorClass, errorCode=error.errorCode)

    # make an element for this value
    read_access_result_element = ReadAccessResultElement(
        propertyIdentifier=propertyIdentifier,
        propertyArrayIndex=propertyArrayIndex,
        readResult=read_result,
        )
    if _debug: ReadPropertyToResultElement._debug("    - read_access_result_element: %r", read_access_result_element)

    # fini
    return read_access_result_element

#
#   ReadPropertyMultipleApplication
#

@bacpypes_debugging
class ReadPropertyMultipleApplication(BIPSimpleApplication):

    def __init__(self, *args, **kwargs):
        if _debug: ReadPropertyMultipleApplication._debug("__init__ %r %r", args, kwargs)
        BIPSimpleApplication.__init__(self, *args, **kwargs)

    def do_ReadPropertyMultipleRequest(self, apdu):
        """Respond to a ReadPropertyMultiple Request."""
        if _debug: ReadPropertyMultipleApplication._debug("do_ReadPropertyMultipleRequest %r", apdu)

        # response is a list of read access results (or an error)
        resp = None
        read_access_result_list = []

        # loop through the request
        for read_access_spec in apdu.listOfReadAccessSpecs:
            # get the object identifier
            objectIdentifier = read_access_spec.objectIdentifier
            if _debug: ReadPropertyMultipleApplication._debug("    - objectIdentifier: %r", objectIdentifier)

            # check for wildcard
            if (objectIdentifier == ('device', 4194303)):
                if _debug: ReadPropertyMultipleApplication._debug("    - wildcard device identifier")
                objectIdentifier = self.localDevice.objectIdentifier

            # get the object
            obj = self.get_object_id(objectIdentifier)
            if _debug: ReadPropertyMultipleApplication._debug("    - object: %r", obj)

            # make sure it exists
            if not obj:
                resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
                if _debug: ReadPropertyMultipleApplication._debug("    - unknown object error: %r", resp)
                break

            # build a list of result elements
            read_access_result_element_list = []

            # loop through the property references
            for prop_reference in read_access_spec.listOfPropertyReferences:
                # get the property identifier
                propertyIdentifier = prop_reference.propertyIdentifier
                if _debug: ReadPropertyMultipleApplication._debug("    - propertyIdentifier: %r", propertyIdentifier)

                # get the array index (optional)
                propertyArrayIndex = prop_reference.propertyArrayIndex
                if _debug: ReadPropertyMultipleApplication._debug("    - propertyArrayIndex: %r", propertyArrayIndex)

                # check for special property identifiers
                if propertyIdentifier in ('all', 'required', 'optional'):
                    for propId, prop in obj._properties.items():
                        if _debug: ReadPropertyMultipleApplication._debug("    - checking: %r %r", propId, prop.optional)

                        if (propertyIdentifier == 'all'):
                            pass
                        elif (propertyIdentifier == 'required') and (prop.optional):
                            if _debug: ReadPropertyMultipleApplication._debug("    - not a required property")
                            continue
                        elif (propertyIdentifier == 'optional') and (not prop.optional):
                            if _debug: ReadPropertyMultipleApplication._debug("    - not an optional property")
                            continue

                        # read the specific property
                        read_access_result_element = ReadPropertyToResultElement(obj, propId, propertyArrayIndex)

                        # check for undefined property
                        if read_access_result_element.readResult.propertyAccessError \
                            and read_access_result_element.readResult.propertyAccessError.errorCode == 'unknownProperty':
                            continue

                        # add it to the list
                        read_access_result_element_list.append(read_access_result_element)

                else:
                    # read the specific property
                    read_access_result_element = ReadPropertyToResultElement(obj, propertyIdentifier, propertyArrayIndex)

                    # add it to the list
                    read_access_result_element_list.append(read_access_result_element)

            # build a read access result
            read_access_result = ReadAccessResult(
                objectIdentifier=objectIdentifier,
                listOfResults=read_access_result_element_list
                )
            if _debug: ReadPropertyMultipleApplication._debug("    - read_access_result: %r", read_access_result)

            # add it to the list
            read_access_result_list.append(read_access_result)

        # this is a ReadPropertyMultiple ack
        if not resp:
            resp = ReadPropertyMultipleACK(context=apdu)
            resp.listOfReadAccessResults = read_access_result_list
            if _debug: ReadPropertyMultipleApplication._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

#
#   __main__
#

try:
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    this_application = ReadPropertyMultipleApplication(this_device, args.ini.address)

    # make a random input object
    ravo1 = RandomAnalogValueObject(
        objectIdentifier=('analogValue', 1), objectName='Random1'
        )
    _log.debug("    - ravo1: %r", ravo1)

    ravo2 = RandomAnalogValueObject(
        objectIdentifier=('analogValue', 2), objectName='Random2'
        )
    _log.debug("    - ravo2: %r", ravo2)

    # add it to the device
    this_application.add_object(ravo1)
    this_application.add_object(ravo2)
    _log.debug("    - object list: %r", this_device.objectList)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")

