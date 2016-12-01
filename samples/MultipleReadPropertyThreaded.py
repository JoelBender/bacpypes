#!/usr/bin/env python

"""
Mutliple Read Property

This application has a static list of points that it would like to read.  It reads the
values of each of them in turn and then quits.
"""

from collections import deque
from threading import Thread

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, stop, deferred
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import ReadPropertyRequest
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

# point list, set according to your device
point_list = [
    ('10.0.1.14', 'analogValue', 1, 'presentValue'),
    ('10.0.1.14', 'analogValue', 2, 'presentValue'),
    ]

#
#   ReadPointListThread
#

@bacpypes_debugging
class ReadPointListThread(Thread):

    def __init__(self, point_list):
        if _debug: ReadPointListThread._debug("__init__ %r", point_list)
        Thread.__init__(self)

        # turn the point list into a queue
        self.point_queue = deque(point_list)

        # make a list of the response values
        self.response_values = []

    def run(self):
        if _debug: ReadPointListThread._debug("run")
        global this_application

        # loop through the points
        for addr, obj_type, obj_inst, prop_id in self.point_queue:
            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)
            if _debug: ReadPointListThread._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: ReadPointListThread._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for the response
            iocb.wait()

            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # find the datatype
                datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
                if _debug: ReadPointListThread._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                    if apdu.propertyArrayIndex == 0:
                        value = apdu.propertyValue.cast_out(Unsigned)
                    else:
                        value = apdu.propertyValue.cast_out(datatype.subtype)
                else:
                    value = apdu.propertyValue.cast_out(datatype)
                if _debug: ReadPointListThread._debug("    - value: %r", value)

                # save the value
                self.response_values.append(value)

            if iocb.ioError:
                if _debug: ReadPointListThread._debug("    - error: %r", iocb.ioError)
                self.response_values.append(iocb.ioError)

        # done
        stop()

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
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # create a thread and
    read_thread = ReadPointListThread(point_list)
    if _debug: _log.debug("    - read_thread: %r", read_thread)

    # start it running when the core is running
    deferred(read_thread.start)

    _log.debug("running")

    run()

    # dump out the results
    for request, response in zip(point_list, read_thread.response_values):
        print(request, response)

    _log.debug("fini")


if __name__ == "__main__":
    main()
