#!/usr/bin/env python

"""
Change Of Value Service
"""

from ..debugging import bacpypes_debugging, DebugContents, ModuleLogger
from ..capability import Capability

from ..task import OneShotTask, TaskManager
from ..iocb import IOCB

from ..basetypes import DeviceAddress, COVSubscription, PropertyValue, \
    Recipient, RecipientProcess, ObjectPropertyReference
from ..constructeddata import SequenceOf, Any
from ..apdu import ConfirmedCOVNotificationRequest, \
    UnconfirmedCOVNotificationRequest, \
    SimpleAckPDU, Error, RejectPDU, AbortPDU
from ..errors import ExecutionError

from ..object import Property
from .detect import DetectionAlgorithm, monitor_filter

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   SubscriptionList
#

@bacpypes_debugging
class SubscriptionList:

    def __init__(self):
        if _debug: SubscriptionList._debug("__init__")

        self.cov_subscriptions = []

    def append(self, cov):
        if _debug: SubscriptionList._debug("append %r", cov)

        self.cov_subscriptions.append(cov)

    def remove(self, cov):
        if _debug: SubscriptionList._debug("remove %r", cov)

        self.cov_subscriptions.remove(cov)

    def find(self, client_addr, proc_id, obj_id):
        if _debug: SubscriptionList._debug("find %r %r %r", client_addr, proc_id, obj_id)

        for cov in self.cov_subscriptions:
            all_equal = (cov.client_addr == client_addr) and \
                (cov.proc_id == proc_id) and \
                (cov.obj_id == obj_id)
            if _debug: SubscriptionList._debug("    - cov, all_equal: %r %r", cov, all_equal)

            if all_equal:
                return cov

        return None

    def __len__(self):
        if _debug: SubscriptionList._debug("__len__")

        return len(self.cov_subscriptions)

    def __iter__(self):
        if _debug: SubscriptionList._debug("__iter__")

        for cov in self.cov_subscriptions:
            yield cov


#
#   Subscription
#

@bacpypes_debugging
class Subscription(OneShotTask, DebugContents):

    _debug_contents = (
        'obj_ref',
        'client_addr',
        'proc_id',
        'obj_id',
        'confirmed',
        'lifetime',
        )

    def __init__(self, obj_ref, client_addr, proc_id, obj_id, confirmed, lifetime):
        if _debug: Subscription._debug("__init__ %r %r %r %r %r %r", obj_ref, client_addr, proc_id, obj_id, confirmed, lifetime)
        OneShotTask.__init__(self)

        # save the reference to the related object
        self.obj_ref = obj_ref

        # save the parameters
        self.client_addr = client_addr
        self.proc_id = proc_id
        self.obj_id = obj_id
        self.confirmed = confirmed
        self.lifetime = lifetime

        # if lifetime is non-zero, schedule the subscription to expire
        if lifetime != 0:
            self.install_task(delta=self.lifetime)

    def cancel_subscription(self):
        if _debug: Subscription._debug("cancel_subscription")

        # suspend the task
        self.suspend_task()

        # tell the application to cancel us
        self.obj_ref._app.cancel_subscription(self)

        # break the object reference
        self.obj_ref = None

    def renew_subscription(self, lifetime):
        if _debug: Subscription._debug("renew_subscription")

        # suspend iff scheduled
        if self.isScheduled:
            self.suspend_task()

        # reschedule the task if its not infinite
        if lifetime != 0:
            self.install_task(delta=lifetime)

    def process_task(self):
        if _debug: Subscription._debug("process_task")

        # subscription is canceled
        self.cancel_subscription()

#
#   COVDetection
#

