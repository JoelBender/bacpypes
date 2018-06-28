#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for Who-Is and I-Am
commands which create the related APDUs, then for each I-Am that is returned, reads
the object name of the device object (often called simply the device name).
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import WhoIsRequest, ReadPropertyRequest, ReadPropertyACK
from bacpypes.primitivedata import CharacterString
from bacpypes.errors import MissingRequiredParameter

from bacpypes.app import BIPForeignApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 1
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None

#
#   DiscoveryApplication
#

@bacpypes_debugging
class DiscoveryApplication(BIPForeignApplication):

    def __init__(self, *args):
        if _debug: DiscoveryApplication._debug("__init__ %r", args)
        BIPForeignApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self.who_is_request = None

    def request(self, apdu):
        """Sniff for Who-Is requests going downstream."""
        if _debug: DiscoveryApplication._debug("request %r", apdu)

        # save a copy of just the Who-Is request
        if isinstance(apdu, WhoIsRequest):
            self.who_is_request = apdu

        # forward it along
        BIPForeignApplication.request(self, apdu)

    def do_IAmRequest(self, apdu):
        """Do something with incoming I-Am requests."""
        if _debug: DiscoveryApplication._debug("do_IAmRequest %r", apdu)

        # check for required parameters
        if apdu.iAmDeviceIdentifier is None:
            raise MissingRequiredParameter("iAmDeviceIdentifier required")
        if apdu.maxAPDULengthAccepted is None:
            raise MissingRequiredParameter("maxAPDULengthAccepted required")
        if apdu.segmentationSupported is None:
            raise MissingRequiredParameter("segmentationSupported required")
        if apdu.vendorID is None:
            raise MissingRequiredParameter("vendorID required")

        # extract the device instance number
        device_instance = apdu.iAmDeviceIdentifier[1]
        if _debug: DiscoveryApplication._debug("    - device_instance: %r", device_instance)

        # extract the source address
        device_address = apdu.pduSource
        if _debug: DiscoveryApplication._debug("    - device_address: %r", device_address)

        # we didn't request anything yet
        if not self.who_is_request:
            return

        if (self.who_is_request.deviceInstanceRangeLowLimit is not None) and \
                (device_instance < self.who_is_request.deviceInstanceRangeLowLimit):
            pass
        elif (self.who_is_request.deviceInstanceRangeHighLimit is not None) and \
                (device_instance > self.who_is_request.deviceInstanceRangeHighLimit):
            pass
        else:
            # build a request for the object name
            request = ReadPropertyRequest(
                destination=apdu.pduSource,
                objectIdentifier=apdu.iAmDeviceIdentifier,
                propertyIdentifier='objectName',
                )

            # make an IOCB
            iocb = IOCB(request)
            if _debug: DiscoveryApplication._debug("    - iocb: %r", iocb)

            # let us know when its complete
            iocb.add_callback(self.device_discovered)

            # give it to the application
            self.request_io(iocb)

    def device_discovered(self, iocb):
        if _debug: DiscoveryApplication._debug("device_discovered %r", iocb)

        # do something for error/reject/abort
        if iocb.ioError:
            sys.stdout.write(str(iocb.ioError) + '\n')

        # do something for success
        elif iocb.ioResponse:
            apdu = iocb.ioResponse

            # should be an ack
            if not isinstance(apdu, ReadPropertyACK):
                if _debug: DiscoveryApplication._debug("    - not an ack")
                return

            # pull out the name
            device_name = apdu.propertyValue.cast_out(CharacterString)
            if _debug: DiscoveryApplication._debug("    - device_name: %r", device_name)

            # print out the response
            sys.stdout.write("%s is at %s named %r\n" % (apdu.objectIdentifier[1], apdu.pduSource, device_name))

        # do something with nothing?
        else:
            if _debug: DiscoveryApplication._debug("    - ioError or ioResponse expected")


#
#   DiscoveryConsoleCmd
#

@bacpypes_debugging
class DiscoveryConsoleCmd(ConsoleCmd):

    def do_whois(self, args):
        """whois [ <addr> ] [ <lolimit> <hilimit> ]"""
        args = args.split()
        if _debug: DiscoveryConsoleCmd._debug("do_whois %r", args)

        try:
            # gather the parameters
            if (len(args) == 1) or (len(args) == 3):
                addr = Address(args[0])
                del args[0]
            else:
                addr = GlobalBroadcast()

            if len(args) == 2:
                lolimit = int(args[0])
                hilimit = int(args[1])
            else:
                lolimit = hilimit = None

            # code lives in the device service
            this_application.who_is(lolimit, hilimit, addr)

        except Exception as error:
            DiscoveryConsoleCmd._exception("exception: %r", error)

    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug: DiscoveryConsoleCmd._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        this_application.nsap.add_router_references(None, router_address, network_list)


#
#   __main__
#

def main():
    global this_device
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = DiscoveryApplication(
        this_device, args.ini.address,
        Address(args.ini.foreignbbmd),
        int(args.ini.foreignttl),
        )

    # make a console
    this_console = DiscoveryConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
