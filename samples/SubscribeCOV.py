#!/usr/bin/python

"""
This application presents a 'console' prompt to the user asking for read commands
which create ReadPropertyRequest PDUs, then lines up the coorresponding ReadPropertyACK
and prints the value.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run

from bacpypes.pdu import Address
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype

from bacpypes.apdu import SubscribeCOVRequest, SimpleAckPDU, \
    Error, RejectPDU, AbortPDU
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

# how the application should respond
rsvp = (True, None, None)

#
#   SubscribeCOVApplication
#

class SubscribeCOVApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: SubscribeCOVApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None

    def request(self, apdu):
        if _debug: SubscribeCOVApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu

        # forward it along
        BIPSimpleApplication.request(self, apdu)

    def confirmation(self, apdu):
        if _debug: SubscribeCOVApplication._debug("confirmation %r", apdu)

        # continue normally
        super(SubscribeCOVApplication, self).confirmation(apdu)

    def indication(self, apdu):
        if _debug: SubscribeCOVApplication._debug("indication %r", apdu)

        # continue normally
        super(SubscribeCOVApplication, self).indication(apdu)

    def do_ConfirmedCOVNotificationRequest(self, apdu):
        if _debug: SubscribeCOVApplication._debug("do_ConfirmedCOVNotificationRequest %r", apdu)
        global rsvp

        if rsvp[0]:
            # success
            response = SimpleAckPDU(context=apdu)
            if _debug: SubscribeCOVApplication._debug("    - simple_ack: %r", response)

        elif rsvp[1]:
            # reject
            response = RejectPDU(reason=rsvp[1], context=apdu)
            if _debug: SubscribeCOVApplication._debug("    - reject: %r", response)

        elif rsvp[2]:
            # abort
            response = AbortPDU(reason=rsvp[2], context=apdu)
            if _debug: SubscribeCOVApplication._debug("    - abort: %r", response)

        # return the result
        self.response(response)

    def do_UnconfirmedCOVNotificationRequest(self, apdu):
        if _debug: SubscribeCOVApplication._debug("do_UnconfirmedCOVNotificationRequest %r", apdu)

bacpypes_debugging(SubscribeCOVApplication)

#
#   SubscribeCOVConsoleCmd
#

class SubscribeCOVConsoleCmd(ConsoleCmd):

    def do_subscribe(self, args):
        """subscribe addr proc_id obj_type obj_inst [ confirmed ] [ lifetime ]
        """
        args = args.split()
        if _debug: SubscribeCOVConsoleCmd._debug("do_subscribe %r", args)

        try:
            addr, proc_id, obj_type, obj_inst = args[:4]

            proc_id = int(proc_id)

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif not get_object_class(obj_type):
                raise ValueError, "unknown object type"
            obj_inst = int(obj_inst)

            if len(args) >= 5:
                issue_confirmed = args[4]
                if issue_confirmed == '-':
                    issue_confirmed = None
                else:
                    issue_confirmed = issue_confirmed.lower() == 'true'
                if _debug: SubscribeCOVConsoleCmd._debug("    - issue_confirmed: %r", issue_confirmed)
            else:
                issue_confirmed = None

            if len(args) >= 6:
                lifetime = args[5]
                if lifetime == '-':
                    lifetime = None
                else:
                    lifetime = int(lifetime)
                if _debug: SubscribeCOVConsoleCmd._debug("    - lifetime: %r", lifetime)
            else:
                lifetime = None

            # build a request
            request = SubscribeCOVRequest(
                subscriberProcessIdentifier=proc_id,
                monitoredObjectIdentifier=(obj_type, obj_inst),
                )
            request.pduDestination = Address(addr)

            # optional parameters
            if issue_confirmed is not None:
                request.issueConfirmedNotifications = issue_confirmed
            if lifetime is not None:
                request.lifetime = lifetime

            if _debug: SubscribeCOVConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            this_application.request(request)

        except Exception, e:
            SubscribeCOVConsoleCmd._exception("exception: %r", e)

    def do_ack(self, args):
        """ack
        """
        args = args.split()
        if _debug: SubscribeCOVConsoleCmd._debug("do_ack %r", args)
        global rsvp

        rsvp = (True, None, None)

    def do_reject(self, args):
        """reject reason
        """
        args = args.split()
        if _debug: SubscribeCOVConsoleCmd._debug("do_subscribe %r", args)
        global rsvp

        rsvp = (False, args[0], None)

    def do_abort(self, args):
        """abort reason
        """
        args = args.split()
        if _debug: SubscribeCOVConsoleCmd._debug("do_subscribe %r", args)
        global rsvp

        rsvp = (False, None, args[0])

bacpypes_debugging(SubscribeCOVConsoleCmd)

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
    this_application = SubscribeCOVApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = SubscribeCOVConsoleCmd()

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")
