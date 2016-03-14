#!/usr/bin/python

"""
Mutliple Read Property

This application has a static list of points that it would like to read.  It reads the 
values of each of them in turn and then quits.
"""

from collections import deque

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, stop, deferred

from bacpypes.pdu import Address
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import get_datatype

from bacpypes.apdu import ReadPropertyRequest, Error, AbortPDU, ReadPropertyACK
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.basetypes import ServicesSupported

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None
this_console = None

# point list
# set according to your device
point_list = [
    ('1.2.3.4', 'analogValue', 1, 'presentValue'),
    ('1.2.3.4', 'analogValue', 2, 'presentValue'),
    ]

#
#   ReadPointListApplication
#

@bacpypes_debugging
class ReadPointListApplication(BIPSimpleApplication):

    def __init__(self, point_list, *args):
        if _debug: ReadPointListApplication._debug("__init__ %r, %r", point_list, args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None

        # make a list of the response values
        self.response_values = []

        # turn the point list into a queue
        self.point_queue = deque(point_list)

    def next_request(self):
        if _debug: ReadPointListApplication._debug("next_request")

        # check to see if we're done
        if not self.point_queue:
            if _debug: ReadPointListApplication._debug("    - done")
            stop()
            return

        # get the next request
        addr, obj_type, obj_inst, prop_id = self.point_queue.popleft()

        # build a request
        self._request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id,
            )
        self._request.pduDestination = Address(addr)
        if _debug: ReadPointListApplication._debug("    - request: %r", self._request)

        # forward it along
        BIPSimpleApplication.request(self, self._request)

    def confirmation(self, apdu):
        if _debug: ReadPointListApplication._debug("confirmation %r", apdu)

        if isinstance(apdu, Error):
            if _debug: ReadPointListApplication._debug("    - error: %r", apdu)
            self.response_values.append(apdu)

        elif isinstance(apdu, AbortPDU):
            if _debug: ReadPointListApplication._debug("    - abort: %r", apdu)
            self.response_values.append(apdu)

        elif (isinstance(self._request, ReadPropertyRequest)) and (isinstance(apdu, ReadPropertyACK)):
            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug: ReadPointListApplication._debug("    - datatype: %r", datatype)
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
            if _debug: ReadPointListApplication._debug("    - value: %r", value)

            # save the value
            self.response_values.append(value)

        # fire off another request
        deferred(self.next_request)

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
    this_application = ReadPointListApplication(point_list, this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # fire off a request when the core has a chance
    deferred(this_application.next_request)

    _log.debug("running")

    run()

    # dump out the results
    for request, response in zip(point_list, this_application.response_values):
        print(request, response)

except Exception as error:
    _log.exception("an error has occurred: %s", error)
finally:
    _log.debug("finally")