@bacpypes_debugging
class COVDetection(DetectionAlgorithm):

    properties_tracked = ()
    properties_reported = ()
    monitored_property_reference = None

    def __init__(self, obj):
        if _debug: COVDetection._debug("__init__ %r", obj)
        DetectionAlgorithm.__init__(self)

        # keep track of the object
        self.obj = obj

        # build a list of parameters and matching object property references
        kwargs = {}
        for property_name in self.properties_tracked:
            setattr(self, property_name, None)
            kwargs[property_name] = (obj, property_name)

        # let the base class set up the bindings and initial values
        self.bind(**kwargs)

        # list of all active subscriptions
        self.cov_subscriptions = SubscriptionList()

    def execute(self):
        if _debug: COVDetection._debug("execute")

        # something changed, send out the notifications
        self.send_cov_notifications()

    def send_cov_notifications(self):
        if _debug: COVDetection._debug("send_cov_notifications")

        # check for subscriptions
        if not len(self.cov_subscriptions):
            return

        # get the current time from the task manager
        current_time = TaskManager().get_time()
        if _debug: COVDetection._debug("    - current_time: %r", current_time)

        # create a list of values
        list_of_values = []
        for property_name in self.properties_reported:
            if _debug: COVDetection._debug("    - property_name: %r", property_name)

            # get the class
            property_datatype = self.obj.get_datatype(property_name)
            if _debug: COVDetection._debug("        - property_datatype: %r", property_datatype)

            # build the value
            bundle_value = property_datatype(self.obj._values[property_name])
            if _debug: COVDetection._debug("        - bundle_value: %r", bundle_value)

            # bundle it into a sequence
            property_value = PropertyValue(
                propertyIdentifier=property_name,
                value=Any(bundle_value),
                )

            # add it to the list
            list_of_values.append(property_value)
        if _debug: COVDetection._debug("    - list_of_values: %r", list_of_values)

        # loop through the subscriptions and send out notifications
        for cov in self.cov_subscriptions:
            if _debug: COVDetection._debug("    - cov: %s", repr(cov))

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
            request.initiatingDeviceIdentifier = self.obj._app.localDevice.objectIdentifier
            request.monitoredObjectIdentifier = cov.obj_id
            request.timeRemaining = time_remaining
            request.listOfValues = list_of_values
            if _debug: COVDetection._debug("    - request: %s", repr(request))

            # let the application send it
            self.obj._app.cov_notification(cov, request)

    def __str__(self):
        return "<" + self.__class__.__name__ + \
            "(" + ','.join(self.properties_tracked) + ')' + \
            ">"

class GenericCriteria(COVDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        )
    monitored_property_reference = 'presentValue'


@bacpypes_debugging
class COVIncrementCriteria(COVDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        'covIncrement',
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        )
    monitored_property_reference = 'presentValue'

    def __init__(self, obj):
        if _debug: COVIncrementCriteria._debug("__init__ %r", obj)
        COVDetection.__init__(self, obj)

        # previous reported value
        self.previous_reported_value = None

    @monitor_filter('presentValue')
    def present_value_filter(self, old_value, new_value):
        if _debug: COVIncrementCriteria._debug("present_value_filter %r %r", old_value, new_value)

        # first time around initialize to the old value
        if self.previous_reported_value is None:
            if _debug: COVIncrementCriteria._debug("    - first value: %r", old_value)
            self.previous_reported_value = old_value

        # see if it changed enough to trigger reporting
        value_changed = (new_value <= (self.previous_reported_value - self.covIncrement)) \
            or (new_value >= (self.previous_reported_value + self.covIncrement))
        if _debug: COVIncrementCriteria._debug("    - value significantly changed: %r", value_changed)

        return value_changed

    def send_cov_notifications(self):
        if _debug: COVIncrementCriteria._debug("send_cov_notifications")

        # when sending out notifications, keep the current value
        self.previous_reported_value = self.presentValue

        # continue
        COVDetection.send_cov_notifications(self)


class AccessDoorCriteria(COVDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        'doorAlarmState',
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        'doorAlarmState',
        )

class AccessPointCriteria(COVDetection):

    properties_tracked = (
        'accessEventTime',
        'statusFlags',
        )
    properties_reported = (
        'accessEvent',
        'statusFlags',
        'accessEventTag',
        'accessEventTime',
        'accessEventCredential',
        'accessEventAuthenticationFactor',
        )
    monitored_property_reference = 'accessEvent'

class CredentialDataInputCriteria(COVDetection):

    properties_tracked = (
        'updateTime',
        'statusFlags'
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        'updateTime',
        )

class LoadControlCriteria(COVDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        'requestedShedLevel',
        'startTime',
        'shedDuration',
        'dutyWindow',
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        'requestedShedLevel',
        'startTime',
        'shedDuration',
        'dutyWindow',
        )

class PulseConverterCriteria(COVDetection):

    properties_tracked = (
        'presentValue',
        'statusFlags',
        )
    properties_reported = (
        'presentValue',
        'statusFlags',
        )

