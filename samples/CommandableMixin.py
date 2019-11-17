#!/usr/bin/env python

"""
Rebuilt Commandable
"""

from bacpypes.debugging import ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Date

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import register_object_type
from bacpypes.local.device import (
    LocalDeviceObject,
)
from bacpypes.local.object import (
    AnalogValueCmdObject,
    BinaryOutputCmdObject,
    DateValueCmdObject,
)

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# register the classes
register_object_type(LocalDeviceObject, vendor_id=999)
register_object_type(AnalogValueCmdObject, vendor_id=999)
register_object_type(BinaryOutputCmdObject, vendor_id=999)
register_object_type(DateValueCmdObject, vendor_id=999)

def main():
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a commandable analog value object, add to the device
    avo1 = AnalogValueCmdObject(objectIdentifier=("analogValue", 1), objectName="avo1")
    if _debug:
        _log.debug("    - avo1: %r", avo1)
    this_application.add_object(avo1)

    # make a commandable binary output object, add to the device
    boo1 = BinaryOutputCmdObject(
        objectIdentifier=("binaryOutput", 1),
        objectName="boo1",
        presentValue="inactive",
        relinquishDefault="inactive",
        minimumOnTime=5,  # let it warm up
        minimumOffTime=10,  # let it cool off
    )
    if _debug:
        _log.debug("    - boo1: %r", boo1)
    this_application.add_object(boo1)

    # get the current date
    today = Date().now()

    # make a commandable date value object, add to the device
    dvo1 = DateValueCmdObject(
        objectIdentifier=("dateValue", 1), objectName="dvo1", presentValue=today.value
    )
    if _debug:
        _log.debug("    - dvo1: %r", dvo1)
    this_application.add_object(dvo1)

    if _debug:
        _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
