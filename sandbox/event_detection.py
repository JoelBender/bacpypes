#!/usr/bin/env python

"""
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.core import run, run_once, deferred

# some debugging
_debug = 0 
_log = ModuleLogger(globals())

#
#   Detection Transfer
#

@bacpypes_debugging
class DetectionTransfer:

    def __init__(self, eda, parameter, obj, prop, filter=None):
        if _debug: DetectionTransfer._debug("__init__ ...")

        # keep track of the parameter values
        self.eda = eda
        self.parameter = parameter
        self.obj = obj
        self.prop = prop
        self.filter = None

    def property_change(self, old_value, new_value):
        if _debug: DetectionTransfer._debug("property_change %r %r", old_value, new_value)

        # set the parameter value
        setattr(self.eda, self.parameter, new_value)

        # if this is already triggered, don't bother checking for more
        if self.eda._triggered:
            if _debug: DetectionTransfer._debug("    - already triggered")
            return

        # if there is a special filter, use it, otherwise use !=
        if self.filter:
            trigger = self.filter(old_value, new_value)
        else:
            trigger = (old_value != new_value)
        if _debug: DetectionTransfer._debug("    - trigger: %r", trigger)

        # trigger it
        if trigger:
            deferred(self.eda.evaluate)
            self.eda._triggered = True

#
#   transfer_filter
#

def transfer_filter(parameter):
    def transfer_filter_decorator(fn):
        fn._transfer_filter = parameter
        return fn

    return transfer_filter_decorator

#
#   DetectionAlgorithm
#

@bacpypes_debugging
class DetectionAlgorithm:

    def __init__(self):
        if _debug: DetectionAlgorithm._debug("__init__ %r")

        # transfer objects
        self._transfers = []

        # triggered
        self._triggered = False

    def bind(self, **kwargs):
        if _debug: DetectionAlgorithm._debug("bind %r", kwargs)

        # build a map of functions that have a transfer filter
        transfer_filters = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_transfer_filter"):
                transfer_filters[attr._transfer_filter] = attr
        if _debug: DetectionAlgorithm._debug("    - transfer_filters %r", kwargs)

        for parameter, (obj, prop) in kwargs.items():
            if not hasattr(self, parameter):
                if _debug: DetectionAlgorithm._debug("    - no matching parameter: %r", parameter)

            # make a transfer object
            xfr = DetectionTransfer(self, parameter, obj, prop)

            # check to see if there is a custom filter for it
            if parameter in transfer_filters:
                xfr.filter = transfer_filters[parameter]

            # keep track of all of these objects for if/when we unbind
            self._transfers.append(xfr)

            # add the property value monitor function
            obj._property_monitor[prop].append(xfr.property_change)

            # set the parameter value to the property value if it's not None
            property_value = obj._values[prop]
            if property_value is not None:
                if _debug: DetectionAlgorithm._debug("    - %s: %r", parameter, property_value)
                setattr(self, parameter, property_value)

    def unbind(self):
        if _debug: DetectionAlgorithm._debug("unbind %r", kwargs)

        # remove the property value monitor functions
        for xfr in self._transfers:
            obj._property_monitor[property].remove(xfr.property_change)

        # abandon the array of transfers
        self._transfers = []

    def evaluate(self):
        if _debug: DetectionAlgorithm._debug("evaluate %r", kwargs)

        self._triggered = False

#
#   SampleEventDetection
#

@bacpypes_debugging
class SampleEventDetection(DetectionAlgorithm):

    def __init__(self, **kwargs):
        if _debug: SampleEventDetection._debug("__init__ %r %r", self, kwargs)
        DetectionAlgorithm.__init__(self)

        # provide an interesting default value
        self.pParameter = None
        self.pSetPoint = None

        # bind to the parameter values provided
        self.bind(**kwargs)

    @transfer_filter('pParameter')
    def parameter_filter(self, old_value, new_value):
        if _debug: SampleEventDetection._debug("parameter_filter %r %r", old_value, new_value)

        return (old_value != new_value)

    def evaluate(self):
        if _debug: SampleEventDetection._debug("evaluate")

        # if _triggered is true this function was called because of some
        # parameter change, but could have been called for some other reason
        if self._triggered:
            if _debug: SampleEventDetection._debug("   - was triggered")

            self._triggered = False
        else:
            if _debug: SampleEventDetection._debug("    - was not triggered")

        # check for things
        if self.pParameter != self.pSetPoint:
            print("ding!")

#
#
#

from bacpypes.consolelogging import ArgumentParser
from bacpypes.object import AnalogValueObject

# parse the command line arguments
parser = ArgumentParser(usage=__doc__)
args = parser.parse_args()

if _debug: _log.debug("initialization")
if _debug: _log.debug("    - args: %r", args)


av1 = AnalogValueObject(
    objectIdentifier=('analogValue', 1),
    presentValue=75.3,
    )
if _debug: _log.debug("    - av1: %r", av1)

av2 = AnalogValueObject(
    objectIdentifier=('analogValue', 2),
    presentValue=75.3,
    )
if _debug: _log.debug("    - av2: %r", av2)


sed = SampleEventDetection(
    pParameter=(av1, 'presentValue'),
    pSetPoint=(av2, 'presentValue'),
    )
if _debug: _log.debug("    - sed: %r", sed)

print("")

av1.presentValue = 12.5
run_once()

print("")

av2.presentValue = 12.5
run_once()

print("")

av1.presentValue = 9.8
av2.presentValue = 10.3
run_once()