# mapping from object type to appropriate criteria class
criteria_type_map = {
    'accessPoint': AccessPointCriteria,
    'analogInput': COVIncrementCriteria,
    'analogOutput': COVIncrementCriteria,
    'analogValue': COVIncrementCriteria,
    'largeAnalogValue': COVIncrementCriteria,
    'integerValue': COVIncrementCriteria,
    'positiveIntegerValue': COVIncrementCriteria,
    'lightingOutput': COVIncrementCriteria,
    'binaryInput': GenericCriteria,
    'binaryOutput': GenericCriteria,
    'binaryValue': GenericCriteria,
    'lifeSafetyPoint': GenericCriteria,
    'lifeSafetyZone': GenericCriteria,
    'multiStateInput': GenericCriteria,
    'multiStateOutput': GenericCriteria,
    'multiStateValue': GenericCriteria,
    'octetString': GenericCriteria,
    'characterString': GenericCriteria,
    'timeValue': GenericCriteria,
    'dateTimeValue': GenericCriteria,
    'dateValue': GenericCriteria,
    'timePatternValue': GenericCriteria,
    'datePatternValue': GenericCriteria,
    'dateTimePatternValue': GenericCriteria,
    'credentialDataInput': CredentialDataInputCriteria,
    'loadControl': LoadControlCriteria,
    'pulseConverter': PulseConverterCriteria,
    }

#
#   ActiveCOVSubscriptions
#

@bacpypes_debugging
class ActiveCOVSubscriptions(Property):

    def __init__(self):
        Property.__init__(
            self, 'activeCovSubscriptions', SequenceOf(COVSubscription),
            default=None, optional=True, mutable=False,
            )

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: ActiveCOVSubscriptions._debug("ReadProperty %s arrayIndex=%r", obj, arrayIndex)

        # get the current time from the task manager
        current_time = TaskManager().get_time()
        if _debug: ActiveCOVSubscriptions._debug("    - current_time: %r", current_time)

        # start with an empty sequence
        cov_subscriptions = SequenceOf(COVSubscription)()

        # loop through the object and detection list
        for obj, cov_detection in self.cov_detections.items():
            for cov in cov_detection.cov_subscriptions:
                # calculate time remaining
                if not cov.lifetime:
                    time_remaining = 0
                else:
                    time_remaining = int(cov.taskTime - current_time)

                    # make sure it is at least one second
                    if not time_remaining:
                        time_remaining = 1

                recipient_process = RecipientProcess(
                    recipient=Recipient(
                        address=DeviceAddress(
                            networkNumber=cov.client_addr.addrNet or 0,
                            macAddress=cov.client_addr.addrAddr,
                            ),
                        ),
                    processIdentifier=cov.proc_id,
                    )

                cov_subscription = COVSubscription(
                    recipient=recipient_process,
                    monitoredPropertyReference=ObjectPropertyReference(
                        objectIdentifier=cov.obj_id,
                        propertyIdentifier=cov_detection.monitored_property_reference,
                        ),
                    issueConfirmedNotifications=cov.confirmed,
                    timeRemaining=time_remaining,
                    )
                if hasattr(cov_detection, 'covIncrement'):
                    cov_subscription.covIncrement = cov_detection.covIncrement
                if _debug: ActiveCOVSubscriptions._debug("    - cov_subscription: %r", cov_subscription)

                # add the list
                cov_subscriptions.append(cov_subscription)

            # add the list
            cov_subscriptions.append(cov_subscription)

        return cov_subscriptions

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')


#
#   ChangeOfValueServices
#

