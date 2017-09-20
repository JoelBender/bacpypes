#!/usr/bin/env python

"""
B/IP VLAN
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.console import ConsoleClient

from bacpypes.comm import Client, Server, Debug, bind
from bacpypes.pdu import Address, LocalBroadcast, PDU, unpack_ip_addr
from bacpypes.core import run, stop
from bacpypes.vlan import IPNetwork, IPNode


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
network = None


#
#   FauxMux
#

@bacpypes_debugging
class FauxMux(Client, Server):

    def __init__(self, addr, network, cid=None, sid=None):
        if _debug: FauxMux._debug("__init__")

        Client.__init__(self, cid)
        Server.__init__(self, sid)

        # get the unicast and broadcast tuples
        self.unicast_tuple = addr.addrTuple
        self.broadcast_tuple = addr.addrBroadcastTuple

        # make an internal node and bind to it, this takes the place of
        # both the direct port and broadcast port of the real UDPMultiplexer
        self.node = IPNode(addr, network)
        bind(self, self.node)

    def indication(self, pdu):
        if _debug: FauxMux._debug("indication %r", pdu)

        # check for a broadcast message
        if pdu.pduDestination.addrType == Address.localBroadcastAddr:
            dest = self.broadcast_tuple
            if _debug: FauxMux._debug("    - requesting local broadcast: %r", dest)

        elif pdu.pduDestination.addrType == Address.localStationAddr:
            dest = unpack_ip_addr(pdu.pduDestination.addrAddr)
            if _debug: FauxMux._debug("    - requesting local station: %r", dest)

        else:
            raise RuntimeError("invalid destination address type")

        # continue downstream
        self.request(PDU(pdu, source=self.unicast_tuple, destination=dest))

    def confirmation(self, pdu):
        if _debug: FauxMux._debug("confirmation %r", pdu)

        # the PDU source and destination are tuples, convert them to Address instances
        src = Address(pdu.pduSource)

        # see if the destination was our broadcast address
        if pdu.pduDestination == self.broadcast_tuple:
            dest = LocalBroadcast()
        else:
            dest = Address(pdu.pduDestination)

        # continue upstream
        self.response(PDU(pdu, source=src, destination=dest))


#
#   MiddleMan
#

@bacpypes_debugging
class MiddleMan(Client, Server):

    def indication(self, pdu):
        if _debug: MiddleMan._debug('indication %r', pdu)

        # empty downstream packets mean EOF
        if not pdu.pduData:
            stop()
            return

        # decode the line and trim off the eol
        line = str(pdu.pduData.decode('utf-8'))[:-1]
        if _debug: MiddleMan._debug('    - line: %r', line)

        line_parts = line.split(' ', 1)
        if _debug: MiddleMan._debug('    - line_parts: %r', line_parts)
        if len(line_parts) != 2:
            sys.stderr.write("err: invalid line: %r\n" % (line,))
            return

        addr, msg = line_parts

        # check the address
        dest = Address(addr)
        if _debug: MiddleMan._debug('    - dest: %r', dest)

        # send it along
        try:
            self.request(PDU(msg.encode('utf_8'), destination=dest))
        except Exception as err:
            sys.stderr.write("err: %r\n" % (err,))
            return

    def confirmation(self, pdu):
        if _debug: MiddleMan._debug('confirmation %r', pdu)

        # decode the line
        line = str(pdu.pduData.decode('utf-8'))
        if _debug: MiddleMan._debug('    - line: %r', line)

        sys.stdout.write("received %r from %s\n" % (line, pdu.pduSource))


#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(usage=__doc__)
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    address = Address("192.168.0.1/24")
    if _debug: _log.debug("    - local_address: %r", address)

    # make a network
    network = IPNetwork()

    console = ConsoleClient()
    middle_man = MiddleMan()

    fauxmux = FauxMux(address, network)
    bind(console, middle_man, fauxmux)

    # add some more debugging nodes
    for i in range(2, 4):
        debug_address = "192.168.0.{}/24".format(i)

        debug_debug = Debug(debug_address)
        debug_fauxmux = FauxMux(Address(debug_address), network)

        bind(debug_debug, debug_fauxmux)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
