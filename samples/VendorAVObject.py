#!/usr/bin/env python

"""
This sample application shows how to extend one of the basic objects, an Analog
Value Object in this case, to provide a present value. This type of code is used
when the application is providing a BACnet interface to a collection of data.
It assumes that almost all of the default behaviour of a BACpypes application is
sufficient.
"""

import random

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Real
from bacpypes.object import AnalogValueObject, Property, register_object_type
from bacpypes.errors import ExecutionError

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
vendor_id = 999

#
#   RandomValueProperty
#

@bacpypes_debugging
class RandomValueProperty(Property):

    def __init__(self, identifier):
        if _debug: RandomValueProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, Real, default=None, optional=True, mutable=False)

        # writing to this property changes the multiplier
        self.multiplier = 100.0

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: RandomValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # return a random value
        value = random.random() * self.multiplier
        if _debug: RandomValueProperty._debug("    - value: %r", value)

        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: RandomValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)

        # change the multiplier
        self.multiplier = value

#
#   Vendor Analog Value Object Type
#

@bacpypes_debugging
class VendorAVObject(AnalogValueObject):
    objectType = 513

    properties = [
        RandomValueProperty(5504),
        ]

    def __init__(self, **kwargs):
        if _debug: VendorAVObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

register_object_type(VendorAVObject, vendor_id=vendor_id)

#
#   main
#

@bacpypes_debugging
def main():
    global vendor_id

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
        vendorIdentifier=vendor_id,
        )

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make some objects
    ravo1 = VendorAVObject(
        objectIdentifier=(513, 1), objectName='Random1'
        )
    if _debug: _log.debug("    - ravo1: %r", ravo1)

    ravo2 = VendorAVObject(
        objectIdentifier=(513, 2), objectName='Random2'
        )
    if _debug: _log.debug("    - ravo2: %r", ravo2)

    # add it to the device
    this_application.add_object(ravo1)
    this_application.add_object(ravo2)
    if _debug: _log.debug("    - object list: %r", this_device.objectList)

    if _debug: _log.debug("running")

    run()

    if _debug: _log.debug("fini")

if __name__ == '__main__':
    main()
