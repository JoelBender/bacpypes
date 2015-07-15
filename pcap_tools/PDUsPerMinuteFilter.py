#!/usr/bin/python

"""
PDUs per Minute Filter - present a table of number of PDUs per minute
"""

import sys
from collections import defaultdict

from bacpypes.debugging import Logging, function_debugging, ModuleLogger
from bacpypes.consolelogging import ConsoleLogHandler

from bacpypes.analysis import trace, strftimestamp, Tracer

try:
    from CSStat import Statistics
except ImportError:
    Statistics = lambda: None

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
counter = defaultdict(int)

#
#   PDUsPerMinuteTracer
#

class PDUsPerMinuteTracer(Tracer, Logging):

    def __init__(self):
        if _debug: PDUsPerMinuteTracer._debug("__init__")
        Tracer.__init__(self, self.Filter)

    def Filter(self, pkt):
        if _debug: PDUsPerMinuteTracer._debug("Filter %r", pkt)

        slot = ((int(pkt._timestamp) / interval) * interval)
        if _debug: PDUsPerMinuteTracer._debug("    - slot: %r", slot)

        # count the packets in the slot
        counter[slot] += 1

#
#   __main__
#

try:
    if ('--debug' in sys.argv):
        indx = sys.argv.index('--debug')
        for i in range(indx+1, len(sys.argv)):
            ConsoleLogHandler(sys.argv[i])
        del sys.argv[indx:]

    if _debug: _log.debug("initialization")

    # check for a custom interval
    if ('--interval' in sys.argv):
        i = sys.argv.index('--interval')
        interval = int(sys.argv[i+1])
        if _debug: _log.debug("    - interval: %r", interval)
        del sys.argv[i:i+2]
    else:
        interval = 60

    # trace the file(s)
    for fname in sys.argv[1:]:
        trace(fname, [PDUsPerMinuteTracer])

    # print some stats at the end
    stats = Statistics()

    # dump the counters
    for ts in range(min(counter), max(counter)+1, interval):
        print strftimestamp(ts), counter[ts]
        if stats:
            stats.Record(counter[ts], ts)

    if stats:
        smin, smax, _, _, _, _ = stats.Stats()

        xlw, lw, q1, m, q3, uw, xuw = stats.Whisker()
        if m is not None:
            print "\t    %-8.1f" % smax
            print "\t    %-8.1f" % xuw
            print "\t--- %-8.1f" % uw
            print "\t | "
            print "\t.'. %-8.1f" % q3
            print "\t| |"
            print "\t|-| %-8.1f" % m
            print "\t| |"
            print "\t'-' %-8.1f" % q1
            print "\t | "
            print "\t--- %-8.1f" % lw
            print "\t    %-8.1f" % xlw
            print "\t    %-8.1f" % smin
        else:
            print "No stats"

except KeyboardInterrupt:
    pass
except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    if _debug: _log.debug("finally")

