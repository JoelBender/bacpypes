#!/usr/bin/env python

"""
UDPConsole
==========

This is a sample application that is similar to the UDPMultiplexer.  It opens
a socket for unicast messages and (optionally) another for broadcast messages.

Run this application with a BACpypes IP address parameter.

    $ python UDPConsole.py <addr> [ --nobroadcast ]

The address can be one of the following forms:

    192.168.1.10             - unicast socket, no broadcast socket, port 47808
    192.168.1.10/24          - unicast socket, 192.168.1.255 broadcast socket, port 47808
    192.168.1.10:12345       - unicast socket, no broadcast socket, port 12345
    192.168.1.10/24:12345    - unicast socket, 192.168.1.255 broadcast socket, port 12345
    any                      - special tuple ('', 47808)
    any:12345                - special tuple ('', 12345)

Use the --nobroadcast option to prevent the application from opening the
broadcast socket when one would otherwise be opened.

To send a packet, enter in a string in the form <addr> <message> where <addr>
is a BACpyes IP address (which may include the socket) or '*' for a local
broadcast.

Linux/MacOS Test Cases
----------------------

Here are some test cases for Linux and MacOS.

Using Any
~~~~~~~~~

    $ python samples/UDPConsole.py any
    * hi
    received u'hi' from ('10.0.1.5', 47808)

In this case the application received its own broadcast, but did not recognize
it as a broadcast message and did not recognize that it came from itself.
Broadcast messages from other devices sent to 255.255.255.255 or 10.0.1.255
are received, but also not recognized as broadcast messages.

Using the Local Address
~~~~~~~~~~~~~~~~~~~~~~~

    $ python samples/UDPConsole.py 10.0.1.5
    * hi
    received u'hi' from self

In this case it received its own broadcast and it recognized that it came from
itself, but it did not recognize it as a broadcast message.  Broadcast messages
from other devices sent to 255.255.255.255 or 10.0.1.255 are not received.

Using the CIDR Address
~~~~~~~~~~~~~~~~~~~~~~

    $ python samples/UDPConsole.py 10.0.1.5/24
    * hi
    received broadcast u'hi' from self

In this case it received its own broadcast, recognized that it came from itself,
and also recognized it was sent as a broadcast message.  Broadcast messages
from other devices sent to 255.255.255.255 are not received, but those sent to
10.0.1.255 are received and recognized as broadcast messages.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.udp import UDPDirector
from bacpypes.comm import Client, Server, bind
from bacpypes.pdu import Address, PDU
from bacpypes.core import run, stop

from bacpypes.consolelogging import ArgumentParser
from bacpypes.console import ConsoleClient


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
local_unicast_tuple = None
local_broadcast_tuple = None

#
#   MiddleMan
#

@bacpypes_debugging
class MiddleMan(Client, Server):

    """
    An instance of this class sits between the UDPDirector and the
    console.  Downstream packets from a console have no concept of a
    destination, so this is interpreted from the text and then a new
    PDU is sent to the director.  Upstream packets could be simply
    forwarded to the console, in that case the source address is ignored,
    this application interprets the source address for the user.
    """

    def indication(self, pdu):
        if _debug: MiddleMan._debug('indication %r', pdu)

        # empty downstream packets mean EOF
        if not pdu.pduData:
            stop()
            return

        # decode the line and trim off the eol
        line = pdu.pduData.decode('utf-8')[:-1]
        if _debug: MiddleMan._debug('    - line: %r', line)

        line_parts = line.split(' ', 1)
        if _debug: MiddleMan._debug('    - line_parts: %r', line_parts)
        if len(line_parts) != 2:
            sys.stderr.write("err: invalid line: %r\n" % (line,))
            return

        addr, msg = line_parts

        # check the address
        if addr == "*":
            dest = local_broadcast_tuple
        elif ':' in addr:
            addr, port = addr.split(':')
            if addr == "*":
                dest = (local_broadcast_tuple[0], int(port))
            else:
                dest = (addr, int(port))
        else:
            dest = (addr, local_unicast_tuple[1])
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
        line = pdu.pduData.decode('utf_8')
        if _debug: MiddleMan._debug('    - line: %r', line)

        if pdu.pduSource == local_unicast_tuple:
            sys.stdout.write("received %r from self\n" % (line,))
        else:
            sys.stdout.write("received %r from %s\n" % (line, pdu.pduSource))


#
#   BroadcastReceiver
#

@bacpypes_debugging
class BroadcastReceiver(Client):

    """
    An instance of this class sits above the UDPDirector that is
    associated with the broadcast address.  There are no downstream
    packets, and it interprets the source address for the user.
    """

    def confirmation(self, pdu):
        if _debug: BroadcastReceiver._debug('confirmation %r', pdu)

        # decode the line
        line = pdu.pduData.decode('utf-8')
        if _debug: MiddleMan._debug('    - line: %r', line)

        if pdu.pduSource == local_unicast_tuple:
            sys.stdout.write("received broadcast %r from self\n" % (line,))
        else:
            sys.stdout.write("received broadcast %r from %s\n" % (line, pdu.pduSource,))


#
#   __main__
#

def main():
    global local_unicast_tuple, local_broadcast_tuple

    # parse the command line arguments
    parser = ArgumentParser(usage=__doc__)
    parser.add_argument("address",
        help="address of socket",
        )
    parser.add_argument("--nobroadcast",
        action="store_true",
        dest="noBroadcast",
        default=False,
        help="do not create a broadcast socket",
        )

    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    if args.address == "any":
        local_unicast_tuple = ('', 47808)
        local_broadcast_tuple = ('255.255.255.255', 47808)

    elif args.address.startswith("any:"):
        port = int(args.address[4:])
        local_unicast_tuple = ('', port)
        local_broadcast_tuple = ('255.255.255.255', port)

    else:
        address = Address(args.address)
        if _debug: _log.debug("    - local_address: %r", address)

        local_unicast_tuple = address.addrTuple
        local_broadcast_tuple = address.addrBroadcastTuple

    if _debug: _log.debug("    - local_unicast_tuple: %r", local_unicast_tuple)
    if _debug: _log.debug("    - local_broadcast_tuple: %r", local_broadcast_tuple)

    console = ConsoleClient()
    middle_man = MiddleMan()
    unicast_director = UDPDirector(local_unicast_tuple)
    bind(console, middle_man, unicast_director)

    if args.noBroadcast:
        _log.debug("    - skipping broadcast")

    elif local_unicast_tuple == local_broadcast_tuple:
        _log.debug("    - identical unicast and broadcast tuples")

    elif local_broadcast_tuple[0] == '255.255.255.255':
        _log.debug("    - special broadcast address only for sending")

    else:
        broadcast_receiver = BroadcastReceiver()
        broadcast_director = UDPDirector(local_broadcast_tuple, reuse=True)
        bind(broadcast_receiver, broadcast_director)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
