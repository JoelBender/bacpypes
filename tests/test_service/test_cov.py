#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device Services
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.capability import Capability

from bacpypes.pdu import Address, PDU
from bacpypes.basetypes import (
    DeviceAddress, COVSubscription, PropertyValue,
    Recipient, RecipientProcess, ObjectPropertyReference,
    )
from bacpypes.apdu import (
    SubscribeCOVRequest,
    ConfirmedCOVNotificationRequest, UnconfirmedCOVNotificationRequest,
    SimpleAckPDU, Error, RejectPDU, AbortPDU,
    )

from bacpypes.service.cov import (
    ChangeOfValueServices,
    )

from bacpypes.object import (
    BinaryValueObject,
    )

from .helpers import ApplicationNetwork, SnifferNode

# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   COVTestClientServices
#

@bacpypes_debugging
class COVTestClientServices(Capability):

    def do_ConfirmedCOVNotificationRequest(self, apdu):
        if _debug: COVTestClientServices._debug("do_ConfirmedCOVNotificationRequest %r", apdu)

        # the test device needs to set these
        assert hasattr(self, 'test_ack')
        assert hasattr(self, 'test_reject')
        assert hasattr(self, 'test_abort')

        print("{} changed\n    {}".format(
            apdu.monitoredObjectIdentifier,
            ",\n    ".join("{} = {}".format(
                element.propertyIdentifier,
                str(element.value),
                ) for element in apdu.listOfValues),
            ))

        if self.test_ack:
            # success
            response = SimpleAckPDU(context=apdu)
            if _debug: COVTestClientServices._debug("    - simple_ack: %r", response)

        elif self.test_reject:
            # reject
            response = RejectPDU(reason=self.test_reject, context=apdu)
            if _debug: COVTestClientServices._debug("    - reject: %r", response)

        elif self.test_abort:
            # abort
            response = AbortPDU(reason=self.test_abort, context=apdu)
            if _debug: COVTestClientServices._debug("    - abort: %r", response)

        # return the result
        self.response(response)

    def do_UnconfirmedCOVNotificationRequest(self, apdu):
        if _debug: COVTestClientServices._debug("do_UnconfirmedCOVNotificationRequest %r", apdu)

        print("{} changed\n    {}".format(
            apdu.monitoredObjectIdentifier,
            ",\n    ".join("{} is {}".format(
                element.propertyIdentifier,
                str(element.value),
                ) for element in apdu.listOfValues),
            ))

@bacpypes_debugging
class TestBasic(unittest.TestCase):

    def test_basic(self):
        """Test basic configuration of a network."""
        if _debug: TestBasic._debug("test_basic")

        # create a network
        anet = ApplicationNetwork("test_basic")

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # all start states are successful
        anet.td.start_state.success()
        anet.iut.start_state.success()

        # run the group
        anet.run()

@bacpypes_debugging
class TestBinaryValue(unittest.TestCase):

    def test_no_traffic(self):
        """Test basic configuration of a network."""
        if _debug: TestBinaryValue._debug("test_no_traffic")

        # create a network
        anet = ApplicationNetwork("test_no_traffic")

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # make a binary value object
        test_bv = BinaryValueObject(
            objectIdentifier=('binaryValue', 1),
            objectName='bv',
            presentValue='inactive',
            statusFlags=[0, 0, 0, 0],
            )

        # an easy way to change the present value
        write_test_bv = lambda v: setattr(test_bv, 'presentValue', v)

        # add it to the implementation
        anet.iut.add_object(test_bv)

        # make some transitions
        anet.iut.start_state.doc("1-1-0") \
            .call(write_test_bv, 'active').doc("1-1-1") \
            .timeout(1).doc("1-1-2") \
            .call(write_test_bv, 'inactive').doc("1-1-3") \
            .timeout(1).doc("1-1-4") \
            .success()

        # test device is quiet
        anet.td.start_state.timeout(5).success()

        # run the group
        anet.run()

    def test_simple_transition_confirmed(self):
        if _debug: TestBinaryValue._debug("test_simple_transition_confirmed")

        # create a network
        anet = ApplicationNetwork("test_simple_transition_confirmed")

        # add the service capability to the IUT
        anet.td.add_capability(COVTestClientServices)
        anet.iut.add_capability(ChangeOfValueServices)

        # make a binary value object
        test_bv = BinaryValueObject(
            objectIdentifier=('binaryValue', 1),
            objectName='bv',
            presentValue='inactive',
            statusFlags=[0, 0, 0, 0],
            )

        # an easy way to change the present value
        write_test_bv = lambda v: setattr(test_bv, 'presentValue', v)

        # add it to the implementation
        anet.iut.add_object(test_bv)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # wait for the subscription, change the value
        anet.iut.start_state.doc("2-1-0") \
            .receive(SubscribeCOVRequest).doc("2-1-1") \
            .wait_event("e1").doc("2-1-2") \
            .call(write_test_bv, 'active').doc("2-1-3") \
            .receive(SimpleAckPDU).doc("2-1-4") \
            .timeout(10).doc("2-2-5") \
            .success()

        # test device is quiet
        anet.td.start_state.doc("2-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('binaryValue', 1),
                issueConfirmedNotifications=True,
                lifetime=30,
                )).doc("2-2-1") \
            .receive(SimpleAckPDU).doc("2-2-2") \
            .set_event("e1").doc("2-2-3") \
            .receive(ConfirmedCOVNotificationRequest).doc("2-2-4") \
            .timeout(10).doc("2-2-5") \
            .success()

        # run the group
        anet.run()

    def test_simple_transition_unconfirmed(self):
        if _debug: TestBinaryValue._debug("test_simple_transition_unconfirmed")

        # create a network
        anet = ApplicationNetwork("test_simple_transition_unconfirmed")

        # add the service capability to the IUT
        anet.td.add_capability(COVTestClientServices)
        anet.iut.add_capability(ChangeOfValueServices)

        # make a binary value object
        test_bv = BinaryValueObject(
            objectIdentifier=('binaryValue', 1),
            objectName='bv',
            presentValue='inactive',
            statusFlags=[0, 0, 0, 0],
            )

        # an easy way to change the present value
        write_test_bv = lambda v: setattr(test_bv, 'presentValue', v)

        # add it to the implementation
        anet.iut.add_object(test_bv)

        # tell the TD how to respond to confirmed notifications
        anet.td.test_ack = True
        anet.td.test_reject = None
        anet.td.test_abort = None

        # wait for the subscription, change the value
        anet.iut.start_state.doc("3-1-0") \
            .receive(SubscribeCOVRequest).doc("3-1-1") \
            .wait_event("e1").doc("3-1-2") \
            .call(write_test_bv, 'active').doc("3-1-3") \
            .timeout(10).doc("3-2-4") \
            .success()

        # test device is quiet
        anet.td.start_state.doc("3-2-0") \
            .send(SubscribeCOVRequest(
                destination=anet.iut.address,
                subscriberProcessIdentifier=1,
                monitoredObjectIdentifier=('binaryValue', 1),
                issueConfirmedNotifications=False,
                lifetime=30,
                )).doc("3-2-1") \
            .receive(SimpleAckPDU).doc("3-2-2") \
            .set_event("e1").doc("3-2-3") \
            .receive(UnconfirmedCOVNotificationRequest).doc("3-2-4") \
            .timeout(10).doc("3-2-5") \
            .success()

        # run the group
        anet.run()

