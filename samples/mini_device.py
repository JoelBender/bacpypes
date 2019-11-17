#!/usr/bin/python

"""
This sample application is a server that supports many core services that
applications need to present data on a BACnet network.  It supports Who-Is
and I-Am for device binding, Read and Write Property, Read and Write
Property Multiple, and COV subscriptions.

Change the process_task() function to do something on a regular INTERVAL
number of seconds.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.task import RecurringTask

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import AnalogValueObject, BinaryValueObject
from bacpypes.local.device import LocalDeviceObject
from bacpypes.service.cov import ChangeOfValueServices
from bacpypes.service.object import ReadWritePropertyMultipleServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
INTERVAL = 1.0

# globals
test_application = None
test_av = None
test_bv = None


@bacpypes_debugging
class SampleApplication(
    BIPSimpleApplication, ReadWritePropertyMultipleServices, ChangeOfValueServices
):
    pass


@bacpypes_debugging
class DoSomething(RecurringTask):
    def __init__(self, interval):
        if _debug:
            DoSomething._debug("__init__ %r", interval)
        RecurringTask.__init__(self, interval * 1000)

        # save the interval
        self.interval = interval

        # make a list of test values
        self.test_values = [
            ("active", 1.0),
            ("inactive", 2.0),
            ("active", 3.0),
            ("inactive", 4.0),
        ]

    def process_task(self):
        if _debug:
            DoSomething._debug("process_task")
        global test_av, test_bv

        # pop the next value
        next_value = self.test_values.pop(0)
        self.test_values.append(next_value)
        if _debug:
            DoSomething._debug("    - next_value: %r", next_value)

        # change the point
        test_av.presentValue = next_value[1]
        test_bv.presentValue = next_value[0]


def main():
    global test_av, test_bv, test_application

    # make a parser
    parser = ConfigArgumentParser(description=__doc__)

    # parse the command line arguments
    args = parser.parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a sample application
    test_application = SampleApplication(this_device, args.ini.address)

    # make an analog value object
    test_av = AnalogValueObject(
        objectIdentifier=("analogValue", 1),
        objectName="av",
        presentValue=0.0,
        statusFlags=[0, 0, 0, 0],
        covIncrement=1.0,
    )
    _log.debug("    - test_av: %r", test_av)

    # add it to the device
    test_application.add_object(test_av)
    _log.debug("    - object list: %r", this_device.objectList)

    # make a binary value object
    test_bv = BinaryValueObject(
        objectIdentifier=("binaryValue", 1),
        objectName="bv",
        presentValue="inactive",
        statusFlags=[0, 0, 0, 0],
    )
    _log.debug("    - test_bv: %r", test_bv)

    # add it to the device
    test_application.add_object(test_bv)

    # binary value task
    do_something_task = DoSomething(INTERVAL)
    do_something_task.install_task()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
