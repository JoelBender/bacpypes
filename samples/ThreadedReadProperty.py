#!/usr/bin/env python

"""
Threaded Read Property

This application has a static list of points that it would like to read.  It
starts a thread for each unique device address and reads the points for that
device.
"""

from threading import Thread

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, stop, deferred
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import ReadPropertyRequest
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

# point list, set according to your devices
point_list = [
    ('10.0.1.14', [
        ('analogValue:1', 'presentValue'),
        ('analogValue:2', 'presentValue'),
        ]),
    ('10.0.1.15', [
        ('analogValue:1', 'presentValue'),
        ('analogValue:2', 'presentValue'),
        ]),
    ]

#
#   ReadPointListThread
#

@bacpypes_debugging
class ReadPointListThread(Thread):

    def __init__(self, device_address, point_list):
        if _debug: ReadPointListThread._debug("__init__ %r %r", device_address, point_list)
        Thread.__init__(self)

        # save the address
        self.device_address = Address(device_address)

        # turn the point list into a queue
        self.point_list = point_list

        # make a list of the response values
        self.response_values = []

    def run(self):
        if _debug: ReadPointListThread._debug("run")
        global this_application

        # loop through the points
        for obj_id, prop_id in self.point_list:
            obj_id = ObjectIdentifier(obj_id).value

            # build a request
            request = ReadPropertyRequest(
                destination=self.device_address,
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id,
                )
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

        if _debug: ReadPointListThread._debug("    - fini")


#
#   ThreadSupervisor
#

@bacpypes_debugging
class ThreadSupervisor(Thread):

    def __init__(self, thread_list):
        if _debug: ThreadSupervisor._debug("__init__ ...")
        Thread.__init__(self)

        self.thread_list = thread_list

    def run(self):
        if _debug: ThreadSupervisor._debug("run")

        # start them up
        for read_thread in self.thread_list:
            read_thread.start()
        if _debug: ThreadSupervisor._debug("    - all started")

        # wait for them to finish
        for read_thread in self.thread_list:
            read_thread.join()
        if _debug: ThreadSupervisor._debug("    - all finished")

        # stop the core
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
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    thread_list = []

    # loop through the address and point lists
    for addr, points in point_list:
        # create a thread
        read_thread = ReadPointListThread(addr, points)
        if _debug: _log.debug("    - read_thread: %r", read_thread)
        thread_list.append(read_thread)

    # create a thread supervisor
    thread_supervisor = ThreadSupervisor(thread_list)

    # start it running when the core is running
    deferred(thread_supervisor.start)

    _log.debug("running")

    run()

    # dump out the results
    for read_thread in thread_list:
        for request, response in zip(read_thread.point_list, read_thread.response_values):
            print(request, response)

    _log.debug("fini")


if __name__ == "__main__":
    main()

