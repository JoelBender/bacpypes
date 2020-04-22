#!/usr/bin/env python

"""
This sample application shows how to extend the basic functionality of a device
to support the ReadPropertyMultiple service.
"""

import random

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Real, CharacterString
from bacpypes.constructeddata import ArrayOf
from bacpypes.object import AnalogValueObject, Property, register_object_type
from bacpypes.errors import ExecutionError

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import DeviceCommunicationControlServices
from bacpypes.service.object import ReadWritePropertyMultipleServices
from bacpypes.local.device import LocalDeviceObject


# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   ReadPropertyMultipleApplication
#

@bacpypes_debugging
class ReadPropertyMultipleApplication(
        BIPSimpleApplication,
        ReadWritePropertyMultipleServices,
        DeviceCommunicationControlServices,
        ):
    pass

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
        Property('eventMessageTexts', ArrayOf(CharacterString), mutable=True),
        ]

    def __init__(self, **kwargs):
        if _debug: RandomAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

register_object_type(RandomAnalogValueObject)

#
#   __main__
#

def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a sample application
    this_application = ReadPropertyMultipleApplication(this_device, args.ini.address)

    # make a random input object
    ravo1 = RandomAnalogValueObject(
        objectIdentifier=('analogValue', 1), objectName='Random1',
        eventMessageTexts=["infinity", "and", "beyond"],
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

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
