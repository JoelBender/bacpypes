#!/usr/bin/env python

"""
Raspberry Pi Binary Input and Output
This sample application is BACnet server running on a Rasbperry Pi that
associates a Button with a BinaryInputObject and a LED with a
BinaryOutputObject.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.basetypes import BinaryPV
from bacpypes.object import (
    BinaryInputObject,
    BinaryOutputObject,
    Property,
    register_object_type,
)
from bacpypes.errors import ExecutionError

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

from gpiozero import Button, LED

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# button number, binary input object instance number
button_list = [(2, 2)]

# LED number, binary output object instance number
led_list = [(17, 17)]

#
#   Mock classes
#

'''
# We may want to look into the mock pin class of gpiozero.
# It will allow for testing without using an RPI board.

class Button:
    def __init__(self, button_id):
        pass


class LED:
    def __init__(self, led_id):
        pass
'''

#
#   BIPresentValue
#


@bacpypes_debugging
class BIPresentValue(Property):
    def __init__(self, identifier):
        if _debug:
            BIPresentValue._debug("__init__ %r", identifier)
        Property.__init__(
            self, identifier, BinaryPV, default=False, optional=False, mutable=False
        )

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug:
            BIPresentValue._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(
                errorClass="property", errorCode="propertyIsNotAnArray"
            )
        

        ###TODO: obj._button is the Button object
        
        if _debug:
            BIPresentValue._debug("    - read button: %r", obj._button)

        if obj._button.is_pressed:
            return "active"
        
        else:
            return "inactive"

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug:
            BIPresentValue._debug(
                "WriteProperty %r %r arrayIndex=%r priority=%r direct=%r",
                obj,
                value,
                arrayIndex,
                priority,
                direct,
            )

        raise ExecutionError(errorClass="property", errorCode="writeAccessDenied")


#
#   RPiBinaryInput
#


@bacpypes_debugging
@register_object_type
class RPiBinaryInput(BinaryInputObject):

    properties = [BIPresentValue("presentValue")]

    def __init__(self, button_id, **kwargs):
        if _debug:
            RPiBinaryInput._debug("__init__ %r %r", button_id, kwargs)
        BinaryInputObject.__init__(self, **kwargs)

        # create a button object
        self._button = Button(button_id)


#
#   BOPresentValue
#


@bacpypes_debugging
class BOPresentValue(Property):
    def __init__(self, identifier):
        if _debug:
            BOPresentValue._debug("__init__ %r", identifier)
        Property.__init__(
            self, identifier, BinaryPV, default=False, optional=False, mutable=True
        )

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug:
            BOPresentValue._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(
                errorClass="property", errorCode="propertyIsNotAnArray"
            )
        

        ###TODO: obj._led is the LED object
        if _debug:
            BOPresentValue._debug("    - read led: %r", obj._led)
        
        if obj._led.value == 1:
            return "active"
        else:
            return "inactive"
        

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug:
            BOPresentValue._debug(
                "WriteProperty %r %r arrayIndex=%r priority=%r direct=%r",
                obj,
                value,
                arrayIndex,
                priority,
                direct,
            )

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(
                errorClass="property", errorCode="propertyIsNotAnArray"
            )

        ###TODO: obj._button is the Button object
        if _debug:
            BOPresentValue._debug("    - write led: %r", obj._led)

        #raise ExecutionError(errorClass="property", errorCode="writeAccessDenied")

        if value == "active":
            obj._led.on()
        elif value == "inactive":
            obj._led.off()
        else:
            ### TODO: insert correct value error. Below is a placeholder.
            print("invalid value for led. Use 'active' to turn on or 'inactive' to turn off.")


#
#   RPiBinaryOutput
#


@bacpypes_debugging
@register_object_type
class RPiBinaryOutput(BinaryOutputObject):

    properties = [BOPresentValue("presentValue")]

    def __init__(self, led_id, **kwargs):
        if _debug:
            RPiBinaryOutput._debug("__init__ %r %r", led_id, kwargs)
        BinaryOutputObject.__init__(self, **kwargs)

        # make an LED object
        self._led = LED(led_id)


#
#   __main__
#


def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=("device", int(args.ini.objectidentifier)),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
    )

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make the buttons
    for button_id, bio_id in button_list:
        bio = RPiBinaryInput(
            button_id,
            objectIdentifier=("binaryInput", bio_id),
            objectName="Button-%d" % (button_id,),
        )
        _log.debug("    - bio: %r", bio)
        this_application.add_object(bio)

    # make the LEDs
    for led_id, boo_id in led_list:
        boo = RPiBinaryOutput(
            led_id,
            objectIdentifier=("binaryOutput", boo_id),
            objectName="LED-%d" % (led_id,),
        )
        _log.debug("    - boo: %r", boo)
        this_application.add_object(boo)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
