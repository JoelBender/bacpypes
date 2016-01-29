#!/usr/bin/python

"""
This sample application shows how to extend the basic functionality of a device 
to support the ReadPropertyMultiple service.
"""

from collections import defaultdict

from bacpypes.debugging import bacpypes_debugging, DebugContents, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run
from bacpypes.task import OneShotTask, TaskManager
from bacpypes.pdu import Address

from bacpypes.primitivedata import Real
from bacpypes.constructeddata import Any
from bacpypes.basetypes import BinaryPV, StatusFlags, PropertyValue
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import AnalogValueObject, BinaryValueObject, \
    WritableProperty, get_object_class, register_object_type
from bacpypes.apdu import SubscribeCOVRequest, \
    ConfirmedCOVNotificationRequest, \
    UnconfirmedCOVNotificationRequest, \
    SimpleAckPDU, Error, RejectPDU, AbortPDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
_generic_criteria_classes = {}
_cov_increment_criteria_classes = {}

# test globals
test_application = None
test_avo = None

#
#   COVSubscriptionList
#

class COVSubscriptionList:

    def __init__(self):
        if _debug: COVSubscriptionList._debug("__init__")

        self.cov_subscriptions = []

    def append(self, cov):
        if _debug: COVSubscriptionList._debug("append %r", cov)

        self.cov_subscriptions.append(cov)

    def remove(self, cov):
        if _debug: COVSubscriptionList._debug("remove %r", cov)

        self.cov_subscriptions.remove(cov)

    def find(self, client_addr, proc_id, obj_id):
        if _debug: COVSubscriptionList._debug("find %r %r %r", client_addr, proc_id, obj_id)

        for cov in self.cov_subscriptions:
            all_equal = (cov.client_addr == client_addr) and \
                (cov.proc_id == proc_id) and \
                (cov.obj_id == obj_id)
            if _debug: COVSubscriptionList._debug("    - cov, all_equal: %r %r", cov, all_equal)

            if all_equal:
                return cov

        return None

    def __len__(self):
        if _debug: COVSubscriptionList._debug("__len__")

        return len(self.cov_subscriptions)

    def __iter__(self):
        if _debug: COVSubscriptionList._debug("__iter__")

        for cov in self.cov_subscriptions:
            yield cov

bacpypes_debugging(COVSubscriptionList)

#
#   COVSubscription
#

class COVSubscription(OneShotTask, DebugContents):

    _debug_contents = (
        'obj_ref',
        'client_addr',
        'proc_id',
        'obj_id',
        'confirmed',
        'lifetime',
        )

    def __init__(self, obj_ref, client_addr, proc_id, obj_id, confirmed, lifetime):
        if _debug: COVSubscription._debug("__init__ %r %r %r %r %r %r", obj_ref, client_addr, proc_id, obj_id, confirmed, lifetime)
        OneShotTask.__init__(self)

        # save the reference to the related object
        self.obj_ref = obj_ref

        # save the parameters
        self.client_addr = client_addr
        self.proc_id = proc_id
        self.obj_id = obj_id
        self.confirmed = confirmed
        self.lifetime = lifetime

        # add ourselves to the subscription list
        self.obj_ref._cov_subscriptions.append(self)

        # if lifetime is non-zero, schedule the subscription to expire
        if lifetime != 0:
            self.install_task(delta=self.lifetime)

    def cancel_subscription(self):
        if _debug: COVSubscription._debug("cancel_subscription")

        # suspend the task
        self.suspend_task()

        # remove ourselves from the other subscriptions for this object
        self.obj_ref._cov_subscriptions.remove(self)

        # break the object reference
        self.obj_ref = None

    def renew_subscription(self, lifetime):
        if _debug: COVSubscription._debug("renew_subscription")

        # suspend iff scheduled
        if self.isScheduled:
            self.suspend_task()

        # reschedule the task if its not infinite
        if lifetime != 0:
            self.install_task(delta=lifetime)

    def process_task(self):
        if _debug: COVSubscription._debug("process_task")

        # subscription is canceled
        self.cancel_subscription()

bacpypes_debugging(COVSubscription)

#
#   COVCriteria
#

