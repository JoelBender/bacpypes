#!/usr/bin/env python

"""
"""

from functools import partial
from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.core import run, run_once, deferred

# some debugging
_debug = 0 
_log = ModuleLogger(globals())

#
#   PropertyMonitor
#

@bacpypes_debugging
class PropertyMonitor:

    def __init__(self, algorithm, parameter, obj, prop, filter=None):
        if _debug: PropertyMonitor._debug("__init__ ...")

        # keep track of the parameter values
        self.algorithm = algorithm
        self.parameter = parameter
        self.obj = obj
        self.prop = prop
        self.filter = None

    def property_change(self, old_value, new_value):
        if _debug: PropertyMonitor._debug("property_change %r %r", old_value, new_value)

        # set the parameter value
        setattr(self.algorithm, self.parameter, new_value)

        # if the algorithm is already triggered, don't bother checking for more
        if self.algorithm._triggered:
            if _debug: PropertyMonitor._debug("    - already triggered")
            return

        # if there is a special filter, use it, otherwise use !=
        if self.filter:
            trigger = self.filter(old_value, new_value)
        else:
            trigger = (old_value != new_value)
        if _debug: PropertyMonitor._debug("    - trigger: %r", trigger)

        # trigger it
        if trigger:
            deferred(self.algorithm._execute)
            self.algorithm._triggered = True

#
#   monitor_filter
#

def monitor_filter(parameter):
    def transfer_filter_decorator(fn):
        fn._monitor_filter = parameter
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
        self._monitors = []

        # triggered
        self._triggered = False

    def bind(self, **kwargs):
        if _debug: DetectionAlgorithm._debug("bind %r", kwargs)

        # build a map of functions that have a transfer filter
        monitor_filters = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_monitor_filter"):
                monitor_filters[attr._monitor_filter] = attr
        if _debug: DetectionAlgorithm._debug("    - monitor_filters %r", kwargs)

        for parameter, (obj, prop) in kwargs.items():
            if not hasattr(self, parameter):
                if _debug: DetectionAlgorithm._debug("    - no matching parameter: %r", parameter)

            # make a property monitor
            monitor = PropertyMonitor(self, parameter, obj, prop)

            # check to see if there is a custom filter for it
            if parameter in monitor_filters:
                monitor.filter = monitor_filters[parameter]

            # keep track of all of these objects for if/when we unbind
            self._monitors.append(monitor)

            # add the property value monitor function
            obj._property_monitors[prop].append(monitor.property_change)

            # set the parameter value to the property value if it's not None
            property_value = obj._values[prop]
            if property_value is not None:
                if _debug: DetectionAlgorithm._debug("    - %s: %r", parameter, property_value)
                setattr(self, parameter, property_value)

    def unbind(self):
        if _debug: DetectionAlgorithm._debug("unbind %r", kwargs)

        # remove the property value monitor functions
        for xfr in self._monitors:
            obj._property_monitor[property].remove(xfr.property_change)

        # abandon the array of transfers
        self._monitors = []

    def _execute(self):
        if _debug: DetectionAlgorithm._debug("_execute")

        # provided by the derived class
        self.execute()

        # turn the trigger off
        self._triggered = False

    def execute(self):
        raise notImplementedError("execute not implemented")

#
#   something_changed
#

def something_changed(thing, old_value, new_value):
    print("{} changed from {} to {}".format(thing, old_value, new_value))

#
#   SampleEventDetection
#

@bacpypes_debugging
class SampleEventDetection(DetectionAlgorithm):

    def __init__(self, **kwargs):
        if _debug: SampleEventDetection._debug("__init__ %r %r", self, kwargs)
        DetectionAlgorithm.__init__(self)

        # provide default values
        self.pParameter = None
        self.pSetPoint = None

        # bind to the parameter values provided
        self.bind(**kwargs)

    @monitor_filter('pParameter')
    def parameter_filter(self, old_value, new_value):
        if _debug: SampleEventDetection._debug("parameter_filter %r %r", old_value, new_value)

        return (old_value != new_value)

    def execute(self):
        if _debug: SampleEventDetection._debug("execute")

        # if _triggered is true this function was called because of some
        # parameter change, but could have been called for some other reason
        if self._triggered:
            if _debug: SampleEventDetection._debug("   - was triggered")
        else:
            if _debug: SampleEventDetection._debug("    - was not triggered")

        # check for things
        if self.pParameter != self.pSetPoint:
            if _debug: SampleEventDetection._debug("    - parameter is wrong")

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

# analog value 1
av1 = AnalogValueObject(
    objectIdentifier=('analogValue', 1),
    presentValue=75.3,
    )
if _debug: _log.debug("    - av1: %r", av1)

# add a very simple monitor
av1._property_monitors['presentValue'].append(
    partial(something_changed, "av1"),
    )

# test it
av1.presentValue = 45.6

# analog value 2
av2 = AnalogValueObject(
    objectIdentifier=('analogValue', 2),
    presentValue=75.3,
    )
if _debug: _log.debug("    - av2: %r", av2)

# sample event detection
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
