#!/usr/bin/python

"""
Mutliple Read Property

This application has a static list of points that it would like to read.  It reads the 
values of each of them in turn and then quits.
"""

from collections import deque

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred
from bacpypes.task import RecurringTask

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
point_list = [
    ('1.2.3.4', 'analogValue', 1, 'presentValue'),
    ('1.2.3.4', 'analogValue', 2, 'presentValue'),
    ]

#
#   PrairieDog
#

@bacpypes_debugging
class PrairieDog(BIPSimpleApplication, RecurringTask):

    def __init__(self, interval, *args):
        if _debug: PrairieDog._debug("__init__ %r, %r", interval, args)
        BIPSimpleApplication.__init__(self, *args)
        RecurringTask.__init__(self, interval * 1000)

        # keep track of requests to line up responses
        self._request = None

        # start out idle
        self.is_busy = False
        self.point_queue = deque()
        self.response_values = []

        # install it
        self.install_task()

    def process_task(self):
        if _debug: PrairieDog._debug("process_task")
        global point_list

        # check to see if we're idle
        if self.is_busy:
            if _debug: PrairieDog._debug("    - busy")
            return

        # now we are busy
        self.is_busy = True

        # turn the point list into a queue
        self.point_queue = deque(point_list)

        # clean out the list of the response values
        self.response_values = []

        # fire off the next request
        self.next_request()

    def next_request(self):
        if _debug: PrairieDog._debug("next_request")

        # check to see if we're done
        if not self.point_queue:
            if _debug: PrairieDog._debug("    - done")

            # dump out the results
            for request, response in zip(point_list, self.response_values):
                print request, response

            # no longer busy
            self.is_busy = False

            return

        # get the next request
        addr, obj_type, obj_inst, prop_id = self.point_queue.popleft()

        # build a request
        self._request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id,
            )
        self._request.pduDestination = Address(addr)
        if _debug: PrairieDog._debug("    - request: %r", self._request)

        # forward it along
        BIPSimpleApplication.request(self, self._request)

    def confirmation(self, apdu):
        if _debug: PrairieDog._debug("confirmation %r", apdu)

        if isinstance(apdu, Error):
            if _debug: PrairieDog._debug("    - error: %r", apdu)
            self.response_values.append(apdu)

        elif isinstance(apdu, AbortPDU):
            if _debug: PrairieDog._debug("    - abort: %r", apdu)
            self.response_values.append(apdu)

        elif (isinstance(self._request, ReadPropertyRequest)) and (isinstance(apdu, ReadPropertyACK)):
            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug: PrairieDog._debug("    - datatype: %r", datatype)
            if not datatype:
                raise TypeError, "unknown datatype"

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
            if _debug: PrairieDog._debug("    - value: %r", value)

            # save the value
            self.response_values.append(value)

        # fire off another request
        deferred(self.next_request)

#
#   __main__
#

try:
    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an argument for interval
    parser.add_argument('interval', type=int,
          help='repeat rate in seconds',
          )

    # now parse the arguments
    args = parser.parse_args()

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

    # build a bit string that knows about the bit names
    pss = ServicesSupported()
    pss['whoIs'] = 1
    pss['iAm'] = 1
    pss['readProperty'] = 1
    pss['writeProperty'] = 1

    # set the property value to be just the bits
    this_device.protocolServicesSupported = pss.value

    # make a dog
    this_application = PrairieDog(args.interval, this_device, args.ini.address)

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")
