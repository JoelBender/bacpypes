#!/usr/bin/python

"""
Read Property Timeout Filter - Look for Read Property Requests with no response
"""

import sys

from bacpypes.debugging import Logging, function_debugging, ModuleLogger
from bacpypes.consolelogging import ConsoleLogHandler

from bacpypes.pdu import Address
from bacpypes.analysis import trace, strftimestamp, Tracer
from bacpypes.apdu import ReadPropertyRequest, ReadPropertyACK

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
filterSource = None
filterDestination = None
filterHost = None

# dictionary of pending requests
requests = {}

# all traffic
traffic = []

#
#   Traffic
#

class Traffic:

    def __init__(self, req):
        self.req = req
        self.resp = None

        self.ts = req._timestamp
        self.retry = 1

#
#   Match
#

@function_debugging
def Match(addr1, addr2):
    """Return true iff addr1 matches addr2."""
    if _debug: Match._debug("Match %r %r", addr1, addr2)

    if (addr2.addrType == Address.localBroadcastAddr):
        # match any local station
        return (addr1.addrType == Address.localStationAddr) or (addr1.addrType == Address.localBroadcastAddr)
    elif (addr2.addrType == Address.localStationAddr):
        # match a specific local station
        return (addr1.addrType == Address.localStationAddr) and (addr1.addrAddr == addr2.addrAddr)
    elif (addr2.addrType == Address.remoteBroadcastAddr):
        # match any remote station or remote broadcast on a matching network
        return ((addr1.addrType == Address.remoteStationAddr) or (addr1.addrType == Address.remoteBroadcastAddr)) \
            and (addr1.addrNet == addr2.addrNet)
    elif (addr2.addrType == Address.remoteStationAddr):
        # match a specific remote station
        return (addr1.addrType == Address.remoteStationAddr) and \
            (addr1.addrNet == addr2.addrNet) and (addr1.addrAddr == addr2.addrAddr)
    elif (addr2.addrType == Address.globalBroadcastAddr):
        # match a global broadcast address
        return (addr1.addrType == Address.globalBroadcastAddr)
    else:
        raise RuntimeError, "invalid match combination"

#
#   ReadPropertySummary
#

class ReadPropertySummary(Tracer, Logging):

    def __init__(self):
        if _debug: ReadPropertySummary._debug("__init__")
        Tracer.__init__(self, self.Filter)

    def Filter(self, pkt):
        if _debug: ReadPropertySummary._debug("Filter %r", pkt)
        global requests

        # apply the filters
        if filterSource:
            if not Match(pkt.pduSource, filterSource):
                if _debug: ReadPropertySummary._debug("    - source filter fail")
                return
        if filterDestination:
            if not Match(pkt.pduDestination, filterDestination):
                if _debug: ReadPropertySummary._debug("    - destination filter fail")
                return
        if filterHost:
            if (not Match(pkt.pduSource, filterHost)) and (not Match(pkt.pduDestination, filterHost)):
                if _debug: ReadPropertySummary._debug("    - host filter fail")
                return

        # check for reads
        if isinstance(pkt, ReadPropertyRequest):
            key = (pkt.pduSource, pkt.pduDestination, pkt.apduInvokeID)
            if key in requests:
                if _debug: ReadPropertySummary._debug("    - retry")
                requests[key].retry += 1
            else:
                if _debug: ReadPropertySummary._debug("    - new request")
                msg = Traffic(pkt)
                requests[key] = msg
                traffic.append(msg)

        # now check for results
        elif isinstance(pkt, ReadPropertyACK):
            key = (pkt.pduDestination, pkt.pduSource, pkt.apduInvokeID)
            req = requests.get(key, None)
            if req:
                if _debug: ReadPropertySummary._debug("    - matched with request")
                requests[key].resp = pkt

                # delete the request, it stays in the traffic list
                del requests[key]
            else:
                if _debug: ReadPropertySummary._debug("    - unmatched")

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

    # check for src
    if ('--src' in sys.argv):
        i = sys.argv.index('--src')
        filterSource = Address(sys.argv[i+1])
        if _debug: _log.debug("    - filterSource: %r", filterSource)
        del sys.argv[i:i+2]

    # check for dest
    if ('--dest' in sys.argv):
        i = sys.argv.index('--dest')
        filterDestination = Address(sys.argv[i+1])
        if _debug: _log.debug("    - filterDestination: %r", filterDestination)
        del sys.argv[i:i+2]

    # check for host
    if ('--host' in sys.argv):
        i = sys.argv.index('--host')
        filterHost = Address(sys.argv[i+1])
        if _debug: _log.debug("    - filterHost: %r", filterHost)
        del sys.argv[i:i+2]

    # start out with no unmatched requests
    requests = {}

    # trace the file
    trace(sys.argv[1], [ReadPropertySummary])

    # dump the requests that failed
    for msg in traffic:
        if not msg.resp:
            print strftimestamp(msg.req._timestamp), msg.req.objectIdentifier, msg.req.propertyIdentifier

except KeyboardInterrupt:
    pass
except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    if _debug: _log.debug("finally")

