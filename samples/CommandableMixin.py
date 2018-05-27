#!/usr/bin/env python

"""
Rebuilt Commandable
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.task import OneShotTask
from bacpypes.errors import ExecutionError

from bacpypes.primitivedata import BitString, CharacterString, Date, Integer, \
    Double, Enumerated, OctetString, Real, Time, Unsigned
from bacpypes.basetypes import BinaryPV, ChannelValue, DateTime, DoorValue, PriorityValue, \
    PriorityArray
from bacpypes.object import Property, ReadableProperty, WritableProperty, \
    register_object_type, \
    AccessDoorObject, AnalogOutputObject, AnalogValueObject, \
    BinaryOutputObject, BinaryValueObject, BitStringValueObject, CharacterStringValueObject, \
    DateValueObject, DatePatternValueObject, DateTimePatternValueObject, \
    DateTimeValueObject, IntegerValueObject, \
    LargeAnalogValueObject, LightingOutputObject, MultiStateOutputObject, \
    MultiStateValueObject, OctetStringValueObject, PositiveIntegerValueObject, \
    TimeValueObject, TimePatternValueObject, ChannelObject

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.object import CurrentPropertyListMixIn
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   Commandable
#

@bacpypes_debugging
def Commandable(datatype, presentValue='presentValue', priorityArray='priorityArray', relinquishDefault='relinquishDefault'):
    if _debug: Commandable._debug("Commandable %r ...", datatype)

    class _Commando(object):

        properties = [
            WritableProperty(presentValue, datatype),
            ReadableProperty(priorityArray, PriorityArray),
            ReadableProperty(relinquishDefault, datatype),
            ]

        _pv_choice = None

        def __init__(self, **kwargs):
            super(_Commando, self).__init__(**kwargs)

            # build a default value in case one is needed
            default_value = datatype().value
            if issubclass(datatype, Enumerated):
                default_value = datatype._xlate_table[default_value]
            if _debug: Commandable._debug("    - default_value: %r", default_value)

            # see if a present value was provided
            if (presentValue not in kwargs):
                setattr(self, presentValue, default_value)

            # see if a priority array was provided
            if (priorityArray not in kwargs):
                new_priority_array = PriorityArray()
                for i in range(16):
                    new_priority_array.append(PriorityValue(null=()))
                setattr(self, priorityArray, new_priority_array)

            # see if a present value was provided
            if (relinquishDefault not in kwargs):
                setattr(self, relinquishDefault, default_value)

        def _highest_priority_value(self):
            if _debug: Commandable._debug("_highest_priority_value")

            priority_array = getattr(self, priorityArray)
            for i in range(1, 17):
                priority_value = priority_array[i]
                if priority_value.null is None:
                    if _debug: Commandable._debug("    - found at index: %r", i)

                    value = getattr(priority_value, _Commando._pv_choice)
                    value_source = "###"

                    if issubclass(datatype, Enumerated):
                        value = datatype._xlate_table[value]
                        if _debug: Commandable._debug("    - remapped enumeration: %r", value)

                    break
            else:
                value = getattr(self, relinquishDefault)
                value_source = None

            if _debug: Commandable._debug("    - value, value_source: %r, %r", value, value_source)

            # return what you found
            return value, value_source

        def WriteProperty(self, property, value, arrayIndex=None, priority=None, direct=False):
            if _debug: Commandable._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", property, value, arrayIndex, priority, direct)

            # when writing to the presentValue with a priority
            if (property == presentValue):
                if _debug: Commandable._debug("    - writing to %s, priority %r", presentValue, priority)

                # default (lowest) priority
                if priority is None:
                    priority = 16
                if _debug: Commandable._debug("    - translate to priority array, index %d", priority)

                # translate to updating the priority array
                property = priorityArray
                arrayIndex = priority
                priority = None

            # update the priority array entry
            if (property == priorityArray):
                if (arrayIndex is None):
                    if _debug: Commandable._debug("    - writing entire %s", priorityArray)

                    # pass along the request
                    super(_Commando, self).WriteProperty(
                        property, value,
                        arrayIndex=arrayIndex, priority=priority, direct=direct,
                        )
                else:
                    if _debug: Commandable._debug("    - writing to %s, array index %d", priorityArray, arrayIndex)

                    # check the bounds
                    if arrayIndex == 0:
                        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')
                    if (arrayIndex < 1) or (arrayIndex > 16):
                        raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')

                    # update the specific priorty value element
                    priority_value = getattr(self, priorityArray)[arrayIndex]
                    if _debug: Commandable._debug("    - priority_value: %r", priority_value)

                    # the null or the choice has to be set, the other clear
                    if value is ():
                        if _debug: Commandable._debug("    - write a null")
                        priority_value.null = value
                        setattr(priority_value, _Commando._pv_choice, None)
                    else:
                        if _debug: Commandable._debug("    - write a value")

                        if issubclass(datatype, Enumerated):
                            value = datatype._xlate_table[value]
                            if _debug: Commandable._debug("    - remapped enumeration: %r", value)

                        priority_value.null = None
                        setattr(priority_value, _Commando._pv_choice, value)

                # look for the highest priority value
                value, value_source = self._highest_priority_value()

                # compare with the current value
                current_value = getattr(self, presentValue)
                if value == current_value:
                    if _debug: Commandable._debug("    - no present value change")
                    return

                # turn this into a present value change
                property = presentValue
                arrayIndex = priority = None

            # allow the request to pass through
            if _debug: Commandable._debug("    - super: %r %r arrayIndex=%r priority=%r", property, value, arrayIndex, priority)

            super(_Commando, self).WriteProperty(
                property, value,
                arrayIndex=arrayIndex, priority=priority, direct=direct,
                )

    # look up a matching priority value choice
    for element in PriorityValue.choiceElements:
        if issubclass(datatype, element.klass):
            _Commando._pv_choice = element.name
            break
    else:
        _Commando._pv_choice = 'constructedValue'
    if _debug: Commandable._debug("    - _pv_choice: %r", _Commando._pv_choice)

    # return the class
    return _Commando

#
#   MinOnOffTask
#

@bacpypes_debugging
class MinOnOffTask(OneShotTask):

    def __init__(self, binary_obj):
        if _debug: MinOnOffTask._debug("__init__ %s", repr(binary_obj))
        OneShotTask.__init__(self)

        # save a reference to the object
        self.binary_obj = binary_obj

        # listen for changes to the present value
        self.binary_obj._property_monitors['presentValue'].append(self.present_value_change)

    def present_value_change(self, old_value, new_value):
        if _debug: MinOnOffTask._debug("present_value_change %r %r", old_value, new_value)

        # if there's no value change, skip all this
        if old_value == new_value:
            if _debug: MinOnOffTask._debug("    - no state change")
            return

        # get the minimum on/off time
        if new_value == 'inactive':
            task_delay = getattr(self.binary_obj, 'minimumOnTime') or 0
            if _debug: MinOnOffTask._debug("    - minimum on: %r", task_delay)
        elif new_value == 'active':
            task_delay = getattr(self.binary_obj, 'minimumOffTime') or 0
            if _debug: MinOnOffTask._debug("    - minimum off: %r", task_delay)
        else:
            raise ValueError("unrecognized present value for %r: %r" % (self.binary_obj.objectIdentifier, new_value))

        # if there's no delay, don't bother
        if not task_delay:
            if _debug: MinOnOffTask._debug("    - no delay")
            return

        # set the value at priority 6
        self.binary_obj.WriteProperty('presentValue', new_value, priority=6)

        # install this to run, if there is a delay
        self.install_task(delta=task_delay)

    def process_task(self):
        if _debug: MinOnOffTask._debug("process_task(%s)", self.binary_obj.objectName)

        # clear the value at priority 6
        self.binary_obj.WriteProperty('presentValue', (), priority=6)

#
#   MinOnOff
#

@bacpypes_debugging
class MinOnOff(object):

    def __init__(self, **kwargs):
        if _debug: MinOnOff._debug("__init__ ...")
        super(MinOnOff, self).__init__(**kwargs)

        # create the timer task
        self._min_on_off_task = MinOnOffTask(self)

#
#   Commandable Standard Objects
#

class AccessDoorObjectCmd(Commandable(DoorValue), AccessDoorObject):
    pass

class AnalogOutputObjectCmd(Commandable(Real), AnalogOutputObject):
    pass

class AnalogValueObjectCmd(Commandable(Real), AnalogValueObject):
    pass

### class BinaryLightingOutputObjectCmd(Commandable(Real), BinaryLightingOutputObject):
###     pass

class BinaryOutputObjectCmd(Commandable(BinaryPV), MinOnOff, BinaryOutputObject):
    pass

class BinaryValueObjectCmd(Commandable(BinaryPV), MinOnOff, BinaryValueObject):
    pass

class BitStringValueObjectCmd(Commandable(BitString), BitStringValueObject):
    pass

class CharacterStringValueObjectCmd(Commandable(CharacterString), CharacterStringValueObject):
    pass

class DateValueObjectCmd(Commandable(Date), DateValueObject):
    pass

class DatePatternValueObjectCmd(Commandable(Date), DatePatternValueObject):
    pass

class DateTimeValueObjectCmd(Commandable(DateTime), DateTimeValueObject):
    pass

class DateTimePatternValueObjectCmd(Commandable(DateTime), DateTimePatternValueObject):
    pass

class IntegerValueObjectCmd(Commandable(Integer), IntegerValueObject):
    pass

class LargeAnalogValueObjectCmd(Commandable(Double), LargeAnalogValueObject):
    pass

class LightingOutputObjectCmd(Commandable(Real), LightingOutputObject):
    pass

class MultiStateOutputObjectCmd(Commandable(Unsigned), MultiStateOutputObject):
    pass

class MultiStateValueObjectCmd(Commandable(Unsigned), MultiStateValueObject):
    pass

class OctetStringValueObjectCmd(Commandable(OctetString), OctetStringValueObject):
    pass

class PositiveIntegerValueObjectCmd(Commandable(Unsigned), PositiveIntegerValueObject):
    pass

class TimeValueObjectCmd(Commandable(Time), TimeValueObject):
    pass

class TimePatternValueObjectCmd(Commandable(Time), TimePatternValueObject):
    pass

#
#   ChannelValueProperty
#

class ChannelValueProperty(Property):

    def __init__(self):
        if _debug: ChannelValueProperty._debug("__init__")
        Property.__init__(self, 'presentValue', ChannelValue, default=None, optional=False, mutable=True)

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: ChannelValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)

        ### Clause 12.53.5, page 487
        raise NotImplementedError()

#
#   ChannelObjectCmd
#

class ChannelObjectCmd(ChannelObject):

    properties = [
        ChannelValueProperty(),
        ]

##
##
##
##
##

@register_object_type(vendor_id=999)
class LocalAnalogValueObjectCmd(CurrentPropertyListMixIn, AnalogValueObjectCmd):
    pass

@register_object_type(vendor_id=999)
class LocalBinaryOutputObjectCmd(CurrentPropertyListMixIn, BinaryOutputObjectCmd):
    pass

@register_object_type(vendor_id=999)
class LocalDateValueObjectCmd(CurrentPropertyListMixIn, DateValueObjectCmd):
    pass

#
#   __main__
#

def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a commandable analog value object, add to the device
    avo1 = LocalAnalogValueObjectCmd(
        objectIdentifier=('analogValue', 1),
        objectName='avo1',
        )
    if _debug: _log.debug("    - avo1: %r", avo1)
    this_application.add_object(avo1)

    # make a commandable binary output object, add to the device
    boo1 = LocalBinaryOutputObjectCmd(
        objectIdentifier=('binaryOutput', 1),
        objectName='boo1',
        presentValue='inactive',
        relinquishDefault='inactive',
        minimumOnTime=5,        # let it warm up
        minimumOffTime=10,      # let it cool off
        )
    if _debug: _log.debug("    - boo1: %r", boo1)
    this_application.add_object(boo1)

    # get the current date
    today = Date().now()

    # make a commandable date value object, add to the device
    dvo1 = LocalDateValueObjectCmd(
        objectIdentifier=('dateValue', 1),
        objectName='dvo1',
        presentValue=today.value,
        )
    if _debug: _log.debug("    - dvo1: %r", dvo1)
    this_application.add_object(dvo1)

    if _debug: _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
