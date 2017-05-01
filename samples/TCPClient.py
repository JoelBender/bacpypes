#!/usr/bin/env python

"""
This simple TCP client application connects to a server and sends the text
entered in the console.  There is no conversion from incoming streams of
content into a line or any other higher-layer concept of a packet.
"""

import os

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.core import run, stop, deferred
from bacpypes.task import TaskManager
from bacpypes.comm import PDU, Client, Server, bind, ApplicationServiceElement

from bacpypes.consolelogging import ArgumentParser
from bacpypes.console import ConsoleClient
from bacpypes.tcp import TCPClientDirector

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
SERVER_PORT = int(os.getenv('SERVER_PORT', 9000))
CONNECT_TIMEOUT = int(os.getenv('CONNECT_TIMEOUT', 0)) or None
IDLE_TIMEOUT = int(os.getenv('IDLE_TIMEOUT', 0)) or None

# globals
args = None
server_address = None

#
#   MiddleMan
#

class MiddleMan(Client, Server):
    """
    An instance of this class sits between the TCPClientDirector and the
    console client.  Downstream packets from a console have no concept of a
    destination, so this is added to the PDUs before being sent to the
    director.  The source information in upstream packets is ignored by the
    console client.
    """
    def indication(self, pdu):
        if _debug: MiddleMan._debug("indication %r", pdu)
        global server_address

        # no data means EOF, stop
        if not pdu.pduData:
            # ask the director (downstream peer) to close the connection
            self.clientPeer.disconnect(server_address)
            return

        # pass it along
        self.request(PDU(pdu.pduData, destination=server_address))

    def confirmation(self, pdu):
        if _debug: MiddleMan._debug("confirmation %r", pdu)

        # check for errors
        if isinstance(pdu, Exception):
            if _debug: MiddleMan._debug("    - exception: %s", pdu)
            return

        # pass it along
        self.response(pdu)

bacpypes_debugging(MiddleMan)

#
#   MiddleManASE
#

class MiddleManASE(ApplicationServiceElement):
    """
    An instance of this class is bound to the director, which is a
    ServiceAccessPoint.  It receives notifications of new actors connected
    to a server, actors that are going away when the connections are closed,
    and socket errors.
    """
    def indication(self, add_actor=None, del_actor=None, actor_error=None, error=None):
        if add_actor:
            if _debug: MiddleManASE._debug("indication add_actor=%r", add_actor)

        if del_actor:
            if _debug: MiddleManASE._debug("indication del_actor=%r", del_actor)

            # if there are no clients, quit
            if not self.elementService.clients:
                if _debug: MiddleManASE._debug("    - no clients, stopping")
                stop()

        if actor_error:
            if _debug: MiddleManASE._debug("indication actor_error=%r error=%r", actor_error, error)
            # tell the director to close
            self.elementService.disconnect(actor_error.peer)

bacpypes_debugging(MiddleManASE)

#
#   main
#

def main():
    """
    Main function, called when run as an application.
    """
    global args, server_address

    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "host", nargs='?',
        help="address of host (default %r)" % (SERVER_HOST,),
        default=SERVER_HOST,
        )
    parser.add_argument(
        "port", nargs='?', type=int,
        help="server port (default %r)" % (SERVER_PORT,),
        default=SERVER_PORT,
        )
    parser.add_argument(
        "--hello", action="store_true",
        default=False,
        help="send a hello message",
        )
    parser.add_argument(
        "--connect-timeout", nargs='?', type=int,
        help="idle connection timeout",
        default=CONNECT_TIMEOUT,
        )
    parser.add_argument(
        "--idle-timeout", nargs='?', type=int,
        help="idle connection timeout",
        default=IDLE_TIMEOUT,
        )
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # extract the server address and port
    host = args.host
    port = args.port
    server_address = (host, port)
    if _debug: _log.debug("    - server_address: %r", server_address)

    # build the stack
    this_console = ConsoleClient()
    if _debug: _log.debug("    - this_console: %r", this_console)

    this_middle_man = MiddleMan()
    if _debug: _log.debug("    - this_middle_man: %r", this_middle_man)

    this_director = TCPClientDirector(
        connect_timeout=args.connect_timeout,
        idle_timeout=args.idle_timeout,
        )
    if _debug: _log.debug("    - this_director: %r", this_director)

    bind(this_console, this_middle_man, this_director)
    bind(MiddleManASE(), this_director)

    # create a task manager for scheduled functions
    task_manager = TaskManager()
    if _debug: _log.debug("    - task_manager: %r", task_manager)

    # don't wait to connect
    deferred(this_director.connect, server_address)

    # send hello maybe
    if args.hello:
        deferred(this_middle_man.indication, PDU(b'Hello, world!\n'))

    if _debug: _log.debug("running")

    run()

    if _debug: _log.debug("fini")

if __name__ == "__main__":
    main()
