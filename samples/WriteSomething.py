#!/usr/bin/env python

"""
This application is a special example of building a custom data structure
to be written to a proprietary property of a proprietary object.  Unlike the
other 'write property' sample applications, this one make no attempt to
translate keywords into object types and property identifiers, it only takes
integers.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

from bacpypes.pdu import Address
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication

from bacpypes.primitivedata import TagList, OpeningTag, ClosingTag, ContextTag
from bacpypes.constructeddata import Any
from bacpypes.apdu import WritePropertyRequest, Error, AbortPDU, SimpleAckPDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   WriteSomethingApplication
#

@bacpypes_debugging
class WriteSomethingApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: WriteSomethingApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None

    def request(self, apdu):
        if _debug: WriteSomethingApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu

        # forward it along
        BIPSimpleApplication.request(self, apdu)

    def confirmation(self, apdu):
        if _debug: WriteSomethingApplication._debug("confirmation %r", apdu)

        if isinstance(apdu, Error):
            sys.stdout.write("error: %s\n" % (apdu.errorCode,))
            sys.stdout.flush()

        elif isinstance(apdu, AbortPDU):
            apdu.debug_contents()

        elif isinstance(apdu, SimpleAckPDU):
            sys.stdout.write("ack\n")
            sys.stdout.flush()


#
#   WriteSomethingConsoleCmd
#

@bacpypes_debugging
class WriteSomethingConsoleCmd(ConsoleCmd):

    def do_write(self, args):
        """write <addr> <type> <inst> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: WriteSomethingConsoleCmd._debug("do_write %r", args)

        try:
            addr, obj_type, obj_inst, prop_id = args[:4]

            obj_type = int(obj_type)
            obj_inst = int(obj_inst)
            prop_id = int(prop_id)

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])

            # build a custom datastructure
            tag_list = TagList([
                OpeningTag(1),
                ContextTag(0, xtob('9c40')),
                ContextTag(1, xtob('02')),
                ContextTag(2, xtob('02')),
                ClosingTag(1)
                ])
            if _debug: WriteSomethingConsoleCmd._debug("    - tag_list: %r", tag_list)

            # stuff the tag list into an Any
            request.propertyValue = Any()
            request.propertyValue.decode(tag_list)

            if _debug: WriteSomethingConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            this_application.request(request)

        except Exception as error:
            WriteSomethingConsoleCmd._exception("exception: %r", error)


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
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a simple application
    this_application = WriteSomethingApplication(this_device, args.ini.address)
    if _debug: _log.debug("    - this_application: %r", this_application)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = WriteSomethingConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
