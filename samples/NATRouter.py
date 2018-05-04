#!/usr/bin/env python

"""
This sample application presents itself as a router between an "inside" network
that sits behind a NAT and a "global" network of other NAT router peers.

$ python NATRouter.py addr1 port1 net1 addr2 port2 net2

    addr1       - local address like 192.168.1.10/24
    port1       - local port
    net1        - local network number
    addr2       - global address like 201.1.1.1:47809
    port2       - local mapped port
    net2        - global network number

The sample addresses are like running BR1 from Figure J-8, Clause J.7.5.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run
from bacpypes.comm import bind

from bacpypes.pdu import Address
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPBBMD, BIPNAT, AnnexJCodec, UDPMultiplexer

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   NATRouter
#

@bacpypes_debugging
class NATRouter:

    def __init__(self, addr1, port1, net1, addr2, port2, net2):
        if _debug: NATRouter._debug("__init__ %r %r %r %r %r %r", addr1, port1, net1, addr2, port2, net2)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        #== First stack

        # local address
        local_addr = Address("{}:{}".format(addr1, port1))

        # create a BBMD stack
        self.s1_bip = BIPBBMD(local_addr)
        self.s1_annexj = AnnexJCodec()
        self.s1_mux = UDPMultiplexer(local_addr)

        # bind the bottom layers
        bind(self.s1_bip, self.s1_annexj, self.s1_mux.annexJ)

        # bind the BIP stack to the local network
        self.nsap.bind(self.s1_bip, net1, addr1)

        #== Second stack

        # global address
        global_addr = Address(addr2)
        nat_addr = Address("{}:{}".format(addr1, port2))

        # create a NAT stack
        self.s2_bip = BIPNAT(global_addr)
        self.s2_annexj = AnnexJCodec()
        self.s2_mux = UDPMultiplexer(nat_addr)

        # bind the bottom layers
        bind(self.s2_bip, self.s2_annexj, self.s2_mux.annexJ)

        # bind the BIP stack to the global network
        self.nsap.bind(self.s2_bip, net2)

#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)

    # add an argument for local address
    parser.add_argument('addr1', type=str,
          help='address of first network',
          )

    # add an argument for local port
    parser.add_argument('port1', type=int,
          help='port number of local network',
          )

    # add an argument for interval
    parser.add_argument('net1', type=int,
          help='network number of local network',
          )

    # add an argument for interval
    parser.add_argument('addr2', type=str,
          help='address of global network (outside NAT)',
          )

    # add an argument for local port
    parser.add_argument('port2', type=int,
          help='port number of global forwarded port',
          )

    # add an argument for interval
    parser.add_argument('net2', type=int,
          help='network number of global network',
          )

    # now parse the arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # create the router
    router = NATRouter(args.addr1, args.port1, args.net1, args.addr2, args.port2, args.net2)
    if _debug: _log.debug("    - router: %r", router)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
