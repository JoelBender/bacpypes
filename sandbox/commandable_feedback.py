#!/usr/bin/env python

"""
Commandable Feedback
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.basetypes import StatusFlags

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import register_object_type
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.object import BinaryOutputCmdObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# register the classes
register_object_type(LocalDeviceObject, vendor_id=999)


@bacpypes_debugging
@register_object_type(vendor_id=999)
class BinaryOutputFeedbackObject(BinaryOutputCmdObject):
    def __init__(self, *args, **kwargs):
        if _debug:
            BinaryOutputFeedbackObject._debug("__init__ %r %r", args, kwargs)
        super().__init__(*args, **kwargs)

        # listen for changes to the present value
        self._property_monitors["presentValue"].append(self.check_feedback)

    def check_feedback(self, old_value, new_value):
        if _debug:
            BinaryOutputFeedbackObject._debug(
                "check_feedback %r %r", old_value, new_value
            )

        # this is violation of 12.7.8 because the object does not support
        # event reporting, but it is here for illustration
        if new_value == self.feedbackValue:
            self.eventState = "normal"
            self.statusFlags["inAlarm"] = False
        else:
            self.eventState = "offnormal"
            self.statusFlags["inAlarm"] = True


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

    # make a commandable binary output object, add to the device
    boo1 = BinaryOutputFeedbackObject(
        objectIdentifier=("binaryOutput", 1),
        objectName="boo1",
        presentValue="inactive",
        eventState="normal",
        statusFlags=StatusFlags(),
        feedbackValue="inactive",
        relinquishDefault="inactive",
        minimumOnTime=5,  # let it warm up
        minimumOffTime=10,  # let it cool off
    )
    if _debug:
        _log.debug("    - boo1: %r", boo1)
    this_application.add_object(boo1)

    if _debug:
        _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
