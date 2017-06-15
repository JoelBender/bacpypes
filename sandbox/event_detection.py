#!/usr/bin/env python

"""
"""

from functools import partial

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run_once

from bacpypes.service.detect import DetectionAlgorithm, monitor_filter
from bacpypes.object import AnalogValueObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   something_changed
#

def something_changed(thing, old_value, new_value):
    print("%r changed from %r to %r" % (thing, old_value, new_value))

#
#   SampleEventDetection
#

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
            if _debug: SampleEventDetection._debug("    - was triggered")
        else:
            if _debug: SampleEventDetection._debug("    - was not triggered")

        # check for things
        if self.pParameter == self.pSetPoint:
            if _debug: SampleEventDetection._debug("    - parameter match")
        else:
            if _debug: SampleEventDetection._debug("    - parameter mismatch")

bacpypes_debugging(SampleEventDetection)

#
#
#

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
