#!/usr/bin/env python

"""
This sample application is a server that supports COV notification services.
The console accepts commands that change the properties of an object that
triggers the notifications.
"""

import time
from threading import Thread

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.task import RecurringTask

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import AnalogValueObject, BinaryValueObject
from bacpypes.local.device import LocalDeviceObject
from bacpypes.service.cov import ChangeOfValueServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# test globals
test_av = None
test_bv = None
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

        # dump from the COV detections dict
        for obj_ref, cov_detection in test_application.cov_detections.items():
            print("{} {}".format(obj_ref.objectIdentifier, obj_ref))

            for cov_subscription in cov_detection.cov_subscriptions:
                print("    {} proc_id={} confirmed={} lifetime={}".format(
                    cov_subscription.client_addr,
                    cov_subscription.proc_id,
                    cov_subscription.confirmed,
                    cov_subscription.lifetime,
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


@bacpypes_debugging
class TestAnalogValueTask(RecurringTask):

    """
    An instance of this class is created when '--avtask <interval>' is
    specified as a command line argument.  Every <interval> seconds it
    changes the value of the test_av present value.
    """

    def __init__(self, interval):
        if _debug: TestAnalogValueTask._debug("__init__ %r", interval)
        RecurringTask.__init__(self, interval * 1000)

        # make a list of test values
        self.test_values = list(float(i * 10) for i in range(10))

    def process_task(self):
        if _debug: TestAnalogValueTask._debug("process_task")
        global test_av

        # pop the next value
        next_value = self.test_values.pop(0)
        self.test_values.append(next_value)
        if _debug: TestAnalogValueTask._debug("    - next_value: %r", next_value)

        # change the point
        test_av.presentValue = next_value


@bacpypes_debugging
class TestAnalogValueThread(Thread):

    """
    An instance of this class is created when '--avthread <interval>' is
    specified as a command line argument.  Every <interval> seconds it
    changes the value of the test_av present value.
    """

    def __init__(self, interval):
        if _debug: TestAnalogValueThread._debug("__init__ %r", interval)
        Thread.__init__(self)

        # runs as a daemon
        self.daemon = True

        # save the interval
        self.interval = interval

        # make a list of test values
        self.test_values = list(100.0 + float(i * 10) for i in range(10))

    def run(self):
        if _debug: TestAnalogValueThread._debug("run")
        global test_av

        while True:
            # pop the next value
            next_value = self.test_values.pop(0)
            self.test_values.append(next_value)
            if _debug: TestAnalogValueThread._debug("    - next_value: %r", next_value)

            # change the point
            test_av.presentValue = next_value

            # sleep
            time.sleep(self.interval)


@bacpypes_debugging
class TestBinaryValueTask(RecurringTask):

    """
    An instance of this class is created when '--bvtask <interval>' is
    specified as a command line argument.  Every <interval> seconds it
    changes the value of the test_bv present value.
    """

    def __init__(self, interval):
        if _debug: TestBinaryValueTask._debug("__init__ %r", interval)
        RecurringTask.__init__(self, interval * 1000)

        # save the interval
        self.interval = interval

        # make a list of test values
        self.test_values = [True, False]

    def process_task(self):
        if _debug: TestBinaryValueTask._debug("process_task")
        global test_bv

        # pop the next value
        next_value = self.test_values.pop(0)
        self.test_values.append(next_value)
        if _debug: TestBinaryValueTask._debug("    - next_value: %r", next_value)

        # change the point
        test_bv.presentValue = next_value


@bacpypes_debugging
class TestBinaryValueThread(RecurringTask, Thread):

    """
    An instance of this class is created when '--bvthread <interval>' is
    specified as a command line argument.  Every <interval> seconds it
    changes the value of the test_bv present value.
    """

    def __init__(self, interval):
        if _debug: TestBinaryValueThread._debug("__init__ %r", interval)
        Thread.__init__(self)

        # runs as a daemon
        self.daemon = True

        # save the interval
        self.interval = interval

        # make a list of test values
        self.test_values = [True, False]

    def run(self):
        if _debug: TestBinaryValueThread._debug("run")
        global test_bv

        while True:
            # pop the next value
            next_value = self.test_values.pop(0)
            self.test_values.append(next_value)
            if _debug: TestBinaryValueThread._debug("    - next_value: %r", next_value)

            # change the point
            test_bv.presentValue = next_value

            # sleep
            time.sleep(self.interval)


def main():
    global test_av, test_bv, test_application

    # make a parser
    parser = ConfigArgumentParser(description=__doc__)
    parser.add_argument("--console",
        action="store_true",
        default=False,
        help="create a console",
        )

    # analog value task and thread
    parser.add_argument("--avtask", type=float,
        help="analog value recurring task",
        )
    parser.add_argument("--avthread", type=float,
        help="analog value thread",
        )

    # analog value task and thread
    parser.add_argument("--bvtask", type=float,
        help="binary value recurring task",
        )
    parser.add_argument("--bvthread", type=float,
        help="binary value thread",
        )

    # provide a different spin value
    parser.add_argument("--spin", type=float,
        help="spin time",
        default=1.0,
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a sample application
    test_application = SubscribeCOVApplication(this_device, args.ini.address)

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
    _log.debug("    - object list: %r", this_device.objectList)

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

    # make a console
    if args.console:
        test_console = COVConsoleCmd()
        _log.debug("    - test_console: %r", test_console)

        # enable sleeping will help with threads
        enable_sleeping()

    # analog value task
    if args.avtask:
        test_av_task = TestAnalogValueTask(args.avtask)
        test_av_task.install_task()

    # analog value thread
    if args.avthread:
        test_av_thread = TestAnalogValueThread(args.avthread)
        deferred(test_av_thread.start)

    # binary value task
    if args.bvtask:
        test_bv_task = TestBinaryValueTask(args.bvtask)
        test_bv_task.install_task()

    # binary value thread
    if args.bvthread:
        test_bv_thread = TestBinaryValueThread(args.bvthread)
        deferred(test_bv_thread.start)

    _log.debug("running")

    run(args.spin)

    _log.debug("fini")


if __name__ == "__main__":
    main()
