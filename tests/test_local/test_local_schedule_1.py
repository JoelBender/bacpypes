#!/usr/bin/python

"""
Test Local Schedule

    so = LocalScheduleObject(
        objectIdentifier=('schedule', 1),
        objectName='Schedule 1',
        presentValue=Integer(5),
        effectivePeriod=DateRange(
            startDate=(0, 1, 1, 1),
            endDate=(254, 12, 31, 2),
            ),
        weeklySchedule=ArrayOf(DailySchedule)([
            DailySchedule(
                daySchedule=[
                    TimeValue(time=(8,0,0,0), value=Integer(8)),
                    TimeValue(time=(14,0,0,0), value=Null()),
                    TimeValue(time=(17,0,0,0), value=Integer(42)),
#                   TimeValue(time=(0,0,0,0), value=Null()),
                    ]
                ),
            ] * 7),
        scheduleDefault=Integer(0),
        )
"""

