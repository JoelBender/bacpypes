#!/usr/bin/python

"""
This simple TCP client application connects to a server and sends the text
entered in the console.  There is no conversion from incoming streams of
content into a line or any other higher-layer concept of a packet.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.core import run, stop
from bacpypes.task import TaskManager
from bacpypes.comm import PDU, Client, Server, bind, ApplicationServiceElement

from bacpypes.consolelogging import ArgumentParser
from bacpypes.console import ConsoleClient
from bacpypes.tcp import TCPClientDirector

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
server_address = None

# defaults
default_server_host = '127.0.0.1'
default_server_port = 9000

#
#   MiddleMan
#

@bacpypes_debugging
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
            stop()
            return

        # pass it along
        self.request(PDU(pdu.pduData, destination=server_address))

    def confirmation(self, pdu):
        if _debug: MiddleMan._debug("confirmation %r", pdu)

        # pass it along
        self.response(pdu)


#
#   MiddleManASE
#

@bacpypes_debugging
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

        # if there are no clients, quit
        if not self.elementService.clients:
            if _debug: MiddleManASE._debug("    - quitting")
            stop()


def main():
    """
    Main function, called when run as an application.
    """
    global server_address

    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "host", nargs='?',
        help="address of host",
        default=default_server_host,
        )
    parser.add_argument(
        "port", nargs='?', type=int,
        help="server port",
        default=default_server_port,
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

    this_director = TCPClientDirector()
    if _debug: _log.debug("    - this_director: %r", this_director)

    bind(this_console, this_middle_man, this_director)
    bind(MiddleManASE(), this_director)

    # create a task manager for scheduled functions
    task_manager = TaskManager()
    if _debug: _log.debug("    - task_manager: %r", task_manager)

    # don't wait to connect
    this_director.connect(server_address)

    if _debug: _log.debug("running")

    run()


if __name__ == "__main__":
    main()