class COVCriteria:

    _properties_tracked = ()
    _properties_reported = ()

    def _check_criteria(self):
        if _debug: COVCriteria._debug("_check_criteria")

        # assume nothing has changed
        something_changed = False

        # check all the things
        for property_name in self._properties_tracked:
            property_changed = (self._values[property_name] != self._cov_properties[property_name])
            if property_changed:
                if _debug: COVCriteria._debug("    - %s changed", property_name)

                # copy the new value for next time
                self._cov_properties[property_name] = self._values[property_name]

                something_changed = True

        if not something_changed:
            if _debug: COVCriteria._debug("    - nothing changed")

        # should send notifications
        return something_changed


def GenericCriteria(cls):
    
    if cls in _generic_criteria_classes:
        return _generic_criteria_classes[cls]

    class _GenericCriteria(COVCriteria):

        _properties_tracked = ('presentValue', 'statusFlags')
        _properties_reported = ('presentValue', 'statusFlags')

        properties = \
            [ WritableProperty('presentValue', cls)
            , WritableProperty('statusFlags', StatusFlags)
            ]

    _GenericCriteria.__name__ = 'GenericCriteria(' + cls.__name__ + ')'

    _generic_criteria_classes[cls] = _GenericCriteria
    return _GenericCriteria


@bacpypes_debugging
def COVIncrementCriteria(cls):
    
    if cls in _cov_increment_criteria_classes:
        return _cov_increment_criteria_classes[cls]

    class _COVIncrementCriteria(COVCriteria):

        _properties_tracked = ('presentValue', 'statusFlags')
        _properties_reported = ('presentValue', 'statusFlags')

        properties = \
            [ WritableProperty('presentValue', cls)
            , WritableProperty('statusFlags', StatusFlags)
            ]

        def _check_criteria(self):
            if _debug: COVIncrementCriteria._debug("_check_criteria")

            # assume nothing has changed
            something_changed = False

            # get the old and new values
            old_present_value = self._cov_properties['presentValue']
            new_present_value = self._values['presentValue']
            cov_increment = self._values['covIncrement']

            # check the difference in values
            value_changed = (new_present_value <= (old_present_value - cov_increment)) \
                or (new_present_value >= (old_present_value + cov_increment))
            if value_changed:
                if _debug: COVCriteria._debug("    - present value changed")

                # copy the new value for next time
                self._cov_properties['presentValue'] = new_present_value

                something_changed = True

            # check the status flags
            status_changed = (self._values['statusFlags'] != self._cov_properties['statusFlags'])
            if status_changed:
                if _debug: COVIncrementCriteria._debug("    - status flags changed")

                # copy the new value for next time
                self._cov_properties['statusFlags'] = self._values['statusFlags']

                something_changed = True

            if not something_changed:
                if _debug: COVIncrementCriteria._debug("    - nothing changed")

            # should send notifications
            return something_changed

    _COVIncrementCriteria.__name__ = 'COVIncrementCriteria(' + cls.__name__ + ')'

    _cov_increment_criteria_classes[cls] = _COVIncrementCriteria
    return _COVIncrementCriteria

#
#   Change of Value Mixin
#

