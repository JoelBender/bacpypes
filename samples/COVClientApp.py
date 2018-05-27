#!/usr/bin/env python

"""
Configured with a subscription context object which is passed to the
application, it sends a SubscribeCOVRequest and listens for confirmed or
unconfirmed COV notifications, lines them up with the context, and passes the
APDU to the context to print out.

Making multiple subscription contexts and keeping them active based on their
lifetime is left as an exercise for the reader.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.apdu import SubscribeCOVRequest, SimpleAckPDU
from bacpypes.errors import ExecutionError

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

subscription_contexts = {}
next_proc_id = 1

#
#   SubscriptionContext
#

@bacpypes_debugging
class SubscriptionContext:

    def __init__(self, address, objid, confirmed=None, lifetime=None):
        if _debug: SubscriptionContext._debug("__init__ %r %r confirmed=%r lifetime=%r", address, objid, confirmed, lifetime)
        global subscription_contexts, next_proc_id

        # destination for subscription requests
        self.address = address

        # assign a unique process identifer and keep track of it
        self.subscriberProcessIdentifier = next_proc_id
        next_proc_id += 1
        subscription_contexts[self.subscriberProcessIdentifier] = self

        self.monitoredObjectIdentifier = objid
        self.issueConfirmedNotifications = confirmed
        self.lifetime = lifetime

    def cov_notification(self, apdu):
        if _debug: SubscriptionContext._debug("cov_notification %r", apdu)

        # make a rash assumption that the property value is going to be
        # a single application encoded tag
        print("{} {} changed\n    {}".format(
            apdu.pduSource,
            apdu.monitoredObjectIdentifier,
            ",\n    ".join("{} = {}".format(
                element.propertyIdentifier,
                str(element.value.tagList[0].app_to_object().value),
                ) for element in apdu.listOfValues),
            ))

#
#   SubscribeCOVApplication
#

@bacpypes_debugging
class SubscribeCOVApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: SubscribeCOVApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

    def send_subscription(self, context):
        if _debug: SubscribeCOVApplication._debug("send_subscription %r", context)

        # build a request
        request = SubscribeCOVRequest(
            subscriberProcessIdentifier=context.subscriberProcessIdentifier,
            monitoredObjectIdentifier=context.monitoredObjectIdentifier,
            )
        request.pduDestination = context.address

        # optional parameters
        if context.issueConfirmedNotifications is not None:
            request.issueConfirmedNotifications = context.issueConfirmedNotifications
        if context.lifetime is not None:
            request.lifetime = context.lifetime

        # make an IOCB
        iocb = IOCB(request)
        if _debug: SubscribeCOVApplication._debug("    - iocb: %r", iocb)

        # callback when it is acknowledged
        iocb.add_callback(self.subscription_acknowledged)

        # give it to the application
        this_application.request_io(iocb)

    def subscription_acknowledged(self, iocb):
        if _debug: SubscribeCOVApplication._debug("subscription_acknowledged %r", iocb)

        # do something for success
        if iocb.ioResponse:
            if _debug: SubscribeCOVApplication._debug("    - response: %r", iocb.ioResponse)

        # do something for error/reject/abort
        if iocb.ioError:
            if _debug: SubscribeCOVApplication._debug("    - error: %r", iocb.ioError)

    def do_ConfirmedCOVNotificationRequest(self, apdu):
        if _debug: SubscribeCOVApplication._debug("do_ConfirmedCOVNotificationRequest %r", apdu)

        # look up the process identifier
        context = subscription_contexts.get(apdu.subscriberProcessIdentifier, None)
        if not context or apdu.pduSource != context.address:
            if _debug: SubscribeCOVApplication._debug("    - no context")

            # this is turned into an ErrorPDU and sent back to the client
            raise ExecutionError('services', 'unknownSubscription')

        # now tell the context object
        context.cov_notification(apdu)

        # success
        response = SimpleAckPDU(context=apdu)
        if _debug: SubscribeCOVApplication._debug("    - simple_ack: %r", response)

        # return the result
        self.response(response)

    def do_UnconfirmedCOVNotificationRequest(self, apdu):
        if _debug: SubscribeCOVApplication._debug("do_UnconfirmedCOVNotificationRequest %r", apdu)

        # look up the process identifier
        context = subscription_contexts.get(apdu.subscriberProcessIdentifier, None)
        if not context or apdu.pduSource != context.address:
            if _debug: SubscribeCOVApplication._debug("    - no context")
            return

        # now tell the context object
        context.cov_notification(apdu)

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
    this_application = SubscribeCOVApplication(this_device, args.ini.address)

    # make a subscription context
    context = SubscriptionContext(Address("10.0.1.31"), ('analogValue', 1), False, 60)

    # send the subscription when the stack is ready
    deferred(this_application.send_subscription, context)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
