#!/usr/bin/env python

"""
This application demonstrates writing a series of values at a regular interval.

    $ python RecurringWriteProperty.py 1.2.3.4 analogValue:1 \
        presentValue 1.2 3.4 5.6
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred
from bacpypes.task import RecurringTask
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.primitivedata import Real, ObjectIdentifier
from bacpypes.constructeddata import Any
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None
this_application = None


@bacpypes_debugging
class PrairieDog(RecurringTask):

    """
    An instance of this class pops up out of the ground every once in a
    while and write out the next value.
    """

    def __init__(self, interval):
        if _debug:
            PrairieDog._debug("__init__ %r", interval)
        RecurringTask.__init__(self, interval)

        # install it
        self.install_task()

    def process_task(self):
        if _debug:
            PrairieDog._debug("process_task")
        global args, this_application

        if _debug:
            PrairieDog._debug("    - args.values: %r", args.values)

        # pick up the next value
        value = args.values.pop(0)
        args.values.append(value)

        # make a primitive value out of it
        value = Real(float(value))

        # build a request
        request = WritePropertyRequest(
            destination=args.daddr,
            objectIdentifier=args.objid,
            propertyIdentifier=args.propid,
        )

        # save the value, application tagged
        request.propertyValue = Any()
        request.propertyValue.cast_in(value)
        if _debug:
            PrairieDog._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        iocb.add_callback(self.write_complete)
        if _debug:
            PrairieDog._debug("    - iocb: %r", iocb)

        # give it to the application to process
        deferred(this_application.request_io, iocb)

    def write_complete(self, iocb):
        if _debug:
            PrairieDog._debug("write_complete %r", iocb)

        # do something for success
        if iocb.ioResponse:
            # should be an ack
            if not isinstance(iocb.ioResponse, SimpleAckPDU):
                if _debug:
                    PrairieDog._debug("    - not an ack")
            else:
                sys.stdout.write("ack\n")

        # do something for error/reject/abort
        elif iocb.ioError:
            sys.stdout.write(str(iocb.ioError) + "\n")


def main():
    global args, this_application

    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an argument for seconds per dog
    parser.add_argument("daddr", help="destination address")
    parser.add_argument("objid", help="object identifier")
    parser.add_argument("propid", help="property identifier")

    # list of values to write
    parser.add_argument("values", metavar="N", nargs="+", help="values to write")

    # add an argument for seconds between writes
    parser.add_argument(
        "--delay", type=float, help="delay between writes in seconds", default=5.0
    )

    # now parse the arguments
    args = parser.parse_args()

    # convert the parameters
    args.daddr = Address(args.daddr)
    args.objid = ObjectIdentifier(args.objid).value
    args.propid = PropertyIdentifier(args.propid).value

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

    # make a dog, task scheduling is in milliseconds
    dog = PrairieDog(args.delay * 1000)
    if _debug:
        _log.debug("    - dog: %r", dog)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
