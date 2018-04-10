#!/usr/bin/python

"""
Muteable Schedule Object
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import ArrayOf
from bacpypes.basetypes import DailySchedule
from bacpypes.object import WritableProperty, ScheduleObject, register_object_type

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   MyScheduleObject
#

@bacpypes_debugging
@register_object_type(vendor_id=999)
class MyScheduleObject(ScheduleObject):

    properties = [
        WritableProperty('weeklySchedule', ArrayOf(DailySchedule)),
        WritableProperty('priorityForWriting', Unsigned),
        ]

    def __init__(self, **kwargs):
        if _debug: MyScheduleObject._debug("__init__ %r", kwargs)
        ScheduleObject.__init__(self, **kwargs)

#
#
#

# parse the command line arguments
parser = ArgumentParser(usage=__doc__)
args = parser.parse_args()

if _debug: _log.debug("initialization")
if _debug: _log.debug("    - args: %r", args)

# create a schedule object
mso = MyScheduleObject(
    objectIdentifier=('schedule', 1),
    objectName="myScheduleObject",
    weeklySchedule=[],
    priorityForWriting=1,
    )

print("getting value")
print(mso.priorityForWriting)
print("")

print("setting value")
mso.priorityForWriting = 2
print("")

print("reading value")
value = mso.ReadProperty('priorityForWriting')
print("{}".format(value))
print("")

print("writing value")
mso.WriteProperty('priorityForWriting', 3)
print("")

