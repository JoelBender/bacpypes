#!/usr/bin/python

"""
This application presents a 'console' prompt to the user asking for read commands
which create ReadPropertyRequest PDUs, then lines up the coorresponding ReadPropertyACK
and prints the value.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run

from bacpypes.pdu import Address
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype

from bacpypes.apdu import ReadPropertyRequest, Error, AbortPDU, ReadPropertyACK
from bacpypes.primitivedata import Tag
from bacpypes.constructeddata import Array
from bacpypes.basetypes import ServicesSupported

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None
this_console = None

#
#   ReadPropertyAnyApplication
#

class ReadPropertyAnyApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: ReadPropertyAnyApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None

    def request(self, apdu):
        if _debug: ReadPropertyAnyApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu

        # forward it along
        BIPSimpleApplication.request(self, apdu)

    def confirmation(self, apdu):
        if _debug: ReadPropertyAnyApplication._debug("confirmation %r", apdu)

        if isinstance(apdu, Error):
            sys.stdout.write("error: %s\n" % (apdu.errorCode,))
            sys.stdout.flush()

        elif isinstance(apdu, AbortPDU):
            apdu.debug_contents()

        elif (isinstance(self._request, ReadPropertyRequest)) and (isinstance(apdu, ReadPropertyACK)):
            # peek at the value tag
            value_tag = apdu.propertyValue.tagList.Peek()
            if _debug: ReadPropertyAnyApplication._debug("    - value_tag: %r", value_tag)

            # make sure that it is application tagged
            if value_tag.tagClass != Tag.applicationTagClass:
                sys.stdout.write("value is not application encoded\n")

            else:
                # find the datatype
                datatype = Tag._app_tag_class[value_tag.tagNumber]
                if _debug: ReadPropertyAnyApplication._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError, "unknown datatype"

                # cast out the value
                value = apdu.propertyValue.cast_out(datatype)
                if _debug: ReadPropertyAnyApplication._debug("    - value: %r", value)

                sys.stdout.write(str(value) + '\n')

            sys.stdout.flush()

bacpypes_debugging(ReadPropertyAnyApplication)

#
#   ReadPropertyAnyConsoleCmd
#

class ReadPropertyAnyConsoleCmd(ConsoleCmd):

    def do_read(self, args):
        """read <addr> <type> <inst> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: ReadPropertyAnyConsoleCmd._debug("do_read %r", args)

        try:
            addr, obj_type, obj_inst, prop_id = args[:4]

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif not get_object_class(obj_type):
                raise ValueError, "unknown object type"

            obj_inst = int(obj_inst)

            if prop_id.isdigit():
                prop_id = int(prop_id)

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            this_application.request(request)

        except Exception as err:
            ReadPropertyAnyConsoleCmd._exception("exception: %r", err)

    def do_rt(self, args):
        """
        rt [ address [ net [ net ... ]]]

        positional arguments:
            address             router address
            net                 reachable network(s)

        Print, add, or remove internal routing table references.

        If the address and network(s) are not provided, the current contents
        of the routing table is printed out.
        """
        args = args.split()
        if _debug: ReadPropertyAnyConsoleCmd._debug("do_rt %r", args)

        # simplify the code a little
        nsap = this_application.nsap

        if not args:
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - print the contents")

            # loop through the router references, ignore the adapter
            for ref in nsap.routers.values():
                print("%s %s" % (ref.address, ref.networks))
        else:
            addr = Address(args[0])
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - addr: %r", addr)
            nets = [int(arg) for arg in args[1:]]
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - nets: %r", nets)

            if not nets:
                if _debug: ReadPropertyAnyConsoleCmd._debug("    - delete the router")

                nsap.remove_router_references(nsap.adapters[0], addr)
            else:
                if _debug: ReadPropertyAnyConsoleCmd._debug("    - add the references")

                nsap.add_router_references(nsap.adapters[0], addr, nets)

bacpypes_debugging(ReadPropertyAnyConsoleCmd)

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

    # make a simple application
    this_application = ReadPropertyAnyApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = ReadPropertyAnyConsoleCmd()

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")
