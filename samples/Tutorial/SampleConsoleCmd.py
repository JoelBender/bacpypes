#!/usr/bin/env python

"""
This sample application is a simple BACpypes application that
presents a console prompt.  Almost identical to the SampleApplication,
the BACnet application is minimal, but with the console commands
that match the command line options like 'buggers' and 'debug' the
user can add debugging "on the fly".
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   SampleApplication
#

@bacpypes_debugging
class SampleApplication(BIPSimpleApplication):

    def __init__(self, device, address):
        if _debug: SampleApplication._debug("__init__ %r %r", device, address)
        BIPSimpleApplication.__init__(self, device, address)

    def request(self, apdu):
        if _debug: SampleApplication._debug("request %r", apdu)
        BIPSimpleApplication.request(self, apdu)

    def indication(self, apdu):
        if _debug: SampleApplication._debug("indication %r", apdu)
        BIPSimpleApplication.indication(self, apdu)

    def response(self, apdu):
        if _debug: SampleApplication._debug("response %r", apdu)
        BIPSimpleApplication.response(self, apdu)

    def confirmation(self, apdu):
        if _debug: SampleApplication._debug("confirmation %r", apdu)
        BIPSimpleApplication.confirmation(self, apdu)


#
#   SampleConsoleCmd
#

@bacpypes_debugging
class SampleConsoleCmd(ConsoleCmd):

    def do_nothing(self, args):
        """nothing can be done"""
        args = args.split()
        if _debug: SampleConsoleCmd._debug("do_nothing %r", args)
            
#
#   __main__
#

def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    this_application = SampleApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = SampleConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
