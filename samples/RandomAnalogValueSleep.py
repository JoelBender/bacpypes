#!/usr/bin/env python

"""
Random Value Property with Sleep

This application is a server of analog value objects that return a random
number when the present value is read.  This version has an additional
'sleep' time that slows down its performance.
"""

import os
import random
import time

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Real
from bacpypes.object import AnalogValueObject, Property, register_object_type
from bacpypes.errors import ExecutionError

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
SLEEP_TIME = float(os.getenv('SLEEP_TIME', 0.1))
RANDOM_OBJECT_COUNT = int(os.getenv('RANDOM_OBJECT_COUNT', 10))

# globals
args = None

#
#   RandomValueProperty
#

class RandomValueProperty(Property):

    def __init__(self, identifier):
        if _debug: RandomValueProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, Real, default=0.0, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: RandomValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)
        global args

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # sleep a little
        time.sleep(args.sleep)

        # return a random value
        value = random.random() * 100.0
        if _debug: RandomValueProperty._debug("    - value: %r", value)

        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: RandomValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

bacpypes_debugging(RandomValueProperty)

#
#   Random Value Object Type
#

class RandomAnalogValueObject(AnalogValueObject):

    properties = [
        RandomValueProperty('presentValue'),
        ]

    def __init__(self, **kwargs):
        if _debug: RandomAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

bacpypes_debugging(RandomAnalogValueObject)
register_object_type(RandomAnalogValueObject)

#
#   __main__
#

def main():
    global args

    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an option to override the sleep time
    parser.add_argument('--sleep', type=float,
        help="sleep before returning the value",
        default=SLEEP_TIME,
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make some random input objects
    for i in range(1, RANDOM_OBJECT_COUNT+1):
        ravo = RandomAnalogValueObject(
            objectIdentifier=('analogValue', i),
            objectName='Random-%d' % (i,),
            )
        _log.debug("    - ravo: %r", ravo)
        this_application.add_object(ravo)

    # make sure they are all there
    _log.debug("    - object list: %r", this_device.objectList)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
