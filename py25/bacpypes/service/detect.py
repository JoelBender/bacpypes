#!/usr/bin/env python

"""
Detection
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.core import deferred

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   DetectionMonitor
#

class DetectionMonitor:

    def __init__(self, algorithm, parameter, obj, prop, filter=None):
        if _debug: DetectionMonitor._debug("__init__ ...")

        # keep track of the parameter values
        self.algorithm = algorithm
        self.parameter = parameter
        self.obj = obj
        self.prop = prop
        self.filter = None

    def property_change(self, old_value, new_value):
        if _debug: DetectionMonitor._debug("property_change %r %r", old_value, new_value)

        # set the parameter value
        setattr(self.algorithm, self.parameter, new_value)

        # if the algorithm is already triggered, don't bother checking for more
        if self.algorithm._triggered:
            if _debug: DetectionMonitor._debug("    - already triggered")
            return

        # if there is a special filter, use it, otherwise use !=
        if self.filter:
            trigger = self.filter(old_value, new_value)
        else:
            trigger = (old_value != new_value)
        if _debug: DetectionMonitor._debug("    - trigger: %r", trigger)

        # trigger it
        if trigger:
            deferred(self.algorithm._execute)
            if _debug: DetectionMonitor._debug("    - deferred: %r", self.algorithm._execute)

            self.algorithm._triggered = True

bacpypes_debugging(DetectionMonitor)

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

class DetectionAlgorithm:

    def __init__(self):
        if _debug: DetectionAlgorithm._debug("__init__")

        # monitor objects
        self._monitors = []

        # triggered flag, set when a parameter changed and the monitor
        # schedules the algorithm to execute
        self._triggered = False

    def bind(self, **kwargs):
        if _debug: DetectionAlgorithm._debug("bind %r", kwargs)

        # build a map of methods that are filters.  These have been decorated
        # with monitor_filter, but they are unbound methods (or simply
        # functions in Python3) at the time they are decorated but by looking
        # for them now they are bound to this instance.
        monitor_filters = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_monitor_filter"):
                monitor_filters[attr._monitor_filter] = attr
        if _debug: DetectionAlgorithm._debug("    - monitor_filters: %r", monitor_filters)

        for parameter, (obj, prop) in kwargs.items():
            if not hasattr(self, parameter):
                if _debug: DetectionAlgorithm._debug("    - no matching parameter: %r", parameter)

            # make a detection monitor
            monitor = DetectionMonitor(self, parameter, obj, prop)
            if _debug: DetectionAlgorithm._debug("    - monitor: %r", monitor)

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
        if _debug: DetectionAlgorithm._debug("unbind")

        # remove the property value monitor functions
        for monitor in self._monitors:
            if _debug: DetectionAlgorithm._debug("    - monitor: %r", monitor)
            monitor.obj._property_monitors[monitor.prop].remove(monitor.property_change)

        # abandon the array
        self._monitors = []

    def _execute(self):
        if _debug: DetectionAlgorithm._debug("_execute")

        # provided by the derived class
        self.execute()

        # turn the trigger off
        self._triggered = False

    def execute(self):
        raise NotImplementedError("execute not implemented")

bacpypes_debugging(DetectionAlgorithm)
