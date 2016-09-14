#!/usr/bin/env python

"""
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0 
_log = ModuleLogger(globals())

#
#   Event Detection Transfer
#

@bacpypes_debugging
class EventDetectionTransfer:

    def __init__(self, eda, parameter, obj, property, filter=None):
        if _debug: EventDetectionTransfer._debug("__init__ ...")

        # keep track of the parameter values
        self.eda = eda
        self.parameter = parameter
        self.obj = obj
        self.property = property
        self.filter = None

    def property_change(self, old_value, new_value):
        if _debug: EventDetectionTransfer._debug("property_change ...")

        # set the parameter value
        setattr(self.eda, self.parameter, new_value)

        # if this is already triggered, don't bother checking for more
        if self.eda._triggered:
            if _debug: EventDetectionTransfer._debug("    - already triggered")
            return

        # if there is a special filter, use it, otherwise use !=
        if self.filter:
            trigger = self.filter(old_value, new_value)
        else:
            trigger = (old_value != new_value)
        if _debug: EventDetectionTransfer._debug("    - trigger: %r", trigger)

        # trigger it
        if trigger:
            deferred(self.eda.evaluate)
            self.eda._triggered = True

#
#   transfer_filter
#

def transfer_filter(parameter):
    def transfer_filter_decorator(fn):
        # extract the class from the unbound method
        filter_class = fn.im_class

        # if the transfer filters is None this is the first transfer filter
        # function for this class and it gets its own mapping
        if filter_class._transfer_filters is None:
            filter_class._transfer_filters = {}

        filter_class._transfer_filters[parameter] = fn

        # return the function unspoiled
        return fn

    return transfer_filter_decorator

#
#   EventDetectionAlgorithm
#

@bacpypes_debugging
class EventDetectionAlgorithm:

    _transfer_filters = None

    def __init__(self):
        if _debug: EventDetectionAlgorithm._debug("__init__ %r")

        # transfer objects
        self._transfers = []

        # triggered
        self._triggered = False

    def bind(self, **kwargs):
        if _debug: EventDetectionAlgorithm._debug("bind %r", kwargs)

        for parameter, (obj, property) in kwargs.items():
            if not hasattr(self, parameter):
                pass

            # make a transfer object
            xfr = EventDetectionTransfer(self, parameter, obj, property)

            # check to see if there is a custom filter for it
            if parameter in self.transfer_filters:
                xfr.filter = partial(self.transfer_filters[parameter], self)

            # keep track of all of these objects for if/when we unbind
            self._transfers.append(xfr)

            # add the property value monitor function
            obj._property_monitor[property] = xfr.property_change

            # set the parameter value to the property value if it's not None
            property_value = obj._value[property]
            if property_value is not None:
                setattr(self, parameter, property_value)

    def unbind(self):
        if _debug: EventDetectionAlgorithm._debug("unbind %r", kwargs)

        # remove the property value monitor functions
        for xfr in self._transfers:
            obj._property_monitor[property].remove(xfr.property_change)

        # abandon the array of transfers
        self._transfers = []

    def evaluate(self):
        if _debug: EventDetectionAlgorithm._debug("evaluate %r", kwargs)

        self._triggered = False

#
#   SampleEventDetection
#

@bacpypes_debugging
class SampleEventDetection(EventDetectionAlgorithm):

    def __init__(self, **kwargs):
        if _debug: SampleEventDetection._debug("__init__ %r %r", self, kwargs)
        EventDetectionAlgorithm.__init__(self)

        # provide an interesting default value
        self.pParameter = None

        # bind to the parameter values provided
        self.bind(**kwargs)

    @transfer_filter('pParameter')
    def parameter_filter(self, old_value, new_value):
        if _debug: SampleEventDetection._debug("parameter_filter %r %r", old_value, new_value)

        return (old_value != new_value)

    def evaluate(self):
        if _debug: SampleEventDetection._debug("evaluate %r", kwargs)

        # if _triggered is true this function was called because of some
        # parameter change, but could have been called for some other reason
        if self._triggered:
            if _debug: SampleEventDetection._debug("   - triggered")

            self._triggered = False
        else:
            if _debug: SampleEventDetection._debug("    - not triggered")