@bacpypes_debugging
class COVObjectMixin(object):

    _debug_contents = (
        '_cov_subscriptions',
        '_cov_properties',
        )

    def __init__(self, **kwargs):
        if _debug: COVObjectMixin._debug("__init__ %r", kwargs)
        super(COVObjectMixin, self).__init__(**kwargs)

        # list of all active subscriptions
        self._cov_subscriptions = COVSubscriptionList()

        # snapshot the properties tracked
        self._cov_properties = {}
        for property_name in self._properties_tracked:
            self._cov_properties[property_name] = self._values[property_name]

    def WriteProperty(self, propid, value, arrayIndex=None, priority=None, direct=False):
        if _debug: COVObjectMixin._debug("WriteProperty %r %r arrayIndex=%r priority=%r", propid, value, arrayIndex, priority)

        # use the default implementation
        super(COVObjectMixin, self).WriteProperty(propid, value, arrayIndex, priority, direct)

        # check for special properties
        if propid in self._properties_tracked:
            if _debug: COVObjectMixin._debug("    - property tracked")

            # check if it is significant
            if self._check_criteria():
                if _debug: COVObjectMixin._debug("    - send notifications")
                self._send_cov_notifications()
            else:
                if _debug: COVObjectMixin._debug("    - no notifications necessary")
        else:
            if _debug: COVObjectMixin._debug("    - property not tracked")

    def _send_cov_notifications(self):
        if _debug: COVObjectMixin._debug("_send_cov_notifications")

        # check for subscriptions
        if not len(self._cov_subscriptions):
            return

        # get the current time from the task manager
        current_time = TaskManager().get_time()
        if _debug: COVObjectMixin._debug("    - current_time: %r", current_time)

        # create a list of values
        list_of_values = []
        for property_name in self._properties_reported:
            if _debug: COVObjectMixin._debug("    - property_name: %r", property_name)

            # get the class
            property_datatype = self.get_datatype(property_name)
            if _debug: COVObjectMixin._debug("        - property_datatype: %r", property_datatype)

            # build the value
            bundle_value = property_datatype(self._values[property_name])
            if _debug: COVObjectMixin._debug("        - bundle_value: %r", bundle_value)

            # bundle it into a sequence
            property_value = PropertyValue(
                propertyIdentifier=property_name,
                value=Any(bundle_value),
                )

            # add it to the list
            list_of_values.append(property_value)
        if _debug: COVObjectMixin._debug("    - list_of_values: %r", list_of_values)

        # loop through the subscriptions and send out notifications
        for cov in self._cov_subscriptions:
            if _debug: COVObjectMixin._debug("    - cov: %r", cov)

            # calculate time remaining
            if not cov.lifetime:
                time_remaining = 0
            else:
                time_remaining = int(cov.taskTime - current_time)

                # make sure it is at least one second
                if not time_remaining:
                    time_remaining = 1

            # build a request with the correct type
            if cov.confirmed:
                request = ConfirmedCOVNotificationRequest()
            else:
                request = UnconfirmedCOVNotificationRequest()

            # fill in the parameters
            request.pduDestination = cov.client_addr
            request.subscriberProcessIdentifier = cov.proc_id
            request.initiatingDeviceIdentifier = self._app.localDevice.objectIdentifier
            request.monitoredObjectIdentifier = cov.obj_id
            request.timeRemaining = time_remaining
            request.listOfValues = list_of_values
            if _debug: COVObjectMixin._debug("    - request: %r", request)

            # let the application send it
            self._app.cov_notification(cov, request)


@register_object_type
class BinaryValueObjectCOV(COVObjectMixin, GenericCriteria(BinaryPV), BinaryValueObject):
    pass

@register_object_type
class AnalogValueObjectCOV(COVObjectMixin, COVIncrementCriteria(Real), AnalogValueObject):
    pass

#
#   COVApplicationMixin
#

