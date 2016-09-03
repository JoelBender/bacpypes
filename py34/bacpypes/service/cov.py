#!/usr/bin/env python

from collections import defaultdict

from ..debugging import bacpypes_debugging, DebugContents, ModuleLogger
from ..capability import Capability

from ..task import OneShotTask, TaskManager

from ..basetypes import DeviceAddress, COVSubscription, PropertyValue, \
    Recipient, RecipientProcess, ObjectPropertyReference
from ..constructeddata import SequenceOf, Any
from ..apdu import ConfirmedCOVNotificationRequest, \
    UnconfirmedCOVNotificationRequest, \
    SimpleAckPDU, Error, RejectPDU, AbortPDU
from ..errors import ExecutionError

from ..object import Object, Property, PropertyError, \
    AccessDoorObject, AccessPointObject, \
    AnalogInputObject, AnalogOutputObject,  AnalogValueObject, \
    LargeAnalogValueObject, IntegerValueObject, PositiveIntegerValueObject, \
    LightingOutputObject, BinaryInputObject, BinaryOutputObject, \
    BinaryValueObject, LifeSafetyPointObject, LifeSafetyZoneObject, \
    MultiStateInputObject, MultiStateOutputObject, MultiStateValueObject, \
    OctetStringValueObject, CharacterStringValueObject, TimeValueObject, \
    DateTimeValueObject, DateValueObject, TimePatternValueObject, \
    DatePatternValueObject, DateTimePatternValueObject, \
    CredentialDataInputObject, LoadControlObject, LoopObject, \
    PulseConverterObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
_generic_criteria_classes = {}
_cov_increment_criteria_classes = {}

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

        # add ourselves to the subscription list for this object
        obj_ref._cov_subscriptions.append(self)

        # add ourselves to the list of all active subscriptions
        obj_ref._app.active_cov_subscriptions.append(self)

        # if lifetime is non-zero, schedule the subscription to expire
        if lifetime != 0:
            self.install_task(delta=self.lifetime)

    def cancel_subscription(self):
        if _debug: Subscription._debug("cancel_subscription")

        # suspend the task
        self.suspend_task()

        # remove ourselves from the other subscriptions for this object
        self.obj_ref._cov_subscriptions.remove(self)

        # remove ourselves from the list of all active subscriptions
        self.obj_ref._app.active_cov_subscriptions.remove(self)

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
#   COVCriteria
#

@bacpypes_debugging
class COVCriteria:

    _properties_tracked = ()
    _properties_reported = ()
    _monitored_property_reference = None

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


class GenericCriteria(COVCriteria):

    _properties_tracked = (
        'presentValue',
        'statusFlags',
        )
    _properties_reported = (
        'presentValue',
        'statusFlags',
        )
    _monitored_property_reference = 'presentValue'


@bacpypes_debugging
class COVIncrementCriteria(COVCriteria):

    _properties_tracked = (
        'presentValue',
        'statusFlags',
        )
    _properties_reported = (
        'presentValue',
        'statusFlags',
        )
    _monitored_property_reference = 'presentValue'

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
            if _debug: COVIncrementCriteria._debug("    - present value changed")

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

#
#   Change of Value Mixin
#

