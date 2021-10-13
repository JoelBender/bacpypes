#!/usr/bin/env python

"""
This sample application shows how to extend one of the basic objects, an Analog
Value Object in this case, to allow the object to be renamed.
"""

from bacpypes.debugging import ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.object import AnalogValueObject, BinaryValueObject, register_object_type

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.object import WriteableObjectNameMixIn, WriteableObjectIdentifierMixIn

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Analog Value Object that can be renamed
#


@register_object_type
class SampleAnalogValueObject(WriteableObjectNameMixIn, AnalogValueObject):
    def __init__(self, **kwargs):
        if _debug:
            SampleAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

        # add a callback when the object name has changed
        self._property_monitors["objectName"].append(self.object_name_changed)

    def object_name_changed(self, old_value, new_value):
        if _debug:
            SampleAnalogValueObject._debug(
                "object_name_changed %r %r", old_value, new_value
            )
        print("object name changed from %r to %r" % (old_value, new_value))


#
#   Binary Value Object that can be given a new object identifier
#


@register_object_type
class SampleBinaryValueObject(WriteableObjectIdentifierMixIn, BinaryValueObject):
    def __init__(self, **kwargs):
        if _debug:
            SampleBinaryValueObject._debug("__init__ %r", kwargs)
        BinaryValueObject.__init__(self, **kwargs)

        # add a callback when the object name has changed
        self._property_monitors["objectIdentifier"].append(self.object_identifier_changed)

    def object_identifier_changed(self, old_value, new_value):
        if _debug:
            SampleBinaryValueObject._debug(
                "object_identifier_changed %r %r", old_value, new_value
            )
        print("object identifier changed from %r to %r" % (old_value, new_value))


#
#   __main__
#


def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
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

    # make some objects
    savo = SampleAnalogValueObject(
        objectIdentifier=("analogValue", 1),
        objectName="SampleAnalogValueObject",
        presentValue=123.4,
    )
    _log.debug("    - savo: %r", savo)

    this_application.add_object(savo)

    # make some objects
    sbvo = SampleBinaryValueObject(
        objectIdentifier=("binaryValue", 1),
        objectName="SampleBinaryValueObject",
        presentValue=True,
    )
    _log.debug("    - sbvo: %r", sbvo)

    this_application.add_object(sbvo)

    # make sure they are all there
    _log.debug("    - object list: %r", this_device.objectList)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
