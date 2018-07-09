#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Analog Value COV Services
------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.apdu import (
    SubscribeCOVRequest, SimpleAckPDU,
    ConfirmedCOVNotificationRequest, UnconfirmedCOVNotificationRequest,
    )

from bacpypes.service.cov import ChangeOfValueServices
from bacpypes.local.device import LocalDeviceObject
from bacpypes.object import AnalogValueObject

from .helpers import ApplicationNetwork, ApplicationStateMachine, COVTestClientServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestAnalogValue(unittest.TestCase):

    def test_8_10_1(self):
        """Confirmed Notifications Subscription"""
        if _debug: TestAnalogValue._debug("test_8_10_1")

        # create a network
        anet = ApplicationNetwork("test_8_10_1")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # add it to the implementation
        anet.iut.add_object(test_av)

        # wait for the subscription
        anet.iut.start_state.doc("8.10.1-1-0") \
            .receive(SubscribeCOVRequest).doc("8.10.1-1-1") \
            .success()

        # send the subscription, wait for the ack
        anet.td.start_state.doc("8.10.1-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=True,
                lifetime=30,
                )).doc("8.10.1-2-1") \
            .receive(SimpleAckPDU).doc("8.10.1-2-2") \
            .success()

        # run the group
        anet.run()

    def test_8_10_2(self):
        """Unconfirmed Notifications Subscription"""
        if _debug: TestAnalogValue._debug("test_8_10_2")

        # create a network
        anet = ApplicationNetwork("test_8_10_2")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # add it to the implementation
        anet.iut.add_object(test_av)

        # wait for the subscription
        anet.iut.start_state.doc("8.10.2-1-0") \
            .receive(SubscribeCOVRequest).doc("8.10.2-1-1") \
            .success()

        # send the subscription, wait for the ack
        anet.td.start_state.doc("8.10.2-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("8.10.2-2-1") \
            .receive(SimpleAckPDU).doc("8.10.2-2-2") \
            .success()

        # run the group, cut the time limit short
        anet.run(time_limit=5.0)

        # check that the IUT still has the detection
        if _debug: TestAnalogValue._debug("    - detections: %r", anet.iut.cov_detections)
        assert len(anet.iut.cov_detections) == 1

        # pop out the subscription list and criteria
        obj_ref, criteria = anet.iut.cov_detections.popitem()
        if _debug: TestAnalogValue._debug("    - criteria: %r", criteria)

        # get the list of subscriptions from the criteria
        subscriptions = criteria.cov_subscriptions.cov_subscriptions
        if _debug: TestAnalogValue._debug("    - subscriptions: %r", subscriptions)
        assert len(subscriptions) == 1

    def test_8_10_3(self):
        """Canceling a Subscription"""
        if _debug: TestAnalogValue._debug("test_8_10_3")

        # create a network
        anet = ApplicationNetwork("test_8_10_3")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # add it to the implementation
        anet.iut.add_object(test_av)

        # wait for the subscription, then for the cancelation
        anet.iut.start_state.doc("8.10.3-1-0") \
            .receive(SubscribeCOVRequest).doc("8.10.3-1-1") \
            .receive(SubscribeCOVRequest).doc("8.10.3-1-2") \
            .success()

        # send the subscription, wait for the ack, then send the cancelation
        # and wait for the ack.  Ignore the notification that is sent when
        # after the subscription
        anet.td.start_state.doc("8.10.3-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("8.10.3-2-1") \
            .ignore(UnconfirmedCOVNotificationRequest) \
            .receive(SimpleAckPDU).doc("8.10.3-2-2") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                )).doc("8.10.3-2-1") \
            .ignore(UnconfirmedCOVNotificationRequest) \
            .receive(SimpleAckPDU).doc("8.10.3-2-2") \
            .success()

        # run the group
        anet.run()

    def test_8_10_4(self):
        """Requests 8 Hour Lifetimes"""
        if _debug: TestAnalogValue._debug("test_8_10_4")

        # create a network
        anet = ApplicationNetwork("test_8_10_4")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # add it to the implementation
        anet.iut.add_object(test_av)

        # wait for the subscription
        anet.iut.start_state.doc("8.10.4-1-0") \
            .receive(SubscribeCOVRequest).doc("8.10.4-1-1") \
            .success()

        # send the subscription, wait for the ack
        anet.td.start_state.doc("8.10.4-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=True,
                lifetime=28800,
                )).doc("8.10.4-2-1") \
            .receive(SimpleAckPDU).doc("8.10.4-2-2") \
            .success()

        # run the group
        anet.run()

    def test_9_10_1_1(self):
        if _debug: TestAnalogValue._debug("test_9_10_1_1")

        notification_fail_time = 0.5

        # create a network
        anet = ApplicationNetwork("test_9_10_1_1")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # add it to the implementation
        anet.iut.add_object(test_av)

        # wait for the subscription, wait for the notification ack
        anet.iut.start_state.doc("9.10.1.1-1-0") \
            .receive(SubscribeCOVRequest).doc("9.10.1.1-1-1") \
            .receive(SimpleAckPDU).doc("9.10.1.1-1-2") \
            .timeout(10).doc("9.10.1.1-1-3") \
            .success()

        # test device is quiet
        wait_for_notification = \
            anet.td.start_state.doc("9.10.1.1-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=True,
                lifetime=30,
                )).doc("9.10.1.1-2-1") \
            .receive(SimpleAckPDU).doc("9.10.1.1-2-2")

        # after the ack, don't wait too long for the notification
        wait_for_notification \
            .timeout(notification_fail_time).doc("9.10.1.1-2-3").fail()

        # if the notification is received, success
        wait_for_notification \
            .receive(ConfirmedCOVNotificationRequest).doc("9.10.1.1-2-4") \
            .timeout(10).doc("9.10.1.1-2-5") \
            .success()

        # run the group
        anet.run()

    def test_no_traffic(self):
        """Test basic configuration of a network."""
        if _debug: TestAnalogValue._debug("test_no_traffic")

        # create a network
        anet = ApplicationNetwork("test_no_traffic")

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # an easy way to change the present value
        write_test_av = lambda v: setattr(test_av, 'presentValue', v)

        # add it to the implementation
        anet.iut.add_object(test_av)

        # make some transitions
        anet.iut.start_state.doc("1-1-0") \
            .call(write_test_av, 100.0).doc("1-1-1") \
            .timeout(1).doc("1-1-2") \
            .call(write_test_av, 0.0).doc("1-1-3") \
            .timeout(1).doc("1-1-4") \
            .success()

        # test device is quiet
        anet.td.start_state.timeout(5).success()

        # run the group
        anet.run()

    def test_8_2_1(self):
        """To verify that the IUT can initiate ConfirmedCOVNotification service
        requests conveying a change of the Present_Value property of Analog
        Input, Analog Output, and Analog Value objects."""
        if _debug: TestAnalogValue._debug("test_8_2_1")

        # create a network
        anet = ApplicationNetwork("test_8_2_1")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # an easy way to change the present value
        write_test_av = lambda v: setattr(test_av, 'presentValue', v)

        # add it to the implementation
        anet.iut.add_object(test_av)

        # receive the subscription request, wait until the client has
        # received the ack and the 'instant' notification.  Then change the
        # value a little bit and nothing should be sent.  Change it some more
        # and wait for the notification ack.
        anet.iut.start_state.doc("2-1-0") \
            .receive(SubscribeCOVRequest).doc("2-1-1") \
            .receive(SimpleAckPDU).doc("2-1-2") \
            .wait_event("e1").doc("2-1-3") \
            .call(write_test_av, 5.0).doc("2-1-4") \
            .timeout(5).doc("2-2-5") \
            .call(write_test_av, 10.0).doc("2-1-6") \
            .receive(SimpleAckPDU).doc("2-1-7") \
            .timeout(10).doc("2-2-8") \
            .success()

        # send the subscription request, wait for the ack and the 'instant'
        # notification, set the event so the IUT can continue, then wait
        # for the next notification
        anet.td.start_state.doc("2-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=True,
                lifetime=30,
                )).doc("2-2-1") \
            .receive(SimpleAckPDU).doc("2-2-2") \
            .receive(ConfirmedCOVNotificationRequest).doc("2-2-4") \
            .set_event("e1").doc("2-2-3") \
            .receive(ConfirmedCOVNotificationRequest).doc("2-2-4") \
            .timeout(10).doc("2-2-5") \
            .success()

        # run the group
        anet.run()

    def test_simple_transition_unconfirmed(self):
        if _debug: TestAnalogValue._debug("test_simple_transition_unconfirmed")

        # create a network
        anet = ApplicationNetwork("test_simple_transition_unconfirmed")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # an easy way to change the present value
        write_test_av = lambda v: setattr(test_av, 'presentValue', v)

        # add it to the implementation
        anet.iut.add_object(test_av)

        # receive the subscription request, wait until the client has
        # received the ack and the 'instant' notification.  Then change the
        # value, no ack coming back
        anet.iut.start_state.doc("3-1-0") \
            .receive(SubscribeCOVRequest).doc("3-1-1") \
            .wait_event("e1").doc("3-1-2") \
            .call(write_test_av, 100.0).doc("3-1-3") \
            .timeout(10).doc("3-2-4") \
            .success()

        # test device is quiet
        anet.td.start_state.doc("3-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("3-2-1") \
            .receive(SimpleAckPDU).doc("3-2-2") \
            .receive(UnconfirmedCOVNotificationRequest).doc("3-2-3") \
            .set_event("e1").doc("3-2-4") \
            .receive(UnconfirmedCOVNotificationRequest).doc("3-2-5") \
            .timeout(10).doc("3-2-6") \
            .success()

        # run the group
        anet.run()

    def test_changing_status_flags(self):
        """This test changes the status flags of binary value point to verify
        that the detection picks up other changes, most tests just change the
        present value."""
        if _debug: TestAnalogValue._debug("test_changing_status_flags")

        # create a network
        anet = ApplicationNetwork("test_changing_status_flags")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # an easy way to change the present value
        def test_av_fault():
            if _debug: TestAnalogValue._debug("test_av_fault")
            test_av.statusFlags = [0, 1, 0, 0]

        # add it to the implementation
        anet.iut.add_object(test_av)

        # receive the subscription request, wait until the client has
        # received the ack and the 'instant' notification.  Then change the
        # value, no ack coming back
        anet.iut.start_state.doc("4-1-0") \
            .receive(SubscribeCOVRequest).doc("4-1-1") \
            .wait_event("e1").doc("4-1-2") \
            .call(test_av_fault).doc("4-1-3") \
            .timeout(10).doc("4-2-4") \
            .success()

        # test device is quiet
        anet.td.start_state.doc("4-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("4-2-1") \
            .receive(SimpleAckPDU).doc("4-2-2") \
            .receive(UnconfirmedCOVNotificationRequest).doc("4-2-3") \
            .set_event("e1").doc("4-2-4") \
            .receive(UnconfirmedCOVNotificationRequest).doc("4-2-5") \
            .timeout(10).doc("4-2-6") \
            .success()

        # run the group
        anet.run()

    def test_changing_properties(self):
        """This test changes the value of multiple properties to verify that
        only one COV notification is sent."""
        if _debug: TestAnalogValue._debug("test_changing_properties")

        # create a network
        anet = ApplicationNetwork("test_changing_properties")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # an easy way to change the present value
        def test_av_fault():
            if _debug: TestAnalogValue._debug("test_av_fault")
            test_av.presentValue = 100.0
            test_av.statusFlags = [0, 0, 1, 0]

        # add it to the implementation
        anet.iut.add_object(test_av)

        # receive the subscription request, wait until the client has
        # received the ack and the 'instant' notification.  Then change the
        # value, no ack coming back
        anet.iut.start_state.doc("5-1-0") \
            .receive(SubscribeCOVRequest).doc("5-1-1") \
            .wait_event("e1").doc("5-1-2") \
            .call(test_av_fault).doc("5-1-3") \
            .timeout(10).doc("5-2-4") \
            .success()

        # test device is quiet
        anet.td.start_state.doc("5-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("5-2-1") \
            .receive(SimpleAckPDU).doc("5-2-2") \
            .receive(UnconfirmedCOVNotificationRequest).doc("5-2-3") \
            .set_event("e1").doc("5-2-4") \
            .receive(UnconfirmedCOVNotificationRequest).doc("5-2-5") \
            .timeout(10).doc("5-2-6") \
            .success()

        # run the group
        anet.run()

    def test_multiple_subscribers(self):
        """This has more than one subscriber for the object."""
        if _debug: TestAnalogValue._debug("test_multiple_subscribers")

        # create a network
        anet = ApplicationNetwork("test_multiple_subscribers")

        # add the ability to accept COV notifications to the TD
        anet.td.add_capability(COVTestClientServices)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make an analog value object
        test_av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='av',
            presentValue=0.0,
            statusFlags=[0, 0, 0, 0],
            covIncrement=10.0,
            )

        # an easy way to change both the present value and status flags
        # which should trigger only one notification
        def test_av_fault():
            if _debug: TestAnalogValue._debug("test_av_fault")
            test_av.presentValue = 100.0
            test_av.statusFlags = [0, 0, 1, 0]

        # add it to the implementation
        anet.iut.add_object(test_av)

        # add another test device object
        anet.td2_device_object = LocalDeviceObject(
            objectName="td2",
            objectIdentifier=('device', 30),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=999,
            )

        # another test device
        anet.td2 = ApplicationStateMachine(anet.td2_device_object, anet.vlan)
        anet.td2.add_capability(COVTestClientServices)
        anet.append(anet.td2)

        # receive the subscription requests, wait until both clients have
        # received the ack and the 'instant' notification.  Then change the
        # value, no ack coming back
        anet.iut.start_state.doc("6-1-0") \
            .receive(SubscribeCOVRequest, pduSource=anet.td.address).doc("6-1-1") \
            .receive(SubscribeCOVRequest, pduSource=anet.td2.address).doc("6-1-2") \
            .wait_event("e2").doc("6-1-3") \
            .call(test_av_fault).doc("6-1-4") \
            .timeout(10).doc("6-2-5") \
            .success()

        # first test device; send the subscription request, get an ack
        # followed by the 'instant' notification
        anet.td.start_state.doc("6-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("6-2-1") \
            .receive(SimpleAckPDU).doc("6-2-2") \
            .receive(UnconfirmedCOVNotificationRequest).doc("6-2-3") \
            .set_event("e1").doc("6-2-4") \
            .receive(UnconfirmedCOVNotificationRequest).doc("6-2-5") \
            .timeout(10).doc("6-2-6") \
            .success()

        # same pattern for the other test device
        anet.td2.start_state.doc("6-3-0") \
            .wait_event("e1").doc("6-3-1") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('analogValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("6-3-2") \
            .receive(SimpleAckPDU).doc("6-3-3") \
            .receive(UnconfirmedCOVNotificationRequest).doc("6-3-4") \
            .set_event("e2").doc("6-3-5") \
            .receive(UnconfirmedCOVNotificationRequest).doc("6-3-6") \
            .timeout(10).doc("6-3-7") \
            .success()

        # run the group
        anet.run()