class COVObjectMixin(object):

    _debug_contents = (
        '_cov_subscriptions',
        '_cov_properties',
        )

    def __init__(self, **kwargs):
        if _debug: COVObjectMixin._debug("__init__ %r", kwargs)
        super(COVObjectMixin, self).__init__(**kwargs)

        # list of all active subscriptions
        self._cov_subscriptions = SubscriptionList()

        # snapshot the properties tracked
        self._cov_properties = {}
        for property_name in self._properties_tracked:
            self._cov_properties[property_name] = self._values[property_name]

    def __setattr__(self, attr, value):
        if _debug: COVObjectMixin._debug("__setattr__ %r %r", attr, value)

        if attr.startswith('_') or attr[0].isupper() or (attr == 'debug_contents'):
            return object.__setattr__(self, attr, value)

        # use the default implementation
        super(COVObjectMixin, self).__setattr__(attr, value)

        # check for special properties
        if attr in self._properties_tracked:
            if _debug: COVObjectMixin._debug("    - property tracked")

            # check if it is significant
            if self._check_criteria():
                if _debug: COVObjectMixin._debug("    - send notifications")
                self._send_cov_notifications()
            else:
                if _debug: COVObjectMixin._debug("    - no notifications necessary")
        else:
            if _debug: COVObjectMixin._debug("    - property not tracked")

    def WriteProperty(self, propid, value, arrayIndex=None, priority=None, direct=False):
        if _debug: COVObjectMixin._debug("WriteProperty %r %r arrayIndex=%r priority=%r", propid, value, arrayIndex, priority)

        # normalize the property identifier
        if isinstance(propid, int):
            # get the property
            prop = self._properties.get(propid)
            if _debug: Object._debug("    - prop: %r", prop)

            if not prop:
                raise PropertyError(propid)

            # use the name from now on
            propid = prop.identifier
            if _debug: Object._debug("    - propid: %r", propid)

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


class AccessDoorCriteria(COVCriteria):

    _properties_tracked = (
        'presentValue',
        'statusFlags',
        'doorAlarmState',
        )
    _properties_reported = (
        'presentValue',
        'statusFlags',
        'doorAlarmState',
        )

class AccessDoorObjectCOV(COVObjectMixin, AccessDoorCriteria, AccessDoorObject):
    pass


class AccessPointCriteria(COVCriteria):

    _properties_tracked = (
        'accessEventTime',
        'statusFlags',
        )
    _properties_reported = (
        'accessEvent',
        'statusFlags',
        'accessEventTag',
        'accessEventTime',
        'accessEventCredential',
        'accessEventAuthenticationFactor',
        )
    _monitored_property_reference = 'accessEvent'

class AccessPointObjectCOV(COVObjectMixin, AccessPointCriteria, AccessPointObject):
    pass

class AnalogInputObjectCOV(COVObjectMixin, COVIncrementCriteria, AnalogInputObject):
    pass

class AnalogOutputObjectCOV(COVObjectMixin, COVIncrementCriteria, AnalogOutputObject):
    pass

class AnalogValueObjectCOV(COVObjectMixin, COVIncrementCriteria, AnalogValueObject):
    pass

class LargeAnalogValueObjectCOV(COVObjectMixin, COVIncrementCriteria, LargeAnalogValueObject):
    pass

class IntegerValueObjectCOV(COVObjectMixin, COVIncrementCriteria, IntegerValueObject):
    pass

class PositiveIntegerValueObjectCOV(COVObjectMixin, COVIncrementCriteria, PositiveIntegerValueObject):
    pass

class LightingOutputObjectCOV(COVObjectMixin, COVIncrementCriteria, LightingOutputObject):
    pass

class BinaryInputObjectCOV(COVObjectMixin, GenericCriteria, BinaryInputObject):
    pass

class BinaryOutputObjectCOV(COVObjectMixin, GenericCriteria, BinaryOutputObject):
    pass

class BinaryValueObjectCOV(COVObjectMixin, GenericCriteria, BinaryValueObject):
    pass

class LifeSafetyPointObjectCOV(COVObjectMixin, GenericCriteria, LifeSafetyPointObject):
    pass

class LifeSafetyZoneObjectCOV(COVObjectMixin, GenericCriteria, LifeSafetyZoneObject):
    pass

class MultiStateInputObjectCOV(COVObjectMixin, GenericCriteria, MultiStateInputObject):
    pass

class MultiStateOutputObjectCOV(COVObjectMixin, GenericCriteria, MultiStateOutputObject):
    pass

class MultiStateValueObjectCOV(COVObjectMixin, GenericCriteria, MultiStateValueObject):
    pass

class OctetStringValueObjectCOV(COVObjectMixin, GenericCriteria, OctetStringValueObject):
    pass

class CharacterStringValueObjectCOV(COVObjectMixin, GenericCriteria, CharacterStringValueObject):
    pass

class TimeValueObjectCOV(COVObjectMixin, GenericCriteria, TimeValueObject):
    pass

