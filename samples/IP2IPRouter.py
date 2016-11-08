#!/usr/bin/env python

"""
This sample application presents itself as a router between two
IP networks.  This application can run on a single homed machine
by using the same IP address and two different port numbers, or
to be closer to what is typically considered a router, on a
multihomed machine using two different IP addresses and the same
port number.

$ python IP2IPRtouer.py addr1 net1 addr2 net2

    addr1       - local address like 192.168.1.2/24:47808
    net1        - network number
    addr2       - local address like 192.168.3.4/24:47809
    net2        - network number

As a router, this does not have an application layer.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run
from bacpypes.comm import bind

from bacpypes.pdu import Address
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPSimple, AnnexJCodec, UDPMultiplexer

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   IP2IPRouter
#

@bacpypes_debugging
class IP2IPRouter:

    def __init__(self, addr1, net1, addr2, net2):
        if _debug: IP2IPRouter._debug("__init__ %r %r %r %r", addr1, net1, addr2, net2)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        #== First stack

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.s1_bip = BIPSimple()
        self.s1_annexj = AnnexJCodec()
        self.s1_mux = UDPMultiplexer(addr1)

        # bind the bottom layers
        bind(self.s1_bip, self.s1_annexj, self.s1_mux.annexJ)

        # bind the BIP stack to the local network
        self.nsap.bind(self.s1_bip, net1, addr1)

        #== Second stack

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.s2_bip = BIPSimple()
        self.s2_annexj = AnnexJCodec()
        self.s2_mux = UDPMultiplexer(addr2)

        # bind the bottom layers
        bind(self.s2_bip, self.s2_annexj, self.s2_mux.annexJ)

        # bind the BIP stack to the local network
        self.nsap.bind(self.s2_bip, net2)

#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)

    # add an argument for interval
    parser.add_argument('addr1', type=str,
          help='address of first network',
          )

    # add an argument for interval
    parser.add_argument('net1', type=int,
          help='network number of first network',
          )

    # add an argument for interval
    parser.add_argument('addr2', type=str,
          help='address of second network',
          )

    # add an argument for interval
    parser.add_argument('net2', type=int,
          help='network number of second network',
          )

    # now parse the arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # create the router
    router = IP2IPRouter(Address(args.addr1), args.net1, Address(args.addr2), args.net2)
    if _debug: _log.debug("    - router: %r", router)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
