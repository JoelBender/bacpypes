#!/usr/bin/env python

"""
This sample application demonstrates a mix-in class for commandable properties
(not useful for Binary Out or Binary Value objects that have a minimum on and off
time, or for Channel objects).
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.errors import ExecutionError

from bacpypes.object import AnalogValueObject, DateValueObject
from bacpypes.primitivedata import Null, Date
from bacpypes.basetypes import PriorityValue, PriorityArray

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   CommandableMixin
#

@bacpypes_debugging
class CommandableMixin(object):

    def __init__(self, init_value, **kwargs):
        if _debug: CommandableMixin._debug("__init__ %r, %r", init_value, kwargs)
        super(CommandableMixin, self).__init__(**kwargs)

        # if no present value given, give it the default value
        if ('presentValue' not in kwargs):
            if _debug: CommandableMixin._debug("    - initialize present value")
            self.presentValue = init_value

        # if no priority array given, give it an empty one
        if ('priorityArray' not in kwargs):
            if _debug: CommandableMixin._debug("    - initialize priority array")
            self.priorityArray = PriorityArray()
            for i in range(16):
                self.priorityArray.append(PriorityValue(null=Null()))

        # if no relinquish default value given, give it the default value
        if ('relinquishDefault' not in kwargs):
            if _debug: CommandableMixin._debug("    - initialize relinquish default")
            self.relinquishDefault = init_value

        # capture the present value property
        self._pv = self._properties['presentValue']
        if _debug: CommandableMixin._debug("    - _pv: %r", self._pv)

        # capture the datatype
        self._pv_datatype = self._pv.datatype
        if _debug: CommandableMixin._debug("    - _pv_datatype: %r", self._pv_datatype)

        # look up a matching priority value choice
        for element in PriorityValue.choiceElements:
            if element.klass is self._pv_datatype:
                self._pv_choice = element.name
                break
        else:
            self._pv_choice = 'constructedValue'
        if _debug: CommandableMixin._debug("    - _pv_choice: %r", self._pv_choice)

    def WriteProperty(self, property, value, arrayIndex=None, priority=None, direct=False):
        if _debug: CommandableMixin._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", property, value, arrayIndex, priority, direct)

        # when writing to the presentValue with a priority
        if (property == 'presentValue'):
            # default (lowest) priority
            if priority is None:
                priority = 16
            if _debug: CommandableMixin._debug("    - translate to array index %d", priority)

            # translate to updating the priority array
            property = 'priorityArray'
            arrayIndex = priority
            priority = None

        # update the priority array entry
        if (property == 'priorityArray') and (arrayIndex is not None):
            # check the bounds
            if arrayIndex == 0:
                raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')
            if (arrayIndex < 1) or (arrayIndex > 16):
                raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')

            # update the specific priorty value element
            priority_value = self.priorityArray[arrayIndex]
            if _debug: CommandableMixin._debug("    - priority_value: %r", priority_value)

            # the null or the choice has to be set, the other clear
            if value is ():
                if _debug: CommandableMixin._debug("    - write a null")
                priority_value.null = value
                setattr(priority_value, self._pv_choice, None)
            else:
                if _debug: CommandableMixin._debug("    - write a value")
                priority_value.null = None
                setattr(priority_value, self._pv_choice, value)

            # look for the highest priority value
            for i in range(1, 17):
                priority_value = self.priorityArray[i]
                if priority_value.null is None:
                    if (i < arrayIndex):
                        if _debug: CommandableMixin._debug("    - existing higher priority value")
                        return
                    value = getattr(priority_value, self._pv_choice)
                    break
            else:
                value = self.relinquishDefault
            if _debug: CommandableMixin._debug("    - new present value: %r", value)

            property = 'presentValue'
            arrayIndex = priority = None

        # allow the request to pass through
        if _debug: CommandableMixin._debug("    - super: %r %r arrayIndex=%r priority=%r", property, value, arrayIndex, priority)
        super(CommandableMixin, self).WriteProperty(
            property, value,
            arrayIndex=arrayIndex, priority=priority, direct=direct,
            )

#
#   CommandableAnalogValueObject
#

@bacpypes_debugging
class CommandableAnalogValueObject(CommandableMixin, AnalogValueObject):

    def __init__(self, **kwargs):
        if _debug: CommandableAnalogValueObject._debug("__init__ %r", kwargs)
        CommandableMixin.__init__(self, 0.0, **kwargs)

#
#   CommandableDateValueObject
#

@bacpypes_debugging
class CommandableDateValueObject(CommandableMixin, DateValueObject):

    def __init__(self, **kwargs):
        if _debug: CommandableDateValueObject._debug("__init__ %r", kwargs)
        CommandableMixin.__init__(self, None, **kwargs)

#
#   __main__
#

def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a commandable analog value object, add to the device
    cavo1 = CommandableAnalogValueObject(
        objectIdentifier=('analogValue', 1), objectName='Commandable1',
        )
    if _debug: _log.debug("    - cavo1: %r", cavo1)
    this_application.add_object(cavo1)

    # get the current date
    today = Date().now()

    # make a commandable date value object, add to the device
    cdvo2 = CommandableDateValueObject(
        objectIdentifier=('dateValue', 1), objectName='Commandable2',
        presentValue=today.value,
        )
    if _debug: _log.debug("    - cdvo2: %r", cdvo2)
    this_application.add_object(cdvo2)

    if _debug: _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
