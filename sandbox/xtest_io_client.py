#!/usr/bin/python

"""
test_io_client
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.console import ConsoleClient
from bacpypes.consolelogging import ArgumentParser
from bacpypes.comm import PDU, Server, bind

from bacpypes.core import run

from io import IOProxy, IOCB, COMPLETED, ABORTED

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# defaults
SERVER = "127.0.0.1"
CONTROLLER = "test"

# globals
testServer = None

#
#   MiddleMan
#

@bacpypes_debugging
class MiddleMan(Server):

    def indication(self, pdu):
        MiddleMan._debug('indication %r', pdu)

        try:
            iocb = IOCB(int(pdu.pduData))
        except:
            print "Integer please."
            return

        iocb.set_timeout(5)
        iocb.add_callback(self.complete)

        # send the request
        testServer.request_io(iocb)

    def complete(self, iocb):
        MiddleMan._debug('complete %r', iocb)
    
        # if this has completed successfully, pass it up
        if iocb.ioState == COMPLETED:
            self.response(PDU(str(iocb.ioResponse) + '\n'))

        # if this aborted, pass that up too
        elif iocb.ioState == ABORTED:
            self.response(PDU(repr(iocb.ioError) + '\n'))

        else:
            raise RuntimeError, "invalid state: %r" % (iocb.ioState,)

#
#   __main__
#

try:
    # create a parser
    parser = ArgumentParser(description=__doc__)

    # add an option to pick a server
    parser.add_argument('--server',
        help="server name or address",
        default=SERVER,
        )

    # add an option to pick a controller
    parser.add_argument('--controller',
        help="controller name",
        default=CONTROLLER,
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # create a proxy for the real server
    testServer = IOProxy(args.controller, args.server)

    console = ConsoleClient()
    middleMan = MiddleMan()
    bind(console, middleMan)

    _log.debug("running")
    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")
