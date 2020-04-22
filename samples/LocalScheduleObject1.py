#!/usr/bin/env python

"""
This application creates a series of Local Schedule Objects and then prompts
to test dates and times.
"""

from time import localtime as _localtime

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run

from bacpypes.primitivedata import Null, Integer, Real, Date, Time, CharacterString
from bacpypes.constructeddata import ArrayOf, SequenceOf
from bacpypes.basetypes import (
    CalendarEntry,
    DailySchedule,
    DateRange,
    DeviceObjectPropertyReference,
    SpecialEvent,
    SpecialEventPeriod,
    TimeValue,
)

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.schedule import LocalScheduleObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
schedule_objects = []

#
#   TestConsoleCmd
#


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

        for so in schedule_objects:
            v, t = so._task.eval(test_date, test_time)
            print(so.objectName + ", " + repr(v and v.value) + " until " + str(t))

    def do_now(self, args):
        """now"""
        args = args.split()
        if _debug:
            TestConsoleCmd._debug("do_now %r", args)

        y = _localtime()
        print("y: {}".format(y))


#
#   __main__
#


def main():
    global args, schedule_objects

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

    #
    #   Simple daily schedule (actually a weekly schedule with every day
    #   being identical.
    #
    so = LocalScheduleObject(
        objectIdentifier=("schedule", 1),
        objectName="Schedule 1",
        presentValue=Integer(8),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2),),
        weeklySchedule=[
            DailySchedule(
                daySchedule=[
                    TimeValue(time=(8, 0, 0, 0), value=Integer(8)),
                    TimeValue(time=(14, 0, 0, 0), value=Null()),
                    TimeValue(time=(17, 0, 0, 0), value=Integer(42)),
                    # TimeValue(time=(0,0,0,0), value=Null()),
                ]
            ),
        ]
        * 7,
        scheduleDefault=Integer(0),
    )
    _log.debug("    - so: %r", so)
    this_application.add_object(so)
    schedule_objects.append(so)

    #
    #   A special schedule when the Year 2000 problem was supposed to collapse
    #   systems, the panic clears ten minutes later when it didn't.
    #
    so = LocalScheduleObject(
        objectIdentifier=("schedule", 2),
        objectName="Schedule 2",
        presentValue=CharacterString(""),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2),),
        exceptionSchedule=[
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(date=Date("2000-01-01").value,),
                ),
                listOfTimeValues=[
                    TimeValue(time=(0, 0, 0, 0), value=CharacterString("Panic!")),
                    TimeValue(time=(0, 10, 0, 0), value=Null()),
                ],
                eventPriority=1,
            ),
        ],
        scheduleDefault=CharacterString("Don't panic."),
    )
    _log.debug("    - so: %r", so)
    this_application.add_object(so)
    schedule_objects.append(so)

    #
    #   A special schedule to celebrate Friday.
    #
    so = LocalScheduleObject(
        objectIdentifier=("schedule", 3),
        objectName="Schedule 3",
        presentValue=CharacterString(""),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2),),
        exceptionSchedule=[
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.05"),),
                ),
                listOfTimeValues=[
                    TimeValue(time=(0, 0, 0, 0), value=CharacterString("It's Friday!")),
                ],
                eventPriority=1,
            ),
        ],
        scheduleDefault=CharacterString("Keep working."),
    )
    _log.debug("    - so: %r", so)
    this_application.add_object(so)
    schedule_objects.append(so)

    #
    #   A schedule object that refers to an AnalogValueObject in the test
    #   device.
    #
    so = LocalScheduleObject(
        objectIdentifier=("schedule", 4),
        objectName="Schedule 4",
        presentValue=Real(73.5),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2),),
        weeklySchedule=[
            DailySchedule(
                daySchedule=[
                    TimeValue(time=(9, 0, 0, 0), value=Real(78.0)),
                    TimeValue(time=(10, 0, 0, 0), value=Null()),
                ]
            ),
        ]
        * 7,
        scheduleDefault=Real(72.0),
        listOfObjectPropertyReferences=SequenceOf(DeviceObjectPropertyReference)(
            [
                DeviceObjectPropertyReference(
                    objectIdentifier=("analogValue", 1),
                    propertyIdentifier="presentValue",
                ),
            ]
        ),
    )
    _log.debug("    - so: %r", so)
    this_application.add_object(so)
    schedule_objects.append(so)

    #
    #   The beast
    #
    so = LocalScheduleObject(
        objectIdentifier=("schedule", 5),
        objectName="Schedule 5",
        presentValue=Integer(0),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2),),
        exceptionSchedule=[
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.FF"),),
                ),
                listOfTimeValues=[
                    TimeValue(time=(5, 0, 0, 0), value=Integer(5)),
                    TimeValue(time=(6, 0, 0, 0), value=Null()),
                ],
                eventPriority=1,
            ),
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.FF"),),
                ),
                listOfTimeValues=[
                    TimeValue(time=(4, 0, 0, 0), value=Integer(4)),
                    TimeValue(time=(7, 0, 0, 0), value=Null()),
                ],
                eventPriority=2,
            ),
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.FF"),),
                ),
                listOfTimeValues=[
                    TimeValue(time=(3, 0, 0, 0), value=Integer(3)),
                    TimeValue(time=(8, 0, 0, 0), value=Null()),
                ],
                eventPriority=3,
            ),
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.FF"),),
                ),
                listOfTimeValues=[
                    TimeValue(time=(2, 0, 0, 0), value=Integer(2)),
                    TimeValue(time=(9, 0, 0, 0), value=Null()),
                ],
                eventPriority=4,
            ),
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.FF"),),
                ),
                listOfTimeValues=[TimeValue(time=(1, 0, 0, 0), value=Integer(1)),],
                eventPriority=5,
            ),
        ],
        scheduleDefault=Integer(0),
    )
    _log.debug("    - so: %r", so)
    this_application.add_object(so)
    schedule_objects.append(so)

    # list of time values for every five minutes
    ltv = []
    for hr in range(24):
        for mn in range(0, 60, 5):
            ltv.append(TimeValue(time=(hr, mn, 0, 0), value=Integer(hr * 100 + mn)))

    so = LocalScheduleObject(
        objectIdentifier=("schedule", 6),
        objectName="Schedule 6",
        presentValue=Integer(0),
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2),),
        exceptionSchedule=[
            SpecialEvent(
                period=SpecialEventPeriod(
                    calendarEntry=CalendarEntry(weekNDay=xtob("FF.FF.FF"),),
                ),
                listOfTimeValues=ltv,
                eventPriority=1,
            ),
        ],
        scheduleDefault=Integer(0),
    )
    _log.debug("    - so: %r", so)
    this_application.add_object(so)
    schedule_objects.append(so)

    # make sure they are all there
    _log.debug("    - object list: %r", this_device.objectList)

    TestConsoleCmd()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
