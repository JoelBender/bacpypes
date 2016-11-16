#!/usr/bin/env python

"""
This sample application mocks up an accumulator object.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.task import RecurringTask

from bacpypes.primitivedata import Date, Time
from bacpypes.basetypes import DateTime, Scale
from bacpypes.object import AccumulatorObject

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject
from bacpypes.service.object import ReadWritePropertyMultipleServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   PulseTask
#

class PulseTask(RecurringTask):

    def __init__(self, accumulator, increment, interval):
        if _debug: PulseTask._debug("__init__ %r %r %r", accumulator, increment, interval)

        # this is a recurring task
        RecurringTask.__init__(self, interval)

        # install it
        self.install_task()

        # save the parameters
        self.accumulator = accumulator
        self.increment = increment

    def process_task(self):
        if _debug: PulseTask._debug("process_task")

        # increment the present value
        self.accumulator.presentValue += self.increment

        # update the value change time
        current_date = Date().now().value
        current_time = Time().now().value

        value_change_time = DateTime(date=current_date, time=current_time)
        if _debug: PulseTask._debug("    - value_change_time: %r", value_change_time)

        self.accumulator.valueChangeTime = value_change_time

bacpypes_debugging(PulseTask)

#
#   __main__
#

def main():
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

    # add the additional service
    this_application.add_capability(ReadWritePropertyMultipleServices)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a random input object
    accumulator = AccumulatorObject(
        objectIdentifier=('accumulator', 1),
        objectName='Something1',
        presentValue=100,
        statusFlags = [0, 0, 0, 0],
        eventState='normal',
        scale=Scale(floatScale=2.3),
        units='btusPerPoundDryAir',
        )
    if _debug: _log.debug("    - accumulator: %r", accumulator)

    # add it to the device
    this_application.add_object(accumulator)
    if _debug: _log.debug("    - object list: %r", this_device.objectList)

    # create a task that bumps the value by one every 10 seconds
    pulse_task = PulseTask(accumulator, 1, 10 * 1000)
    if _debug: _log.debug("    - pulse_task: %r", pulse_task)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
