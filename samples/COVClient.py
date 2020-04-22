#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for
subscribe commands which create SubscribeCOVRequests.  The other commands are
for changing the type of reply to the confirmed COV notification that gets
sent.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.apdu import SubscribeCOVRequest, SimpleAckPDU, RejectPDU, AbortPDU
from bacpypes.primitivedata import ObjectIdentifier

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

# how the application should respond
rsvp = (True, None, None)

#
#   SubscribeCOVApplication
#


@bacpypes_debugging
class SubscribeCOVApplication(BIPSimpleApplication):
    def __init__(self, *args):
        if _debug:
            SubscribeCOVApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

    def do_ConfirmedCOVNotificationRequest(self, apdu):
        if _debug:
            SubscribeCOVApplication._debug(
                "do_ConfirmedCOVNotificationRequest %r", apdu
            )
        global rsvp

        print("{} changed\n".format(apdu.monitoredObjectIdentifier))
        for element in apdu.listOfValues:
            element_value = element.value.tagList
            if _debug:
                SubscribeCOVApplication._debug("    - propertyIdentifier: %r", element.propertyIdentifier)
                SubscribeCOVApplication._debug("    - value tag list: %r", element_value)

            if len(element_value) == 1:
                element_value = element_value[0].app_to_object().value

            print("    {} is {}".format(element.propertyIdentifier, str(element_value)))

        if rsvp[0]:
            # success
            response = SimpleAckPDU(context=apdu)
            if _debug:
                SubscribeCOVApplication._debug("    - simple_ack: %r", response)

        elif rsvp[1]:
            # reject
            response = RejectPDU(reason=rsvp[1], context=apdu)
            if _debug:
                SubscribeCOVApplication._debug("    - reject: %r", response)

        elif rsvp[2]:
            # abort
            response = AbortPDU(reason=rsvp[2], context=apdu)
            if _debug:
                SubscribeCOVApplication._debug("    - abort: %r", response)

        # return the result
        self.response(response)

    def do_UnconfirmedCOVNotificationRequest(self, apdu):
        if _debug:
            SubscribeCOVApplication._debug(
                "do_UnconfirmedCOVNotificationRequest %r", apdu
            )

        print("{} changed\n".format(apdu.monitoredObjectIdentifier))
        for element in apdu.listOfValues:
            element_value = element.value.tagList
            if len(element_value) == 1:
                element_value = element_value[0].app_to_object().value

            print("    {} is {}".format(element.propertyIdentifier, str(element_value)))


#
#   SubscribeCOVConsoleCmd
#


@bacpypes_debugging
class SubscribeCOVConsoleCmd(ConsoleCmd):
    def do_subscribe(self, args):
        """subscribe addr proc_id obj_id [ confirmed ] [ lifetime ]

        Generate a SubscribeCOVRequest and wait for the response.
        """
        args = args.split()
        if _debug:
            SubscribeCOVConsoleCmd._debug("do_subscribe %r", args)

        try:
            addr, proc_id, obj_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value

            proc_id = int(proc_id)

            if len(args) >= 4:
                issue_confirmed = args[3]
                if issue_confirmed == "-":
                    issue_confirmed = None
                else:
                    issue_confirmed = issue_confirmed.lower() == "true"
                if _debug:
                    SubscribeCOVConsoleCmd._debug(
                        "    - issue_confirmed: %r", issue_confirmed
                    )
            else:
                issue_confirmed = None

            if len(args) >= 5:
                lifetime = args[4]
                if lifetime == "-":
                    lifetime = None
                else:
                    lifetime = int(lifetime)
                if _debug:
                    SubscribeCOVConsoleCmd._debug("    - lifetime: %r", lifetime)
            else:
                lifetime = None

            # build a request
            request = SubscribeCOVRequest(
                subscriberProcessIdentifier=proc_id, monitoredObjectIdentifier=obj_id
            )
            request.pduDestination = Address(addr)

            # optional parameters
            if issue_confirmed is not None:
                request.issueConfirmedNotifications = issue_confirmed
            if lifetime is not None:
                request.lifetime = lifetime

            if _debug:
                SubscribeCOVConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                SubscribeCOVConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                if _debug:
                    SubscribeCOVConsoleCmd._debug("    - response: %r", iocb.ioResponse)

            # do something for error/reject/abort
            if iocb.ioError:
                if _debug:
                    SubscribeCOVConsoleCmd._debug("    - error: %r", iocb.ioError)

        except Exception as e:
            SubscribeCOVConsoleCmd._exception("exception: %r", e)

    def do_ack(self, args):
        """ack

        When confirmed COV notification requests arrive, respond with a
        simple acknowledgement.
        """
        args = args.split()
        if _debug:
            SubscribeCOVConsoleCmd._debug("do_ack %r", args)
        global rsvp

        rsvp = (True, None, None)

    def do_reject(self, args):
        """reject reason

        When confirmed COV notification requests arrive, respond with a
        reject PDU with the provided reason.
        """
        args = args.split()
        if _debug:
            SubscribeCOVConsoleCmd._debug("do_reject %r", args)
        global rsvp

        rsvp = (False, args[0], None)

    def do_abort(self, args):
        """abort reason

        When confirmed COV notification requests arrive, respond with an
        abort PDU with the provided reason.
        """
        args = args.split()
        if _debug:
            SubscribeCOVConsoleCmd._debug("do_abort %r", args)
        global rsvp

        rsvp = (False, None, args[0])


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
    this_application = SubscribeCOVApplication(this_device, args.ini.address)

    # make a console
    this_console = SubscribeCOVConsoleCmd()
    if _debug:
        _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
