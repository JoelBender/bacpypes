#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for
device communication control commands.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.apdu import DeviceCommunicationControlRequest

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None


#
#   DCCConsoleCmd
#

@bacpypes_debugging
class DCCConsoleCmd(ConsoleCmd):

    def do_dcc(self, args):
        """dcc <addr> [ <duration> ] <enable> [ <password> ]"""
        args = args.split()
        if _debug: DCCConsoleCmd._debug("do_dcc %r", args)

        try:
            addr = args[0]

            if len(args) == 2:
                enable_disable = args[1]
                time_duration = password = None

            elif len(args) == 3:
                if args[1].isdigit():
                    time_duration = int(args[1])
                    enable_disable = args[2]
                    password = None
                else:
                    time_duration = None
                    enable_disable = args[1]
                    password = args[2]
            else:
                time_duration = int(args[1])
                enable_disable = args[2]
                password = args[3]

            # build a request
            request = DeviceCommunicationControlRequest(
                enableDisable=enable_disable,
                )
            request.pduDestination = Address(addr)

            if time_duration is not None:
                request.timeDuration = time_duration
            if password is not None:
                request.password = password
            if _debug: DCCConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: DCCConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')
            else:
                if _debug: DCCConsoleCmd._debug("    - ack")

        except Exception as error:
            DCCConsoleCmd._exception("exception: %r", error)

    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug: DCCConsoleCmd._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        this_application.nsap.add_router_references(None, router_address, network_list)


#
#   __main__
#

def main():
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a console
    this_console = DCCConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
