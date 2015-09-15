#!/usr/bin/python

"""
This sample application provides a single MultiState Value Object to test
reading and writing its various properties.
"""

from bacpypes.debugging import ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import MultiStateValueObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None

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
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a multistate value object
    msvo = MultiStateValueObject(
        objectIdentifier=('multiStateValue', 1), 
        objectName='My Special Object',
        presentValue=1,
        numberOfStates=3,
        stateText=['red', 'green', 'blue'],
        )
    _log.debug("    - msvo: %r", msvo)

    # add it to the device
    this_application.add_object(msvo)
    _log.debug("    - object list: %r", this_device.objectList)

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")