@bacpypes_debugging
class COVApplicationMixin(object):

    def __init__(self, *args, **kwargs):
        if _debug: COVApplicationMixin._debug("__init__ %r %r", args, kwargs)
        super(COVApplicationMixin, self).__init__(*args, **kwargs)

        # a queue of confirmed notifications by client address
        self.confirmed_notifications_queue = defaultdict(list)

    def cov_notification(self, cov, request):
        if _debug: COVApplicationMixin._debug("cov_notification %s %s", str(cov), str(request))

        # if this is confirmed, keep track of the cov
        if cov.confirmed:
            if _debug: COVApplicationMixin._debug("    - it's confirmed")

            notification_list = self.confirmed_notifications_queue[cov.client_addr]
            notification_list.append((request, cov))

            # if this isn't the first, wait until the first one is done
            if len(notification_list) > 1:
                if _debug: COVApplicationMixin._debug("    - not the first")
                return
        else:
            if _debug: COVApplicationMixin._debug("    - it's unconfirmed")

        # send it along down the stack
        super(COVApplicationMixin, self).request(request)
        if _debug: COVApplicationMixin._debug("    - apduInvokeID: %r", getattr(request, 'apduInvokeID'))

    def cov_error(self, cov, request, response):
        if _debug: COVApplicationMixin._debug("cov_error %r %r %r", cov, request, response)

    def cov_reject(self, cov, request, response):
        if _debug: COVApplicationMixin._debug("cov_reject %r %r %r", cov, request, response)

    def cov_abort(self, cov, request, response):
        if _debug: COVApplicationMixin._debug("cov_abort %r %r %r", cov, request, response)

        # delete the rest of the pending requests for this client
        del self.confirmed_notifications_queue[cov.client_addr][:]
        if _debug: COVApplicationMixin._debug("    - other notifications deleted")

    def confirmation(self, apdu):
        if _debug: COVApplicationMixin._debug("confirmation %r", apdu)

        if _debug: COVApplicationMixin._debug("    - queue keys: %r", self.confirmed_notifications_queue.keys())

        # if this isn't from someone we care about, toss it
        if apdu.pduSource not in self.confirmed_notifications_queue:
            if _debug: COVApplicationMixin._debug("    - not someone we are tracking")

            # pass along to the application
            super(COVApplicationMixin, self).confirmation(apdu)
            return

        # refer to the notification list for this client
        notification_list = self.confirmed_notifications_queue[apdu.pduSource]
        if _debug: COVApplicationMixin._debug("    - notification_list: %r", notification_list)

        # peek at the front of the list
        request, cov = notification_list[0]
        if _debug: COVApplicationMixin._debug("    - request: %s", request)

        # line up the invoke id
        if apdu.apduInvokeID == request.apduInvokeID:
            if _debug: COVApplicationMixin._debug("    - request/response align")
            notification_list.pop(0)
        else:
            if _debug: COVApplicationMixin._debug("    - request/response do not align")

            # pass along to the application
            super(COVApplicationMixin, self).confirmation(apdu)
            return

        if isinstance(apdu, Error):
            if _debug: COVApplicationMixin._debug("    - error: %r", apdu.errorCode)
            self.cov_error(cov, request, apdu)

        elif isinstance(apdu, RejectPDU):
            if _debug: COVApplicationMixin._debug("    - reject: %r", apdu.apduAbortRejectReason)
            self.cov_reject(cov, request, apdu)

        elif isinstance(apdu, AbortPDU):
            if _debug: COVApplicationMixin._debug("    - abort: %r", apdu.apduAbortRejectReason)
            self.cov_abort(cov, request, apdu)

        # if the notification list is empty, delete the reference
        if not notification_list:
            if _debug: COVApplicationMixin._debug("    - no other pending notifications")
            del self.confirmed_notifications_queue[apdu.pduSource]
            return

        # peek at the front of the list for the next request
        request, cov = notification_list[0]
        if _debug: COVApplicationMixin._debug("    - next notification: %r", request)

        # send it along down the stack
        super(COVApplicationMixin, self).request(request)

    def do_SubscribeCOVRequest(self, apdu):
        if _debug: COVApplicationMixin._debug("do_SubscribeCOVRequest %r", apdu)
        global test_avo

        # extract the pieces
        client_addr = apdu.pduSource
        proc_id = apdu.subscriberProcessIdentifier
        obj_id = apdu.monitoredObjectIdentifier
        confirmed = apdu.issueConfirmedNotifications
        lifetime = apdu.lifetime

        # request is to cancel the subscription
        cancel_subscription = (confirmed is None) and (lifetime is None)

        # can a match be found?
        cov = test_avo._cov_subscriptions.find(client_addr, proc_id, obj_id)
        if _debug: COVConsoleCmd._debug("    - cov: %r", cov)

        # if a match was found, update the subscription
        if cov:
            if cancel_subscription:
                if _debug: COVConsoleCmd._debug("    - cancel the subscription")
                cov.cancel_subscription()
            else:
                if _debug: COVConsoleCmd._debug("    - renew the subscription")
                cov.renew_subscription(lifetime)
        else:
            if cancel_subscription:
                if _debug: COVConsoleCmd._debug("    - cancel a subscription that doesn't exist")
            else:
                if _debug: COVConsoleCmd._debug("    - create a subscription")

                cov = COVSubscription(test_avo, client_addr, proc_id, obj_id, confirmed, lifetime)
                if _debug: COVConsoleCmd._debug("    - cov: %r", cov)

        # success
        response = SimpleAckPDU(context=apdu)

        # return the result
        self.response(response)

