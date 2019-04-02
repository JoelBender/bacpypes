#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for read commands
which create ReadPropertyRequest PDUs, waits for the response, then decodes the
value if it is application encoded.  This is useful for reading the values
of propietary properties when the datatype isn't known.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address

from bacpypes.apdu import ReadPropertyRequest
from bacpypes.primitivedata import Tag, ObjectIdentifier
from bacpypes.constructeddata import ArrayOf

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   ReadPropertyAnyConsoleCmd
#

@bacpypes_debugging
class ReadPropertyAnyConsoleCmd(ConsoleCmd):

    def do_read(self, args):
        """read <addr> <objid> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: ReadPropertyAnyConsoleCmd._debug("do_read %r", args)

        try:
            addr, obj_id, prop_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 4:
                request.propertyArrayIndex = int(args[3])
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse
                if _debug: ReadPropertyAnyConsoleCmd._debug("    - apdu: %r", apdu)

                try:
                    tag_list = apdu.propertyValue.tagList

                    # all tags application encoded
                    non_app_tags = [tag for tag in tag_list if tag.tagClass != Tag.applicationTagClass]
                    if non_app_tags:
                        raise RuntimeError("value has some non-application tags")

                    # all the same type
                    first_tag = tag_list[0]
                    other_type_tags = [tag for tag in tag_list[1:] if tag.tagNumber != first_tag.tagNumber]
                    if other_type_tags:
                        raise RuntimeError("all the tags must be the same type")

                    # find the datatype
                    datatype = Tag._app_tag_class[first_tag.tagNumber]
                    if _debug: ReadPropertyAnyConsoleCmd._debug("    - datatype: %r", datatype)
                    if not datatype:
                        raise RuntimeError("unknown datatype")

                    # more than one then it's an array of these
                    if len(tag_list) > 1:
                        datatype = ArrayOf(datatype)
                        if _debug: ReadPropertyAnyConsoleCmd._debug("    - array: %r", datatype)

                    # cast out the value
                    value = apdu.propertyValue.cast_out(datatype)
                    if _debug: ReadPropertyAnyConsoleCmd._debug("    - value: %r", value)

                    sys.stdout.write("%s (%s)\n" % (value, datatype))
                except RuntimeError as err:
                    sys.stdout.write("error: %s\n" % (err,))

                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            ReadPropertyAnyConsoleCmd._exception("exception: %r", error)

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

    # provide max segments accepted if any kind of segmentation supported
    if args.ini.segmentationsupported != 'noSegmentation':
        this_device.maxSegmentsAccepted = int(args.ini.maxsegmentsaccepted)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)
    if _debug: _log.debug("    - this_application: %r", this_application)

    # make a console
    this_console = ReadPropertyAnyConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
