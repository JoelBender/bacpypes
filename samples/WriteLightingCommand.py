#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for commands.
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
    SimpleAckPDU,
    ReadPropertyRequest,
    ReadPropertyACK,
    WritePropertyRequest,
)
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array, Any
from bacpypes.basetypes import LightingCommand

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   WriteLightingConsoleCmd
#


@bacpypes_debugging
class WriteLightingConsoleCmd(ConsoleCmd):
    def do_read(self, args):
        """read <addr> <objid> <prop> [ <indx> ]"""
        args = args.split()
        if _debug:
            WriteLightingConsoleCmd._debug("do_read %r", args)

        try:
            addr, obj_id, prop_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value

            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id, propertyIdentifier=prop_id
            )
            request.pduDestination = Address(addr)

            if len(args) == 4:
                request.propertyArrayIndex = int(args[3])
            if _debug:
                WriteLightingConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                WriteLightingConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, ReadPropertyACK):
                    if _debug:
                        WriteLightingConsoleCmd._debug("    - not an ack")
                    return

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    WriteLightingConsoleCmd._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (
                    apdu.propertyArrayIndex is not None
                ):
                    if apdu.propertyArrayIndex == 0:
                        value = apdu.propertyValue.cast_out(Unsigned)
                    else:
                        value = apdu.propertyValue.cast_out(datatype.subtype)
                else:
                    value = apdu.propertyValue.cast_out(datatype)
                if _debug:
                    WriteLightingConsoleCmd._debug("    - value: %r", value)

                sys.stdout.write(str(value) + "\n")
                if hasattr(value, "debug_contents"):
                    value.debug_contents(file=sys.stdout)
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + "\n")

        except Exception as error:
            WriteLightingConsoleCmd._exception("exception: %r", error)

    def do_write(self, args):
        """write <addr> <objid> <prop> <operation> [ ... ]"""
        args = args.split()
        if _debug:
            WriteLightingConsoleCmd._debug("do_write %r", args)

        try:
            addr = args.pop(0)
            obj_id = ObjectIdentifier(args.pop(0)).value
            prop_id = args.pop(0)

            if obj_id[0] != "lightingOutput":
                raise ValueError("lightingOutput")
            if prop_id != "lightingCommand":
                raise ValueError("lightingCommand")
            if not args:
                raise ValueError("operation required")

            value = LightingCommand()
            value.operation = operation = args.pop(0)

            if operation == "fadeTo":
                if not args:
                    raise ValueError("target level required")
                value.targetLevel = float(args.pop(0))

                if args:
                    value.priority = int(args.pop(0))
                if args:
                    value.fadeTime = int(args.pop(0))

            elif operation == "rampTo":
                if not args:
                    raise ValueError("target level required")
                value.targetLevel = float(args.pop(0))

                if args:
                    value.priority = int(args.pop(0))
                if args:
                    value.rampRate = float(args.pop(0))

            elif operation == "stepUp":
                if args:
                    value.priority = int(args.pop(0))
                if args:
                    value.stepIncrement = float(args.pop(0))

            elif operation == "stepDown":
                if args:
                    value.priority = int(args.pop(0))
                if args:
                    value.stepIncrement = float(args.pop(0))

            elif operation == "stepOn":
                if args:
                    value.priority = int(args.pop(0))
                if args:
                    value.stepIncrement = float(args.pop(0))

            elif operation == "stepOff":
                if args:
                    value.priority = int(args.pop(0))
                if args:
                    value.stepIncrement = float(args.pop(0))

            elif operation == "warn":
                if args:
                    value.priority = int(args.pop(0))

            elif operation == "warnOff":
                if args:
                    value.priority = int(args.pop(0))

            elif operation == "warnRelinquish":
                if args:
                    value.priority = int(args.pop(0))

            elif operation == "stop":
                if args:
                    value.priority = int(args.pop(0))

            else:
                raise ValueError("invalid operation")

            if (value.targetLevel is not None) and not (
                0.0 <= value.targetLevel <= 100.0
            ):
                raise ValueError("invalid target level (0.0..100.0)")
            if (value.rampRate is not None) and not (0.0 <= value.rampRate <= 100.0):
                raise ValueError("invalid ramp rate (0.0..100.0)")
            if (value.stepIncrement is not None) and not (
                0.1 <= value.stepIncrement <= 100.0
            ):
                raise ValueError("invalid step increment (0.1..100.0)")
            if (value.fadeTime is not None) and not (100 <= value.fadeTime <= 86400000):
                raise ValueError("invalid fade time (100..86400000)")
            if (value.priority is not None) and not (1 <= value.priority <= 16):
                raise ValueError("invalid priority (1..16)")

            if _debug:
                WriteLightingConsoleCmd._debug("    - value: %r", value)

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=obj_id, propertyIdentifier=prop_id
            )
            request.pduDestination = Address(addr)

            # save the value
            request.propertyValue = Any()
            try:
                request.propertyValue.cast_in(value)
            except Exception as error:
                WriteLightingConsoleCmd._exception(
                    "WriteProperty cast error: %r", error
                )
            if _debug:
                WriteLightingConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                WriteLightingConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                # should be an ack
                if not isinstance(iocb.ioResponse, SimpleAckPDU):
                    if _debug:
                        WriteLightingConsoleCmd._debug("    - not an ack")
                    return

                sys.stdout.write("ack\n")

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + "\n")

        except Exception as error:
            WriteLightingConsoleCmd._exception("exception: %r", error)

    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug:
            WriteLightingConsoleCmd._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        this_application.nsap.update_router_references(
            None, router_address, network_list
        )


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
    this_console = WriteLightingConsoleCmd()
    if _debug:
        _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