#
#   SubscribeCOVApplication
#

@bacpypes_debugging
class SubscribeCOVApplication(COVApplicationMixin, BIPSimpleApplication):
    pass

#
#   COVConsoleCmd
#

class COVConsoleCmd(ConsoleCmd):

    def do_subscribe(self, args):
        """subscribe addr proc_id obj_type obj_inst [ confirmed ] [ lifetime ]
        """
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_subscribe %r", args)
        global test_application, test_avo

        try:
            addr, proc_id, obj_type, obj_inst = args[:4]

            client_addr = Address(addr)
            if _debug: COVConsoleCmd._debug("    - client_addr: %r", client_addr)

            proc_id = int(proc_id)
            if _debug: COVConsoleCmd._debug("    - proc_id: %r", proc_id)

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif not get_object_class(obj_type):
                raise ValueError("unknown object type")
            obj_inst = int(obj_inst)
            obj_id = (obj_type, obj_inst)
            if _debug: COVConsoleCmd._debug("    - obj_id: %r", obj_id)

            if len(args) >= 5:
                issue_confirmed = args[4]
                if issue_confirmed == '-':
                    issue_confirmed = None
                else:
                    issue_confirmed = issue_confirmed.lower() == 'true'
                if _debug: COVConsoleCmd._debug("    - issue_confirmed: %r", issue_confirmed)
            else:
                issue_confirmed = None

            if len(args) >= 6:
                lifetime = args[5]
                if lifetime == '-':
                    lifetime = None
                else:
                    lifetime = int(lifetime)
                if _debug: COVConsoleCmd._debug("    - lifetime: %r", lifetime)
            else:
                lifetime = None

            # can a match be found?
            cov = test_avo._cov_subscriptions.find(client_addr, proc_id, obj_id)
            if _debug: COVConsoleCmd._debug("    - cov: %r", cov)

            # build a request
            request = SubscribeCOVRequest(
                subscriberProcessIdentifier=proc_id,
                monitoredObjectIdentifier=(obj_type, obj_inst),
                )

            # spoof that it came from the client
            request.pduSource = client_addr

            # optional parameters
            if issue_confirmed is not None:
                request.issueConfirmedNotifications = issue_confirmed
            if lifetime is not None:
                request.lifetime = lifetime

            if _debug: COVConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            test_application.do_SubscribeCOVRequest(request)

        except Exception as err:
            COVConsoleCmd._exception("exception: %r", err)

    def do_status(self, args):
        """status"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_status %r", args)
        global test_avo

        print("test_avo")
        test_avo.debug_contents()

    def do_trigger(self, args):
        """trigger"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_trigger %r", args)
        global test_avo

        # tell the object to send out notifications
        test_avo._send_cov_notifications()

    def do_set(self, args):
        """set value"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_set %r", args)
        global test_avo

        # use 'direct' access to the property
        test_avo.presentValue = float(args[0])

    def do_write(self, args):
        """write value"""
        args = args.split()
        if _debug: COVConsoleCmd._debug("do_set %r", args)
        global test_avo

        # use the service to change the value
        test_avo.WriteProperty('presentValue', float(args[0]))

bacpypes_debugging(COVConsoleCmd)


def main():
    global test_application, test_avo

    # make a parser
    parser = ConfigArgumentParser(description=__doc__)
    parser.add_argument("--console",
        action="store_true",
        default=False,
        help="create a console",
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    test_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    test_application = SubscribeCOVApplication(test_device, args.ini.address)

    # make an analog value object
    test_avo = AnalogValueObjectCOV(
        objectIdentifier=('analogValue', 1),
        objectName='Random1',
        presentValue=0.0,
        statusFlags=[0, 0, 0, 0],
        covIncrement=1.0,
        )
    _log.debug("    - test_avo: %r", test_avo)

    # add it to the device
    test_application.add_object(test_avo)
    _log.debug("    - object list: %r", test_device.objectList)

    # get the services supported
    services_supported = test_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    test_device.protocolServicesSupported = services_supported.value

    # make a console
    if args.console:
        test_console = COVConsoleCmd()
        _log.debug("    - test_console: %r", test_console)

    _log.debug("running")

    run()


if __name__ == "__main__":
    main()