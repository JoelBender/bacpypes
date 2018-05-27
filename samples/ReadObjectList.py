#!/usr/bin/env python

"""
This application is given the device instance number of a device and its
address read the object list, then for each object, read the object name.
"""

from collections import deque

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred, stop
from bacpypes.iocb import IOCB

from bacpypes.primitivedata import ObjectIdentifier, CharacterString
from bacpypes.constructeddata import ArrayOf

from bacpypes.pdu import Address
from bacpypes.apdu import ReadPropertyRequest, ReadPropertyACK

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None

# convenience definition
ArrayOfObjectIdentifier = ArrayOf(ObjectIdentifier)

#
#   ObjectListContext
#

class ObjectListContext:

    def __init__(self, device_id, device_addr):
        self.device_id = device_id
        self.device_addr = device_addr

        self.object_list = []
        self.object_names = []

        self._object_list_queue = None

    def completed(self, had_error=None):
        if had_error:
            print("had error: %r" % (had_error,))
        else:
            for objid, objname in zip(self.object_list, self.object_names):
                print("%s: %s" % (objid, objname))

        stop()

#
#   ReadObjectListApplication
#

@bacpypes_debugging
class ReadObjectListApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: ReadObjectListApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

    def read_object_list(self, device_id, device_addr):
        if _debug: ReadObjectListApplication._debug("read_object_list %r %r", device_id, device_addr)

        # create a context to hold the results
        context = ObjectListContext(device_id, device_addr)

        # build a request for the object name
        request = ReadPropertyRequest(
            destination=context.device_addr,
            objectIdentifier=context.device_id,
            propertyIdentifier='objectList',
            )
        if _debug: ReadObjectListApplication._debug("    - request: %r", request)

        # make an IOCB, reference the context
        iocb = IOCB(request)
        iocb.context = context
        if _debug: ReadObjectListApplication._debug("    - iocb: %r", iocb)

        # let us know when its complete
        iocb.add_callback(self.object_list_results)

        # give it to the application
        self.request_io(iocb)

    def object_list_results(self, iocb):
        if _debug: ReadObjectListApplication._debug("object_list_results %r", iocb)

        # extract the context
        context = iocb.context

        # do something for error/reject/abort
        if iocb.ioError:
            context.completed(iocb.ioError)
            return

        # do something for success
        apdu = iocb.ioResponse

        # should be an ack
        if not isinstance(apdu, ReadPropertyACK):
            if _debug: ReadObjectListApplication._debug("    - not an ack")
            context.completed(RuntimeError("read property ack expected"))
            return

        # pull out the content
        object_list = apdu.propertyValue.cast_out(ArrayOfObjectIdentifier)
        if _debug: ReadObjectListApplication._debug("    - object_list: %r", object_list)

        # store it in the context
        context.object_list = object_list

        # make a queue of the identifiers to read, start reading them
        context._object_list_queue = deque(object_list)
        deferred(self.read_next_object, context)

    def read_next_object(self, context):
        if _debug: ReadObjectListApplication._debug("read_next_object %r", context)

        # if there's nothing more to do, we're done
        if not context._object_list_queue:
            if _debug: ReadObjectListApplication._debug("    - all done")
            context.completed()
            return

        # pop off the next object identifier
        object_id = context._object_list_queue.popleft()
        if _debug: ReadObjectListApplication._debug("    - object_id: %r", object_id)

        # build a request for the object name
        request = ReadPropertyRequest(
            destination=context.device_addr,
            objectIdentifier=object_id,
            propertyIdentifier='objectName',
            )
        if _debug: ReadObjectListApplication._debug("    - request: %r", request)

        # make an IOCB, reference the context
        iocb = IOCB(request)
        iocb.context = context
        if _debug: ReadObjectListApplication._debug("    - iocb: %r", iocb)

        # let us know when its complete
        iocb.add_callback(self.object_name_results)

        # give it to the application
        self.request_io(iocb)

    def object_name_results(self, iocb):
        if _debug: ReadObjectListApplication._debug("object_name_results %r", iocb)

        # extract the context
        context = iocb.context

        # do something for error/reject/abort
        if iocb.ioError:
            context.completed(iocb.ioError)
            return

        # do something for success
        apdu = iocb.ioResponse

        # should be an ack
        if not isinstance(apdu, ReadPropertyACK):
            if _debug: ReadObjectListApplication._debug("    - not an ack")
            context.completed(RuntimeError("read property ack expected"))
            return

        # pull out the name
        object_name = apdu.propertyValue.cast_out(CharacterString)
        if _debug: ReadObjectListApplication._debug("    - object_name: %r", object_name)

        # store it in the context
        context.object_names.append(object_name)

        # read the next one
        deferred(self.read_next_object, context)

#
#   __main__
#

def main():
    global this_device
    global this_application

    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an argument for interval
    parser.add_argument('device_id', type=int,
          help='device identifier',
          )

    # add an argument for interval
    parser.add_argument('device_addr', type=str,
          help='device address',
          )

    # parse the args
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = ReadObjectListApplication(this_device, args.ini.address)

    # build a device object identifier
    device_id = ('device', args.device_id)

    # translate the address
    device_addr = Address(args.device_addr)

    # kick off the process after the core is up and running
    deferred(this_application.read_object_list, device_id, device_addr)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
