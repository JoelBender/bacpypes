#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for Who-Is and I-Am
commands which create the related APDUs, then lines up the coorresponding I-Am
for incoming traffic and prints out the contents.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import WhoIsRequest, IAmRequest
from bacpypes.errors import DecodingError

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None

#
#   WhoIsIAmApplication
#

@bacpypes_debugging
class WhoIsIAmApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: WhoIsIAmApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None

    def process_io(self, iocb):
        if _debug: WhoIsIAmApplication._debug("process_io %r", iocb)

        # save a copy of the request
        self._request = iocb.args[0]

        # forward it along
        BIPSimpleApplication.process_io(self, iocb)

    def confirmation(self, apdu):
        if _debug: WhoIsIAmApplication._debug("confirmation %r", apdu)

        # forward it along
        BIPSimpleApplication.confirmation(self, apdu)

    def indication(self, apdu):
        if _debug: WhoIsIAmApplication._debug("indication %r", apdu)

        if (isinstance(self._request, WhoIsRequest)) and (isinstance(apdu, IAmRequest)):
            device_type, device_instance = apdu.iAmDeviceIdentifier
            if device_type != 'device':
                raise DecodingError("invalid object type")

            if (self._request.deviceInstanceRangeLowLimit is not None) and \
                    (device_instance < self._request.deviceInstanceRangeLowLimit):
                pass
            elif (self._request.deviceInstanceRangeHighLimit is not None) and \
                    (device_instance > self._request.deviceInstanceRangeHighLimit):
                pass
            else:
                # print out the contents
                sys.stdout.write('pduSource = ' + repr(apdu.pduSource) + '\n')
                sys.stdout.write('iAmDeviceIdentifier = ' + str(apdu.iAmDeviceIdentifier) + '\n')
                sys.stdout.write('maxAPDULengthAccepted = ' + str(apdu.maxAPDULengthAccepted) + '\n')
                sys.stdout.write('segmentationSupported = ' + str(apdu.segmentationSupported) + '\n')
                sys.stdout.write('vendorID = ' + str(apdu.vendorID) + '\n')
                sys.stdout.flush()

        # forward it along
        BIPSimpleApplication.indication(self, apdu)

#
#   WhoIsIAmConsoleCmd
#

@bacpypes_debugging
class WhoIsIAmConsoleCmd(ConsoleCmd):

    def do_whois(self, args):
        """whois [ <addr>] [ <lolimit> <hilimit> ]"""
        args = args.split()
        if _debug: WhoIsIAmConsoleCmd._debug("do_whois %r", args)

        try:
            # build a request
            request = WhoIsRequest()
            if (len(args) == 1) or (len(args) == 3):
                request.pduDestination = Address(args[0])
                del args[0]
            else:
                request.pduDestination = GlobalBroadcast()

            if len(args) == 2:
                request.deviceInstanceRangeLowLimit = int(args[0])
                request.deviceInstanceRangeHighLimit = int(args[1])
            if _debug: WhoIsIAmConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: WhoIsIAmConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

        except Exception as err:
            WhoIsIAmConsoleCmd._exception("exception: %r", err)

    def do_iam(self, args):
        """iam"""
        args = args.split()
        if _debug: WhoIsIAmConsoleCmd._debug("do_iam %r", args)

        try:
            # build a request
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = this_device.objectIdentifier
            request.maxAPDULengthAccepted = this_device.maxApduLengthAccepted
            request.segmentationSupported = this_device.segmentationSupported
            request.vendorID = this_device.vendorIdentifier
            if _debug: WhoIsIAmConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: WhoIsIAmConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

        except Exception as err:
            WhoIsIAmConsoleCmd._exception("exception: %r", err)

    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug: WhoIsIAmConsoleCmd._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        this_application.nsap.update_router_references(None, router_address, network_list)


#
#   main
#

def main():
    global this_device, this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = WhoIsIAmApplication(
        this_device, args.ini.address,
        )
    if _debug: _log.debug("    - this_application: %r", this_application)

    # make a console
    this_console = WhoIsIAmConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
