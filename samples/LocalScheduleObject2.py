#!/usr/bin/env python

"""
This application creates a Local Schedule Objects and then prompts
to test dates and times.
"""

from time import localtime as _localtime

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run

from bacpypes.primitivedata import Null, Real, Date, Time
from bacpypes.constructeddata import ArrayOf, ListOf
from bacpypes.basetypes import (
    CalendarEntry,
    DailySchedule,
    DateRange,
    DeviceObjectPropertyReference,
    SpecialEvent,
    SpecialEventPeriod,
    TimeValue,
)
from bacpypes.object import register_object_type, WritableProperty, AnalogValueObject

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.object import CurrentPropertyListMixIn
from bacpypes.local.schedule import LocalScheduleObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
test_analog_value = None
test_schedule = None


@register_object_type(vendor_id=999)
class WritableAnalogValueObject(CurrentPropertyListMixIn, AnalogValueObject):

    properties = [WritableProperty("presentValue", Real)]


@bacpypes_debugging
def analog_value_changed(old_value, new_value):
    if _debug:
        TestConsoleCmd._debug("analog_value_changed %r %r", old_value, new_value)
    print("analog value changed from {!r} to {!r}".format(old_value, new_value))


@bacpypes_debugging
class TestConsoleCmd(ConsoleCmd):
    def do_test(self, args):
        """test <date> <time>"""
        args = args.split()
        if _debug:
            TestConsoleCmd._debug("do_test %r", args)

        date_string, time_string = args
        test_date = Date(date_string).value
        test_time = Time(time_string).value

        v, t = test_schedule._task.eval(test_date, test_time)
        print(
            test_schedule.objectName + ", " + repr(v and v.value) + " until " + str(t)
        )

    def do_except(self, args):
        """except <date> <start> <stop>"""
        args = args.split()
        if _debug:
            TestConsoleCmd._debug("do_except %r", args)

        date_string, start_string, stop_string = args
        except_date = Date(date_string).value
        start_time = Time(start_string).value
        stop_time = Time(stop_string).value

        exception_schedule = [
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(date=except_date)
                ),
                listOfTimeValues=[
                    TimeValue(time=start_time, value=Real(999.0)),
                    TimeValue(time=stop_time, value=Null()),
                ],
                eventPriority=1,
            )
        ]
        if _debug:
            TestConsoleCmd._debug("    - exception_schedule: %r", exception_schedule)

        # new exception
        test_schedule.exceptionSchedule = exception_schedule

    def do_now(self, args):
        """now"""
        args = args.split()
        if _debug:
            TestConsoleCmd._debug("do_now %r", args)

        print("test analog value: %r" % (test_analog_value.presentValue,))
        print("test schedule: %r" % (test_schedule.presentValue.value,))


def main():
    global args, test_analog_value, test_schedule

    # parse the command line arguments
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
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # create a writeable analog value object
    test_analog_value = WritableAnalogValueObject(
        objectIdentifier=("analogValue", 1),
        objectName="Test Analog Value",
        presentValue=0.0,
    )
    _log.debug("    - test_analog_value: %r", test_analog_value)
    this_application.add_object(test_analog_value)

    # print when the value changes
    test_analog_value._property_monitors["presentValue"].append(analog_value_changed)

    #
    #   Simple daily schedule (actually a weekly schedule with every day
    #   being identical.
    #
    test_schedule = LocalScheduleObject(
        objectIdentifier=("schedule", 1),
        objectName="Test Schedule",
        presentValue=Real(8.0),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2)),
        weeklySchedule=[
            DailySchedule(
                daySchedule=[
                    TimeValue(time=(8, 0, 0, 0), value=Real(8.0)),
                    TimeValue(time=(14, 0, 0, 0), value=Null()),
                    TimeValue(time=(17, 0, 0, 0), value=Real(42.0)),
                ]
            )
        ]
        * 7,
        listOfObjectPropertyReferences=ListOf(DeviceObjectPropertyReference)(
            [
                DeviceObjectPropertyReference(
                    objectIdentifier=("analogValue", 1),
                    propertyIdentifier="presentValue",
                )
            ]
        ),
        scheduleDefault=Real(0.0),
    )
    _log.debug("    - test_schedule: %r", test_schedule)
    this_application.add_object(test_schedule)

    TestConsoleCmd()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
