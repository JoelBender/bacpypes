#!/usr/bin/env python

"""
This sample application is a server that supports COV notification services.
The console accepts commands that change the properties of an object that
triggers the notifications.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import AnalogValueObject, BinaryValueObject
from bacpypes.service.device import LocalDeviceObject
from bacpypes.service.cov import ChangeOfValueServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# test globals
test_application = None

#
#   SubscribeCOVApplication
#

@bacpypes_debugging
class SubscribeCOVApplication(BIPSimpleApplication, ChangeOfValueServices):
    pass

#
#   COVConsoleCmd
#

@bacpypes_debugging
class COVConsoleCmd(ConsoleCmd):

    def do_status(self, args):
        """status"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_status %r", args)
        global test_application

        # reference the list of active subscriptions
        active_subscriptions = test_application.active_cov_subscriptions
        if _debug: COVConsoleCmd._debug("    - %d active subscriptions", len(active_subscriptions))

        # dump then out
        for subscription in active_subscriptions:
            print("{} {} {} {} {}".format(
                subscription.client_addr,
                subscription.proc_id,
                subscription.obj_id,
                subscription.confirmed,
                subscription.lifetime,
                ))

        # reference the object to algorithm map
        object_detections = test_application.object_detections
        for objref, cov_detection in object_detections.items():
            print("{} {}".format(
                objref.objectIdentifier,
                cov_detection,
                ))

    def do_trigger(self, args):
        """trigger object_name"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_trigger %r", args)
        global test_application

        if not args:
            print("object name required")
            return

        obj = test_application.get_object_name(args[0])
        if not obj:
            print("no such object")
            return

        # get the detection algorithm object
        cov_detection = test_application.cov_detections.get(obj, None)
        if (not cov_detection) or (len(cov_detection.cov_subscriptions) == 0):
            print("no subscriptions for that object")
            return

        # tell it to send out notifications
        cov_detection.send_cov_notifications()

    def do_set(self, args):
        """set object_name [ . ] property_name [ = ] value"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_set %r", args)
        global test_application

        try:
            object_name = args.pop(0)
            if '.' in object_name:
                object_name, property_name = object_name.split('.')
            else:
                property_name = args.pop(0)
            if _debug: COVConsoleCmd._debug("    - object_name: %r", object_name)
            if _debug: COVConsoleCmd._debug("    - property_name: %r", property_name)

            obj = test_application.get_object_name(object_name)
            if _debug: COVConsoleCmd._debug("    - obj: %r", obj)
            if not obj:
                raise RuntimeError("object not found: %r" % (object_name,))

            datatype = obj.get_datatype(property_name)
            if _debug: COVConsoleCmd._debug("    - datatype: %r", datatype)
            if not datatype:
                raise RuntimeError("not a property: %r" % (property_name,))

            # toss the equals
            if args[0] == '=':
                args.pop(0)

            # evaluate the value
            value = eval(args.pop(0))
            if _debug: COVConsoleCmd._debug("    - raw value: %r", value)

            # see if it can be built
            obj_value = datatype(value)
            if _debug: COVConsoleCmd._debug("    - obj_value: %r", obj_value)

            # normalize
            value = obj_value.value
            if _debug: COVConsoleCmd._debug("    - normalized value: %r", value)

            # change the value
            setattr(obj, property_name, value)

        except IndexError:
            print(COVConsoleCmd.do_set.__doc__)
        except Exception as err:
            print("exception: %s" % (err,))

    def do_write(self, args):
        """write object_name [ . ] property [ = ] value"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_set %r", args)
        global test_application

        try:
            object_name = args.pop(0)
            if '.' in object_name:
                object_name, property_name = object_name.split('.')
            else:
                property_name = args.pop(0)
            if _debug: COVConsoleCmd._debug("    - object_name: %r", object_name)
            if _debug: COVConsoleCmd._debug("    - property_name: %r", property_name)

            obj = test_application.get_object_name(object_name)
            if _debug: COVConsoleCmd._debug("    - obj: %r", obj)
            if not obj:
                raise RuntimeError("object not found: %r" % (object_name,))

            datatype = obj.get_datatype(property_name)
            if _debug: COVConsoleCmd._debug("    - datatype: %r", datatype)
            if not datatype:
                raise RuntimeError("not a property: %r" % (property_name,))

            # toss the equals
            if args[0] == '=':
                args.pop(0)

            # evaluate the value
            value = eval(args.pop(0))
            if _debug: COVConsoleCmd._debug("    - raw value: %r", value)

            # see if it can be built
            obj_value = datatype(value)
            if _debug: COVConsoleCmd._debug("    - obj_value: %r", obj_value)

            # normalize
            value = obj_value.value
            if _debug: COVConsoleCmd._debug("    - normalized value: %r", value)

            # pass it along
            obj.WriteProperty(property_name, value)

        except IndexError:
            print(COVConsoleCmd.do_write.__doc__)
        except Exception as err:
            print("exception: %s" % (err,))


def main():
    global test_application

    # make a parser
    parser = ConfigArgumentParser(description=__doc__)
    parser.add_argument("--console",
        action="store_true",
        default=False,
        help="create a console",
        )

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

    # make a sample application
    test_application = SubscribeCOVApplication(test_device, args.ini.address)

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
    if args.console:
        test_console = COVConsoleCmd()
        _log.debug("    - test_console: %r", test_console)

        # enable sleeping will help with threads
        enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
