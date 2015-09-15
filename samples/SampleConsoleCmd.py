#!/usr/bin/python

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

from bacpypes.core import run

from bacpypes.app import LocalDeviceObject, BIPSimpleApplication

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None
this_console = None

#
#   SampleApplication
#

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

bacpypes_debugging(SampleApplication)

#
#   SampleConsoleCmd
#

class SampleConsoleCmd(ConsoleCmd):

    def do_nothing(self, args):
        """nothing can be done"""
        args = args.split()
        if _debug: SampleConsoleCmd._debug("do_nothing %r", args)

bacpypes_debugging(SampleConsoleCmd)

#
#   __main__
#

try:
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
    this_console = SampleConsoleCmd()

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")

