#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for read commands
which create ReadPropertyRequest PDUs, then lines up the coorresponding ReadPropertyACK
and prints the value.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype

from bacpypes.apdu import ReadPropertyMultipleRequest, PropertyReference, \
    ReadAccessSpecification, ReadPropertyMultipleACK
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.basetypes import PropertyIdentifier

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   ReadPropertyMultipleConsoleCmd
#

class ReadPropertyMultipleConsoleCmd(ConsoleCmd):

    def do_read(self, args):
        """read <addr> ( <type> <inst> ( <prop> [ <indx> ] )... )..."""
        args = args.split()
        if _debug: ReadPropertyMultipleConsoleCmd._debug("do_read %r", args)

        try:
            i = 0
            addr = args[i]
            i += 1

            read_access_spec_list = []
            while i < len(args):
                obj_type = args[i]
                i += 1

                if obj_type.isdigit():
                    obj_type = int(obj_type)
                elif not get_object_class(obj_type):
                    raise ValueError("unknown object type")

                obj_inst = int(args[i])
                i += 1

                prop_reference_list = []
                while i < len(args):
                    prop_id = args[i]
                    if prop_id not in PropertyIdentifier.enumerations:
                        break

                    i += 1
                    if prop_id in ('all', 'required', 'optional'):
                        pass
                    else:
                        datatype = get_datatype(obj_type, prop_id)
                        if not datatype:
                            raise ValueError("invalid property for object type")

                    # build a property reference
                    prop_reference = PropertyReference(
                        propertyIdentifier=prop_id,
                        )

                    # check for an array index
                    if (i < len(args)) and args[i].isdigit():
                        prop_reference.propertyArrayIndex = int(args[i])
                        i += 1

                    # add it to the list
                    prop_reference_list.append(prop_reference)

                # check for at least one property
                if not prop_reference_list:
                    raise ValueError("provide at least one property")

                # build a read access specification
                read_access_spec = ReadAccessSpecification(
                    objectIdentifier=(obj_type, obj_inst),
                    listOfPropertyReferences=prop_reference_list,
                    )

                # add it to the list
                read_access_spec_list.append(read_access_spec)

            # check for at least one
            if not read_access_spec_list:
                raise RuntimeError("at least one read access specification required")

            # build the request
            request = ReadPropertyMultipleRequest(
                listOfReadAccessSpecs=read_access_spec_list,
                )
            request.pduDestination = Address(addr)
            if _debug: ReadPropertyMultipleConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: ReadPropertyMultipleConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, ReadPropertyMultipleACK):
                    if _debug: ReadPropertyMultipleConsoleCmd._debug("    - not an ack")
                    return

                # loop through the results
                for result in apdu.listOfReadAccessResults:
                    # here is the object identifier
                    objectIdentifier = result.objectIdentifier
                    if _debug: ReadPropertyMultipleConsoleCmd._debug("    - objectIdentifier: %r", objectIdentifier)

                    # now come the property values per object
                    for element in result.listOfResults:
                        # get the property and array index
                        propertyIdentifier = element.propertyIdentifier
                        if _debug: ReadPropertyMultipleConsoleCmd._debug("    - propertyIdentifier: %r", propertyIdentifier)
                        propertyArrayIndex = element.propertyArrayIndex
                        if _debug: ReadPropertyMultipleConsoleCmd._debug("    - propertyArrayIndex: %r", propertyArrayIndex)

                        # here is the read result
                        readResult = element.readResult

                        sys.stdout.write(propertyIdentifier)
                        if propertyArrayIndex is not None:
                            sys.stdout.write("[" + str(propertyArrayIndex) + "]")

                        # check for an error
                        if readResult.propertyAccessError is not None:
                            sys.stdout.write(" ! " + str(readResult.propertyAccessError) + '\n')

                        else:
                            # here is the value
                            propertyValue = readResult.propertyValue

                            # find the datatype
                            datatype = get_datatype(objectIdentifier[0], propertyIdentifier)
                            if _debug: ReadPropertyMultipleConsoleCmd._debug("    - datatype: %r", datatype)
                            if not datatype:
                                raise TypeError("unknown datatype")

                            # special case for array parts, others are managed by cast_out
                            if issubclass(datatype, Array) and (propertyArrayIndex is not None):
                                if propertyArrayIndex == 0:
                                    value = propertyValue.cast_out(Unsigned)
                                else:
                                    value = propertyValue.cast_out(datatype.subtype)
                            else:
                                value = propertyValue.cast_out(datatype)
                            if _debug: ReadPropertyMultipleConsoleCmd._debug("    - value: %r", value)

                            sys.stdout.write(" = " + str(value) + '\n')
                        sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception, error:
            ReadPropertyMultipleConsoleCmd._exception("exception: %r", error)

bacpypes_debugging(ReadPropertyMultipleConsoleCmd)

#
#   __main__
#

def main():
    global this_application

    # check the version
    if (sys.version_info[:2] != (2, 5)):
        sys.stderr.write("Python 2.5 only\n")
        sys.exit(1)

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
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = ReadPropertyMultipleConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
