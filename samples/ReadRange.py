#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for readrange
commands which create ReadRangeRequest PDUs, then lines up the coorresponding
ReadRangeACK and prints the value.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_datatype
from bacpypes.apdu import (
    ReadRangeRequest,
    Range,
    RangeByPosition,
    RangeBySequenceNumber,
    RangeByTime,
    ReadRangeACK,
)

from bacpypes.app import BIPSimpleApplication
from bacpypes.primitivedata import Date, Time, ObjectIdentifier
from bacpypes.constructeddata import Array, List
from bacpypes.basetypes import DateTime
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   ReadRangeConsoleCmd
#


@bacpypes_debugging
class ReadRangeConsoleCmd(ConsoleCmd):
    def do_readrange(self, args):
        """readrange <addr> <objid> <prop> [ <indx> ]
            [ p <indx> <count> ]
            [ s <seq> <count> ]
            [ t <date> <time> <count> ]
        """
        args = args.split()
        if _debug:
            ReadRangeConsoleCmd._debug("do_readrange %r", args)

        try:
            addr = Address(args.pop(0))
            obj_id = ObjectIdentifier(args.pop(0)).value
            prop_id = args.pop(0)

            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadRangeRequest(
                destination=addr, objectIdentifier=obj_id, propertyIdentifier=prop_id
            )

            # index is optional
            if args:
                if args[0].isdigit():
                    if not issubclass(datatype, Array):
                        raise ValueError("property is not an array")
                    request.propertyArrayIndex = int(args.pop(0))
                    datatype = datatype.subtype
            if not issubclass(datatype, List):
                raise ValueError("property is not a list")

            # range is optional
            if args:
                range_type = args.pop(0)
                if range_type == "p":
                    rbp = RangeByPosition(
                        referenceIndex=int(args[0]), count=int(args[1])
                    )
                    request.range = Range(byPosition=rbp)
                elif range_type == "s":
                    rbs = RangeBySequenceNumber(
                        referenceSequenceNumber=int(args[0]), count=int(args[1])
                    )
                    request.range = Range(bySequenceNumber=rbs)
                elif range_type == "t":
                    rbt = RangeByTime(
                        referenceTime=DateTime(
                            date=Date(args[0]).value, time=Time(args[1]).value
                        ),
                        count=int(args[2]),
                    )
                    request.range = Range(byTime=rbt)
                elif range_type == "x":
                    # should be missing required parameter
                    request.range = Range()
                else:
                    raise ValueError("unknown range type: %r" % (range_type,))

            if _debug:
                ReadRangeConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                ReadRangeConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse
                if _debug:
                    ReadRangeConsoleCmd._debug("    - apdu: %r", apdu)

                # should be an ack
                if not isinstance(apdu, ReadRangeACK):
                    if _debug:
                        ReadRangeConsoleCmd._debug("    - not an ack")
                    return

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    ReadRangeConsoleCmd._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                sys.stdout.write(
                    "firstSequenceNumber: %s\n" % (apdu.firstSequenceNumber,)
                )
                sys.stdout.write("resultFlags: %s\n" % (apdu.resultFlags,))

                # cast out the data into a list
                value = apdu.itemData.cast_out(datatype)

                # dump it out
                for i, item in enumerate(value):
                    sys.stdout.write("[%d]\n" % (i,))
                    item.debug_contents(file=sys.stdout, indent=2)
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + "\n")

        except Exception as error:
            ReadRangeConsoleCmd._exception("exception: %r", error)


#
#   __main__
#


def main():
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a console
    this_console = ReadRangeConsoleCmd()
    if _debug:
        _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
