#!/usr/bin/env python

"""
This sample application provides a single MultiState Value Object to test
reading and writing its various properties.
"""

from bacpypes.debugging import ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import ArrayOf
from bacpypes.object import MultiStateValueObject

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

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

    _log.debug("fini")


if __name__ == "__main__":
    main()
