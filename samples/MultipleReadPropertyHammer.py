#!/usr/bin/env python

"""
Mutliple Read Property Hammer

This application blasts a list of ReadPropertyRequest messages with no
regard to the number of simultaneous requests to the same device.  The
ReadPointListApplication is constructed like the BIPSimpleApplication but
without the ApplicationIOController interface and sieve.
"""

import os
from time import time as _time
from copy import copy as _copy

from random import shuffle

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.comm import bind
from bacpypes.task import RecurringTask

from bacpypes.pdu import Address

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPSimple, AnnexJCodec, UDPMultiplexer

from bacpypes.apdu import ReadPropertyRequest

from bacpypes.local.device import LocalDeviceObject
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None
this_application = None

# settings
INTERVAL = float(os.getenv('INTERVAL', 10.0))

# point list, set according to your device
point_list = [
    ('10.0.1.21:47809', 'analogValue', 1, 'presentValue'),
    ('10.0.1.21:47809', 'analogValue', 2, 'presentValue'),
    ('10.0.1.21:47809', 'analogValue', 3, 'presentValue'),
    ('10.0.1.21:47809', 'analogValue', 4, 'presentValue'),
    ('10.0.1.21:47809', 'analogValue', 5, 'presentValue'),
    ]

#
#   ReadPointListApplication
#

@bacpypes_debugging
class ReadPointListApplication(Application, WhoIsIAmServices, ReadWritePropertyServices, RecurringTask):

    def __init__(self, localDevice, localAddress, deviceInfoCache=None, aseID=None):
        if _debug: ReadPointListApplication._debug("__init__ %r %r deviceInfoCache=%r aseID=%r", localDevice, localAddress, deviceInfoCache, aseID)
        global args

        Application.__init__(self, localDevice, deviceInfoCache, aseID=aseID)
        RecurringTask.__init__(self, args.interval * 1000)

        # local address might be useful for subclasses
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the BIP stack to the network, no network number
        self.nsap.bind(self.bip)

        # install the task
        self.install_task()

        # timer
        self.start_time = None

        # pending requests
        self.pending_requests = {}

    def process_task(self):
        if _debug: ReadPointListApplication._debug("process_task")
        global point_list

        # we might not have finished from the last round
        if self.pending_requests:
            if _debug: ReadPointListApplication._debug("    - %d pending", len(self.pending_requests))
            return

        # start the clock
        self.start_time = _time()

        # make a copy of the point list and shuffle it
        point_list_copy = _copy(point_list)
        shuffle(point_list_copy)

        # loop through the points
        for addr, obj_type, obj_inst, prop_id in point_list_copy:
            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)
            if _debug: ReadPointListApplication._debug("    - request: %r", request)

            # send the request
            self.request(request)

            # get the destination address from the pdu
            request_key = request.pduDestination, request.apduInvokeID
            if _debug: ReadPointListApplication._debug("    - request_key: %r", request_key)

            # make sure it's unused
            if request_key in self.pending_requests:
                raise RuntimeError("request key already used: %r" % (request_key,))
                
            # add this to pending requests
            self.pending_requests[request_key] = request

    def confirmation(self, apdu):
        if _debug: ReadPointListApplication._debug("confirmation %r", apdu)

        # get the source address from the pdu
        request_key = apdu.pduSource, apdu.apduInvokeID
        if _debug: ReadPointListApplication._debug("    - request_key: %r", request_key)

        # make sure it's unused
        if request_key not in self.pending_requests:
            raise RuntimeError("request missing: %r" % (request_key,))

        # this is no longer pending
        del self.pending_requests[request_key]

        # we could be done with this interval
        if not self.pending_requests:
            elapsed_time = _time() - self.start_time
            if _debug: ReadPointListApplication._debug("    - completed interval, %r seconds", elapsed_time)


#
#   __main__
#

def main():
    global args, this_application

    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an option to override the interval time
    parser.add_argument('--interval', type=float,
        help="amount of time between intervals",
        default=INTERVAL,
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = ReadPointListApplication(this_device, args.ini.address)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