@bacpypes_debugging
class ChangeOfValueServices(Capability):

    def __init__(self):
        if _debug: ChangeOfValueServices._debug("__init__")
        Capability.__init__(self)

        # map from an object to its detection algorithm
        self.cov_detections = {}

        # if there is a local device object, make sure it has an active COV
        # subscriptions property
        if self.localDevice and self.localDevice.activeCovSubscriptions is None:
            self.localDevice.add_property(ActiveCOVSubscriptions())

    def add_subscription(self, cov):
        if _debug: ChangeOfValueServices._debug("add_subscription %r", cov)

        # add it to the subscription list for its object
        self.cov_detections[cov.obj_ref].cov_subscriptions.append(cov)

    def cancel_subscription(self, cov):
        if _debug: ChangeOfValueServices._debug("cancel_subscription %r", cov)

        # cancel the subscription timeout
        if cov.isScheduled:
            cov.suspend_task()
            if _debug: ChangeOfValueServices._debug("    - task suspended")

        # get the detection algorithm object
        cov_detection = self.cov_detections[cov.obj_ref]

        # remove it from the subscription list for its object
        cov_detection.cov_subscriptions.remove(cov)

        # if the detection algorithm doesn't have any subscriptions, remove it
        if not len(cov_detection.cov_subscriptions):
            if _debug: ChangeOfValueServices._debug("    - no more subscriptions")

            # unbind all the hooks into the object
            cov_detection.unbind()

            # delete it from the object map
            del self.cov_detections[cov.obj_ref]

    def cov_notification(self, cov, request):
        if _debug: ChangeOfValueServices._debug("cov_notification %s %s", str(cov), str(request))

        # create an IOCB with the request
        iocb = IOCB(request)
        if _debug: ChangeOfValueServices._debug("    - iocb: %r", iocb)

        # add a callback for the response, even if it was unconfirmed
        iocb.cov = cov
        iocb.add_callback(self.cov_confirmation)

        # send the request via the ApplicationIOController
        self.request_io(iocb)

    def cov_confirmation(self, iocb):
        if _debug: ChangeOfValueServices._debug("cov_confirmation %r", iocb)

        # do something for success
        if iocb.ioResponse:
            if _debug: ChangeOfValueServices._debug("    - ack")
            self.cov_ack(iocb.cov, iocb.args[0], iocb.ioResponse)

        elif isinstance(iocb.ioError, Error):
            if _debug: ChangeOfValueServices._debug("    - error: %r", iocb.ioError.errorCode)
            self.cov_error(iocb.cov, iocb.args[0], iocb.ioError)

        elif isinstance(iocb.ioError, RejectPDU):
            if _debug: ChangeOfValueServices._debug("    - reject: %r", iocb.ioError.apduAbortRejectReason)
            self.cov_reject(iocb.cov, iocb.args[0], iocb.ioError)

        elif isinstance(iocb.ioError, AbortPDU):
            if _debug: ChangeOfValueServices._debug("    - abort: %r", iocb.ioError.apduAbortRejectReason)
            self.cov_abort(iocb.cov, iocb.args[0], iocb.ioError)

    def cov_ack(self, cov, request, response):
        if _debug: ChangeOfValueServices._debug("cov_ack %r %r %r", cov, request, response)

    def cov_error(self, cov, request, response):
        if _debug: ChangeOfValueServices._debug("cov_error %r %r %r", cov, request, response)

    def cov_reject(self, cov, request, response):
        if _debug: ChangeOfValueServices._debug("cov_reject %r %r %r", cov, request, response)

    def cov_abort(self, cov, request, response):
        if _debug: ChangeOfValueServices._debug("cov_abort %r %r %r", cov, request, response)

        ### delete the rest of the pending requests for this client

    def do_SubscribeCOVRequest(self, apdu):
        if _debug: ChangeOfValueServices._debug("do_SubscribeCOVRequest %r", apdu)

        # extract the pieces
        client_addr = apdu.pduSource
        proc_id = apdu.subscriberProcessIdentifier
        obj_id = apdu.monitoredObjectIdentifier
        confirmed = apdu.issueConfirmedNotifications
        lifetime = apdu.lifetime

        # request is to cancel the subscription
        cancel_subscription = (confirmed is None) and (lifetime is None)

        # find the object
        obj = self.get_object_id(obj_id)
        if _debug: ChangeOfValueServices._debug("    - object: %r", obj)
        if not obj:
            raise ExecutionError(errorClass='object', errorCode='unknownObject')

        # look for an algorithm already associated with this object
        cov_detection = self.cov_detections.get(obj, None)

        # if there isn't one, make one and associate it with the object
        if not cov_detection:
            # look for an associated class and if it's not there it's not supported
            criteria_class = criteria_type_map.get(obj_id[0], None)
            if not criteria_class:
                raise ExecutionError(errorClass='services', errorCode='covSubscriptionFailed')

            # make one of these and bind it to the object
            cov_detection = criteria_class(obj)

            # keep track of it for other subscriptions
            self.cov_detections[obj] = cov_detection
        if _debug: ChangeOfValueServices._debug("    - cov_detection: %r", cov_detection)

        # can a match be found?
        cov = cov_detection.cov_subscriptions.find(client_addr, proc_id, obj_id)
        if _debug: ChangeOfValueServices._debug("    - cov: %r", cov)

        # if a match was found, update the subscription
        if cov:
            if cancel_subscription:
                if _debug: ChangeOfValueServices._debug("    - cancel the subscription")
                self.cancel_subscription(cov)
            else:
                if _debug: ChangeOfValueServices._debug("    - renew the subscription")
                cov.renew_subscription(lifetime)
        else:
            if cancel_subscription:
                if _debug: ChangeOfValueServices._debug("    - cancel a subscription that doesn't exist")
            else:
                if _debug: ChangeOfValueServices._debug("    - create a subscription")

                # make a subscription
                cov = Subscription(obj, client_addr, proc_id, obj_id, confirmed, lifetime)
                if _debug: ChangeOfValueServices._debug("    - cov: %r", cov)

                # add it to our subscriptions lists
                self.add_subscription(cov)

        # success
        response = SimpleAckPDU(context=apdu)

        # return the result
        self.response(response)
