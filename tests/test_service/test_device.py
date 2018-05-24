#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device Services
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address, PDU
from bacpypes.basetypes import PropertyReference
from bacpypes.apdu import (
    ConfirmedRequestSequence, SequenceOf, Element,
    WhoIsRequest, IAmRequest,
    WhoHasRequest, WhoHasObject, IHaveRequest,
    DeviceCommunicationControlRequest, ReadPropertyRequest,
    SimpleAckPDU, Error, RejectPDU, AbortPDU,
    )

from bacpypes.service.device import (
    WhoIsIAmServices, WhoHasIHaveServices,
    DeviceCommunicationControlServices,
    )

from .helpers import ApplicationNetwork, SnifferNode

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestBasic(unittest.TestCase):

    def test_basic(self):
        """Test basic configuration of a network."""
        if _debug: TestBasic._debug("test_basic")

        # create a network
        anet = ApplicationNetwork()

        # all start states are successful
        anet.td.start_state.success()
        anet.iut.start_state.success()

        # run the group
        anet.run()


@bacpypes_debugging
class TestWhoIsIAm(unittest.TestCase):

    def test_whois_unconstrained(self):
        """Test an unconstrained WhoIs, all devices respond."""
        if _debug: TestWhoIsIAm._debug("test_whois_unconstrained")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)

        # all start states are successful
        anet.td.start_state.doc("1-1-0") \
            .send(WhoIsRequest(destination=anet.vlan.broadcast_address)).doc("1-1-1") \
            .receive(IAmRequest, pduSource=anet.iut.address).doc("1-1-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_whois_range_below(self):
        """Test range below."""
        if _debug: TestWhoIsIAm._debug("test_whois_range_below")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the iut
        anet.iut.add_capability(WhoIsIAmServices)

        # all start states are successful
        anet.td.start_state.doc("2-1-0") \
            .send(WhoIsRequest(
                destination=anet.vlan.broadcast_address,
                deviceInstanceRangeLowLimit=0,
                deviceInstanceRangeHighLimit=9,
                )).doc("2-1-1") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_whois_range_above(self):
        """Test range above."""
        if _debug: TestWhoIsIAm._debug("test_whois_range_above")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the iut
        anet.iut.add_capability(WhoIsIAmServices)

        # all start states are successful
        anet.td.start_state.doc("3-1-0") \
            .send(WhoIsRequest(
                destination=anet.vlan.broadcast_address,
                deviceInstanceRangeLowLimit=21,
                deviceInstanceRangeHighLimit=29,
                )).doc("3-1-1") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_whois_range(self):
        """Test a WhoIs, included range."""
        if _debug: TestWhoIsIAm._debug("test_whois_range")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)

        # all start states are successful
        anet.td.start_state.doc("4-1-0") \
            .send(WhoIsRequest(
                destination=anet.vlan.broadcast_address,
                deviceInstanceRangeLowLimit=19,
                deviceInstanceRangeHighLimit=21,
                )).doc("4-1-1") \
            .receive(IAmRequest, pduSource=anet.iut.address).doc("4-1-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()


@bacpypes_debugging
class TestWhoHasIHave(unittest.TestCase):

    def test_who_has_object_by_name(self):
        """Test an unconstrained WhoIs, all devices respond."""
        if _debug: TestWhoIsIAm._debug("test_who_has_object_by_name")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoHasIHaveServices)

        # all start states are successful
        anet.td.start_state.doc("5-1-0") \
            .send(WhoHasRequest(
                destination=anet.vlan.broadcast_address,
                object=WhoHasObject(objectName="iut"),
                )).doc("5-1-1") \
            .receive(IHaveRequest, pduSource=anet.iut.address).doc("5-1-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_who_has_object_by_id(self):
        """Test an unconstrained WhoIs, all devices respond."""
        if _debug: TestWhoIsIAm._debug("test_who_has_object_by_id")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoHasIHaveServices)

        # all start states are successful
        anet.td.start_state.doc("6-1-0") \
            .send(WhoHasRequest(
                destination=anet.vlan.broadcast_address,
                object=WhoHasObject(objectIdentifier=('device', 20)),
                )).doc("6-1-1") \
            .receive(IHaveRequest, pduSource=anet.iut.address).doc("6-1-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

@bacpypes_debugging
class TestDeviceCommunicationControl(unittest.TestCase):

    def test_default_behavior(self):
        """Test."""
        if _debug: TestDeviceCommunicationControl._debug("test_default_behavior")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # test sequence
        anet.td.start_state.doc("7-1-0") \
            .send(WhoIsRequest(destination=anet.vlan.broadcast_address)).doc("7-1-1") \
            .receive(IAmRequest, pduSource=anet.iut.address).doc("7-1-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_disable(self):
        """Test."""
        if _debug: TestDeviceCommunicationControl._debug("test_disable")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # test sequence
        anet.td.start_state.doc("7-2-0") \
            .send(DeviceCommunicationControlRequest(
                destination=anet.iut.address,
                enableDisable='disable',
                )).doc("7-2-1") \
            .receive(SimpleAckPDU).doc("7-2-2") \
            .send(WhoIsRequest(destination=anet.vlan.broadcast_address)).doc("7-2-3") \
            .timeout(10).doc("7-2-4") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_disable_initiation(self):
        """Test disabling initiation.  After the DCC request send the IUT
        a WhoIsRequest and verify that the IAmRequest makes it back.
        """
        if _debug: TestDeviceCommunicationControl._debug("test_disable")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # test sequence
        anet.td.start_state.doc("7-3-0") \
            .send(DeviceCommunicationControlRequest(
                destination=anet.iut.address,
                enableDisable='disableInitiation',
                )).doc("7-3-1") \
            .receive(SimpleAckPDU).doc("7-3-2") \
            .send(WhoIsRequest(destination=anet.vlan.broadcast_address)).doc("7-3-3") \
            .receive(IAmRequest, pduSource=anet.iut.address).doc("7-3-4") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_disable_time_duration(self):
        """Test disabling communication for a specific amount of time in
        minutes.  After turning off communications, wait for 30 seconds and
        send a request and nothing should come back.  Wait an additional 30
        seconds and try again, this time receiving the response."""
        if _debug: TestDeviceCommunicationControl._debug("test_disable_time_duration")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # test sequence
        anet.td.start_state.doc("7-4-0") \
            .send(DeviceCommunicationControlRequest(
                destination=anet.iut.address,
                enableDisable='disable',
                timeDuration=1,
                )).doc("7-4-1") \
            .receive(SimpleAckPDU).doc("7-4-2") \
            .timeout(30).doc("7-4-3") \
            .send(WhoIsRequest(
                destination=anet.vlan.broadcast_address,
                )).doc("7-4-4") \
            .timeout(30.1).doc("7-4-5") \
            .send(WhoIsRequest(
                destination=anet.vlan.broadcast_address,
                )).doc("7-4-6") \
            .receive(IAmRequest, pduSource=anet.iut.address).doc("7-4-7") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group a little longer than a minute
        anet.run(61)

    def test_correct_password(self):
        """Test disabling communication that requires a password."""
        if _debug: TestDeviceCommunicationControl._debug("test_correct_password")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # set the password
        anet.iut_device_object._dcc_password = "xyzzy"

        # test sequence
        anet.td.start_state.doc("7-5-0") \
            .send(DeviceCommunicationControlRequest(
                destination=anet.iut.address,
                timeDuration=1,
                enableDisable='disable',
                password="xyzzy",
                )).doc("7-5-1") \
            .receive(SimpleAckPDU).doc("7-5-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

    def test_incorrect_password(self):
        """Test disabling communication that requires a password."""
        if _debug: TestDeviceCommunicationControl._debug("test_incorrect_password")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # set the password
        anet.iut_device_object._dcc_password = "xyzzy"

        # test sequence
        anet.td.start_state.doc("7-6-0") \
            .send(DeviceCommunicationControlRequest(
                destination=anet.iut.address,
                timeDuration=1,
                enableDisable='disable',
                password="plugh",
                )).doc("7-6-1") \
            .receive(Error,
                errorClass='security',
                errorCode='passwordFailure',
                ).doc("7-6-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()


@bacpypes_debugging
class TestUnrecognizedService(unittest.TestCase):

    class ReadPropertyConditionalRequest(ConfirmedRequestSequence):
        serviceChoice = 13
        sequenceElements = [
            # Element('objectSelectionCriteria', ObjectSelectionCriteria, 1),
            Element('listOfPropertyReferences', SequenceOf(PropertyReference), 1),
            ]

    def test_9_39_1(self):
        """9.39.1 Unsupported Confirmed Services Test"""
        if _debug: TestUnrecognizedService._debug("test_9_39_1")

        # create a network
        anet = ApplicationNetwork()

        # send the request, get it rejected
        anet.td.start_state.doc("7-6-0") \
            .send(TestUnrecognizedService.ReadPropertyConditionalRequest(
                destination=anet.iut.address,
                listOfPropertyReferences=[],
                )).doc("7-6-1") \
            .receive(RejectPDU, pduSource=anet.iut.address, apduAbortRejectReason=9).doc("7-6-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()


@bacpypes_debugging
class TestAPDURetryTimeout(unittest.TestCase):

    def test_apdu_retry_default(self):
        """Confirmed Request - No Reply"""
        if _debug: TestAPDURetryTimeout._debug("test_apdu_retry")

        # create a network
        anet = ApplicationNetwork()

        # adjust test if default retries changes
        assert anet.iut_device_object.numberOfApduRetries == 3

        # add a sniffer to see requests without doing anything
        sniffer = SnifferNode(anet.vlan)
        anet.append(sniffer)

        # no TD application layer matching
        anet.td.start_state.success()

        # send a request to a non-existent device, get it rejected
        anet.iut.start_state.doc("7-7-0") \
            .send(ReadPropertyRequest(
                objectIdentifier=('analogValue', 1),
                propertyIdentifier='presentValue',
                destination=Address(99),
                )).doc("7-7-1") \
            .receive(AbortPDU, apduAbortRejectReason=65).doc("7-7-2") \
            .success()

        # see the attempts and nothing else
        sniffer.start_state.doc("7-8-0") \
            .receive(PDU).doc("7-8-1") \
            .receive(PDU).doc("7-8-2") \
            .receive(PDU).doc("7-8-3") \
            .receive(PDU).doc("7-8-4") \
            .timeout(10).doc("7-8-5") \
            .success()

        # run the group
        anet.run()

    def test_apdu_retry_1(self):
        """Confirmed Request - No Reply"""
        if _debug: TestAPDURetryTimeout._debug("test_apdu_retry_1")

        # create a network
        anet = ApplicationNetwork()

        # change the retry count in the device properties
        anet.iut_device_object.numberOfApduRetries = 1

        # add a sniffer to see requests without doing anything
        sniffer = SnifferNode(anet.vlan)
        anet.append(sniffer)

        # no TD application layer matching
        anet.td.start_state.success()

        # send a request to a non-existent device, get it rejected
        anet.iut.start_state.doc("7-9-0") \
            .send(ReadPropertyRequest(
                objectIdentifier=('analogValue', 1),
                propertyIdentifier='presentValue',
                destination=Address(99),
                )).doc("7-9-1") \
            .receive(AbortPDU, apduAbortRejectReason=65).doc("7-9-2") \
            .success()

        # see the attempts and nothing else
        sniffer.start_state.doc("7-10-0") \
            .receive(PDU).doc("7-10-1") \
            .receive(PDU).doc("7-10-2") \
            .timeout(10).doc("7-10-3") \
            .success()

        # run the group
        anet.run()

