#!/usr/bin/env python

"""
This simple TCP server application listens for one or more client connections
and echos the incoming lines back to the client.  There is no conversion from 
incoming streams of content into a line or any other higher-layer concept
of a packet.
"""

import os

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run
from bacpypes.comm import PDU, Client, bind, ApplicationServiceElement
from bacpypes.tcp import TCPServerDirector

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
SERVER_HOST = os.getenv('SERVER_HOST', 'any')
SERVER_PORT = int(os.getenv('SERVER_PORT', 9000))

#
#   EchoMaster
#

@bacpypes_debugging
class EchoMaster(Client):

    def confirmation(self, pdu):
        if _debug: EchoMaster._debug('confirmation %r', pdu)

        # check for errors
        if isinstance(pdu, Exception):
            if _debug: EchoMaster._debug("    - exception: %s", pdu)
            return

        # send it back down the stack
        self.request(PDU(pdu.pduData, destination=pdu.pduSource))


#
#   MiddleManASE
#

@bacpypes_debugging
class MiddleManASE(ApplicationServiceElement):

    def indication(self, addPeer=None, delPeer=None, actor_error=None, error=None):
        """
        This function is called by the TCPDirector when the client connects to
        or disconnects from a server.  It is called with addPeer or delPeer
        keyword parameters, but not both.
        """
        if _debug: MiddleManASE._debug('indication addPeer=%r delPeer=%r', addPeer, delPeer)

        if addPeer:
            if _debug: MiddleManASE._debug("    - add peer %s", addPeer)

        if delPeer:
            if _debug: MiddleManASE._debug("    - delete peer %s", delPeer)


#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "host", nargs='?',
        help="listening address of server or 'any' (default {!r})".format(SERVER_HOST),
        default=SERVER_HOST,
        )
    parser.add_argument(
        "port", nargs='?', type=int,
        help="server port (default {!r})".format(SERVER_PORT),
        default=SERVER_PORT,
        )
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # extract the server address and port
    host = args.host
    if host == "any":
        host = ''
    server_address = (host, args.port)
    if _debug: _log.debug("    - server_address: %r", server_address)

    # create a director listening to the address
    this_director = TCPServerDirector(server_address)
    if _debug: _log.debug("    - this_director: %r", this_director)

    # create an echo
    echo_master = EchoMaster()
    if _debug: _log.debug("    - echo_master: %r", echo_master)

    # bind everything together
    bind(echo_master, this_director)
    bind(MiddleManASE(), this_director)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
