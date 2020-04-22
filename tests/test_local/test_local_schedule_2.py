#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Local Schedule
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.primitivedata import Null, Real
from bacpypes.constructeddata import ArrayOf, ListOf
from bacpypes.basetypes import DailySchedule, DateRange, \
    DeviceObjectPropertyReference, TimeValue
from bacpypes.object import register_object_type, \
    WritableProperty, AnalogValueObject

from bacpypes.app import Application
from bacpypes.local.object import CurrentPropertyListMixIn
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.schedule import LocalScheduleObject

from ..time_machine import reset_time_machine, run_time_machine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@register_object_type(vendor_id=999)
class WritableAnalogValueObject(CurrentPropertyListMixIn, AnalogValueObject):

    properties = [
        WritableProperty('presentValue', Real),
        ]


@bacpypes_debugging
class TestLocalSchedule(unittest.TestCase):

    def test_local_schedule(self):
        if _debug: TestLocalSchedule._debug("test_local_schedule")

        # reset the time machine
        reset_time_machine(start_time="1970-01-01")

        # make a device object
        this_device = LocalDeviceObject(
            objectName="device 1",
            objectIdentifier=('device', 1),
            maxApduLengthAccepted=1024,
            segmentationSupported='segmentedBoth',
            vendorIdentifier=999,
            )

        # make a floating application, no network interface
        this_application = Application(this_device)

        # create a writeable analog value object
        avo = WritableAnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='analog value 1',
            presentValue=0.0,
            )
        _log.debug("    - avo: %r", avo)
        this_application.add_object(avo)

        # create a simple daily schedule, actually a weekly schedule with
        # every day identical
        so = LocalScheduleObject(
            objectIdentifier=('schedule', 1),
            objectName='Schedule 1',
            presentValue=Real(-1.0),
            effectivePeriod=DateRange(
                startDate=(0, 1, 1, 1),
                endDate=(254, 12, 31, 2),
                ),
            weeklySchedule=ArrayOf(DailySchedule)([
                DailySchedule(
                    daySchedule=[
                        TimeValue(time=(8,0,0,0), value=Real(8)),
                        TimeValue(time=(14,0,0,0), value=Null()),
                        TimeValue(time=(17,0,0,0), value=Real(42)),
                        ]
                    ),
                ] * 7),
            listOfObjectPropertyReferences=ListOf(DeviceObjectPropertyReference)(
                [
                    DeviceObjectPropertyReference(
                        objectIdentifier=('analogValue', 1),
                        propertyIdentifier='presentValue',
                        ),
                ],
            ),
            priorityForWriting=7,
            scheduleDefault=Real(0.0),
            )
        _log.debug("    - so: %r", so)
        this_application.add_object(so)

        # run from midnight to just after midnight the next day
        for hr, val in zip(range(0, 26), [0]*8 + [8]*6 + [0]*3 + [42]*7 + [0]):
            # let it run
            run_time_machine(stop_time="{}:00:01".format(hr))
            if _debug: TestLocalSchedule._debug("    - hr, val, pv: %s, %s, %s",
                hr, val, so.presentValue.value,
                )

            assert so.presentValue.value == val
            assert avo.presentValue == val

