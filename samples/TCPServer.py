#!/usr/bin/python

"""
This simple TCP server application listens for one or more client connections
and echos the incoming lines back to the client.  There is no conversion from 
incoming streams of content into a line or any other higher-layer concept
of a packet.
"""

import sys
import logging

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run
from bacpypes.comm import PDU, Client, bind, ApplicationServiceElement
from bacpypes.tcp import TCPServerDirector

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
server_address = None

# defaults
default_server_host = '127.0.0.1'
default_server_port = 9000

#
#   EchoMaster
#

class EchoMaster(Client):

    def confirmation(self, pdu):
        if _debug: EchoMaster._debug('confirmation %r', pdu)
        
        self.request(PDU(pdu.pduData, destination=pdu.pduSource))

bacpypes_debugging(EchoMaster)

#
#   MiddleManASE
#

class MiddleManASE(ApplicationServiceElement):

    def indication(self, addPeer=None, delPeer=None):
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

bacpypes_debugging(MiddleManASE)

#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host", nargs='?',
        help="listening address of server",
        default=default_server_host,
        )
    parser.add_argument(
        "--port", nargs='?', type=int,
        help="server port",
        default=default_server_port,
        )
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # extract the server address and port
    host = args.host
    if host == "any":
        host = ''
    port = args.port
    server_address = (host, port)
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


if __name__ == "__main__":
    main()

