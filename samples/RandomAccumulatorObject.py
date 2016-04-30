#!/usr/bin/python

"""
This sample application mocks up an accumulator object.
"""

import random

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Unsigned, Date, Time
from bacpypes.basetypes import DateTime
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import AccumulatorObject, Property, register_object_type
from bacpypes.errors import ExecutionError

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None

#
#   RandomUnsignedValueProperty
#

@bacpypes_debugging
class RandomUnsignedValueProperty(Property):

    def __init__(self, identifier):
        if _debug: RandomUnsignedValueProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, Unsigned, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: RandomUnsignedValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # return a random value
        value = int(random.random() * 100.0)
        if _debug: RandomUnsignedValueProperty._debug("    - value: %r", value)

        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: RandomUnsignedValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentDateTimeProperty
#

@bacpypes_debugging
class CurrentDateTimeProperty(Property):

    def __init__(self, identifier):
        if _debug: CurrentDateTimeProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, DateTime, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: CurrentDateTimeProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # get the value
        current_date = Date().now().value
        current_time = Time().now().value

        value = DateTime(date=current_date, time=current_time)
        if _debug: CurrentDateTimeProperty._debug("    - value: %r", value)

        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: CurrentDateTimeProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   Random Accumulator Object
#

@bacpypes_debugging
class RandomAccumulatorObject(AccumulatorObject):

    properties = [
        RandomUnsignedValueProperty('presentValue'),
        CurrentDateTimeProperty('valueChangeTime'),
        ]

    def __init__(self, **kwargs):
        if _debug: RandomAccumulatorObject._debug("__init__ %r", kwargs)
        AccumulatorObject.__init__(self, **kwargs)

register_object_type(RandomAccumulatorObject)

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
        objectIdentifier=('device', int(args.ini.objectidentifier)),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a random input object
    rao1 = RandomAccumulatorObject(
        objectIdentifier=('accumulator', 1),
        objectName='Random1',
        statusFlags = [0, 0, 0, 0],
        )
    _log.debug("    - rao1: %r", rao1)

    # add it to the device
    this_application.add_object(rao1)
    _log.debug("    - object list: %r", this_device.objectList)

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")

