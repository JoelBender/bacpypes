#!/usr/bin/env python

"""
This sample application is a server with console commands that change the
properties of an object.  It can be used in conjunction with the
ReadWriteProperty.py application.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import AnalogValueObject, BinaryValueObject
from bacpypes.primitivedata import Enumerated
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# test globals
test_application = None

#
#   RWPConsoleCmd
#

@bacpypes_debugging
class RWPConsoleCmd(ConsoleCmd):

    def do_get(self, args):
        """get object_name [ . ] property_name"""
        args = args.split()
        if _debug: RWPConsoleCmd._debug("do_set %r", args)
        global test_application

        try:
            object_name = args.pop(0)
            if '.' in object_name:
                object_name, property_name = object_name.split('.')
            else:
                property_name = args.pop(0)
            if _debug: RWPConsoleCmd._debug("    - object_name: %r", object_name)
            if _debug: RWPConsoleCmd._debug("    - property_name: %r", property_name)

            obj = test_application.get_object_name(object_name)
            if _debug: RWPConsoleCmd._debug("    - obj: %r", obj)
            if not obj:
                raise RuntimeError("object not found: %r" % (object_name,))

            # print the value
            print(repr(getattr(obj, property_name)))

        except IndexError:
            print(RWPConsoleCmd.do_set.__doc__)
        except Exception as err:
            print("exception: %s" % (err,))

    def do_set(self, args):
        """set object_name [ . ] property_name [ = ] value"""
        args = args.split()
        if _debug: RWPConsoleCmd._debug("do_set %r", args)
        global test_application

        try:
            object_name = args.pop(0)
            if '.' in object_name:
                object_name, property_name = object_name.split('.')
            else:
                property_name = args.pop(0)
            if _debug: RWPConsoleCmd._debug("    - object_name: %r", object_name)
            if _debug: RWPConsoleCmd._debug("    - property_name: %r", property_name)

            obj = test_application.get_object_name(object_name)
            if _debug: RWPConsoleCmd._debug("    - obj: %r", obj)
            if not obj:
                raise RuntimeError("object not found: %r" % (object_name,))

            datatype = obj.get_datatype(property_name)
            if _debug: RWPConsoleCmd._debug("    - datatype: %r", datatype)
            if not datatype:
                raise RuntimeError("not a property: %r" % (property_name,))

            # toss the equals
            if args[0] == '=':
                args.pop(0)

            # see if it's enumerate
            if issubclass(datatype, Enumerated):
                value = args.pop(0)
                if value.isdigit():
                    value = int(value)
                    if _debug: RWPConsoleCmd._debug("    - integer value: %r", value)
                elif value not in datatype.enumerations:
                    raise ValueError("must be a enumeration value: " + ', '.join(datatype.enumerations.keys()))
            else:
                # evaluate the value
                value = eval(args.pop(0))
                if _debug: RWPConsoleCmd._debug("    - raw value: %r", value)

                # see if it can be built
                obj_value = datatype(value)
                if _debug: RWPConsoleCmd._debug("    - obj_value: %r", obj_value)

                # normalize
                value = obj_value.value
                if _debug: RWPConsoleCmd._debug("    - normalized value: %r", value)

            # change the value
            setattr(obj, property_name, value)

        except IndexError:
            print(RWPConsoleCmd.do_set.__doc__)
        except Exception as err:
            print("exception: %s" % (err,))


def main():
    global test_application

    # make a parser
    parser = ConfigArgumentParser(description=__doc__)

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    test_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a simple application
    test_application = BIPSimpleApplication(test_device, args.ini.address)

    # make a binary value object
    test_bv = BinaryValueObject(
        objectIdentifier=('binaryValue', 1),
        objectName='bv',
        presentValue='inactive',
        statusFlags=[0, 0, 0, 0],
        )
    _log.debug("    - test_bv: %r", test_bv)

    # add it to the device
    test_application.add_object(test_bv)

    # make an analog value object
    test_av = AnalogValueObject(
        objectIdentifier=('analogValue', 1),
        objectName='av',
        presentValue=0.0,
        statusFlags=[0, 0, 0, 0],
        covIncrement=1.0,
        )
    _log.debug("    - test_av: %r", test_av)

    # add it to the device
    test_application.add_object(test_av)
    _log.debug("    - object list: %r", test_device.objectList)

    # get the services supported
    services_supported = test_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    test_device.protocolServicesSupported = services_supported.value

    # make a console
    test_console = RWPConsoleCmd()
    _log.debug("    - test_console: %r", test_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
