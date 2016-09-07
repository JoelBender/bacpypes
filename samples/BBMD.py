#!/usr/bin/env python

"""
This sample application presents itself as a BBMD sitting on an IP network.
The first parameter is the address of the BBMD itself and the second and
subsequent parameters are the entries to put in its broadcast distribution
table.
"""

from bacpypes.debugging import ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run
from bacpypes.comm import bind

from bacpypes.pdu import Address
from bacpypes.bvllservice import BIPBBMD, AnnexJCodec, UDPMultiplexer

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)

    # add an argument for interval
    parser.add_argument('localaddr', type=str,
          help='local address of the BBMD',
          )

    # add an argument for interval
    parser.add_argument('bdtentry', type=str, nargs='*',
          help='list of addresses of peers',
          )

    # now parse the arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    local_address = Address(args.localaddr)
    if _debug: _log.debug("    - local_address: %r", local_address)

    # create a BBMD, bound to the Annex J server on a UDP multiplexer
    bbmd = BIPBBMD(local_address)
    annexj = AnnexJCodec()
    multiplexer = UDPMultiplexer(local_address)

    # bind the layers together
    bind(bbmd, annexj, multiplexer.annexJ)

    # loop through the rest of the addresses
    for bdtentry in args.bdtentry:
        if _debug: _log.debug("    - bdtentry: %r", bdtentry)

        bdt_address = Address(bdtentry)
        bbmd.add_peer(bdt_address)

    if _debug: _log.debug("    - bbmd: %r", bbmd)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