class DateTimeValueObjectCOV(COVObjectMixin, GenericCriteria, DateTimeValueObject):
    pass

class DateValueObjectCOV(COVObjectMixin, GenericCriteria, DateValueObject):
    pass

class TimePatternValueObjectCOV(COVObjectMixin, GenericCriteria, TimePatternValueObject):
    pass

class DatePatternValueObjectCOV(COVObjectMixin, GenericCriteria, DatePatternValueObject):
    pass

class DateTimePatternValueObjectCOV(COVObjectMixin, GenericCriteria, DateTimePatternValueObject):
    pass

class CredentialDataInputCriteria(COVCriteria):

    _properties_tracked = (
        'updateTime',
        'statusFlags'
        )
    _properties_reported = (
        'presentValue',
        'statusFlags',
        'updateTime',
        )

class CredentialDataInputObjectCOV(COVObjectMixin, CredentialDataInputCriteria, CredentialDataInputObject):
    pass

class LoadControlCriteria(COVCriteria):

    _properties_tracked = (
        'presentValue',
        'statusFlags',
        'requestedShedLevel',
        'startTime',
        'shedDuration',
        'dutyWindow',
        )
    _properties_reported = (
        'presentValue',
        'statusFlags',
        'requestedShedLevel',
        'startTime',
        'shedDuration',
        'dutyWindow',
        )

class LoadControlObjectCOV(COVObjectMixin, LoadControlCriteria, LoadControlObject):
    pass

class LoopObjectCOV(COVObjectMixin, COVIncrementCriteria, LoopObject):
    pass

class PulseConverterCriteria():

    _properties_tracked = (
        'presentValue',
        'statusFlags',
        )
    _properties_reported = (
        'presentValue',
        'statusFlags',
        )

class PulseConverterObjectCOV(COVObjectMixin, PulseConverterCriteria, PulseConverterObject):
    pass


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

        # the obj is a DeviceObject with a reference to the application
        for cov in obj._app.active_cov_subscriptions:
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
                    propertyIdentifier=cov.obj_ref._monitored_property_reference,
                    ),
                issueConfirmedNotifications=cov.confirmed,
                timeRemaining=time_remaining,
                # covIncrement=???,
                )
            if _debug: ActiveCOVSubscriptions._debug("    - cov_subscription: %r", cov_subscription)

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

        # list of active subscriptions
        self.active_cov_subscriptions = []

        # if there is a local device object, make sure it has an active COV
        # subscriptions property
        if self.localDevice and self.localDevice.activeCovSubscriptions is None:
            self.localDevice.add_property(ActiveCOVSubscriptions())

    def cov_notification(self, cov, request):
        if _debug: ChangeOfValueServices._debug("cov_notification %s %s", str(cov), str(request))

        # send the request
        iocb = self.request(request)

        # if this is confirmed, add a callback for the response, otherwise it
        # was unconfirmed
        if iocb:
            iocb.cov = cov
            iocb.add_callback(self.cov_confirmation)

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
        if _debug: ChangeOfValueServices._debug("    - other notifications deleted")

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
            raise Error(errorClass='object', errorCode='unknownObject')

        # can a match be found?
        cov = obj._cov_subscriptions.find(client_addr, proc_id, obj_id)
        if _debug: ChangeOfValueServices._debug("    - cov: %r", cov)

        # if a match was found, update the subscription
        if cov:
            if cancel_subscription:
                if _debug: ChangeOfValueServices._debug("    - cancel the subscription")
                cov.cancel_subscription()
            else:
                if _debug: ChangeOfValueServices._debug("    - renew the subscription")
                cov.renew_subscription(lifetime)
        else:
            if cancel_subscription:
                if _debug: ChangeOfValueServices._debug("    - cancel a subscription that doesn't exist")
            else:
                if _debug: ChangeOfValueServices._debug("    - create a subscription")

                cov = Subscription(obj, client_addr, proc_id, obj_id, confirmed, lifetime)
                if _debug: ChangeOfValueServices._debug("    - cov: %r", cov)

        # success
        response = SimpleAckPDU(context=apdu)

        # return the result
        self.response(response)
