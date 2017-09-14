#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device Services
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.pdu import Address, LocalBroadcast, PDU
from bacpypes.apdu import (
    WhoIsRequest, IAmRequest,
    WhoHasRequest, WhoHasLimits, WhoHasObject, IHaveRequest,
    DeviceCommunicationControlRequest,
    )

from bacpypes.service.device import (
    WhoIsIAmServices, WhoHasIHaveServices,
    DeviceCommunicationControlServices,
    )

from .helpers import ApplicationNetwork, ApplicationNode

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

    def test_01(self):
        """Test an unconstrained WhoIs, all devices respond."""
        if _debug: TestDeviceCommunicationControl._debug("test_01")

        # create a network
        anet = ApplicationNetwork()

        # add the service capability to the IUT
        anet.iut.add_capability(WhoIsIAmServices)
        anet.iut.add_capability(DeviceCommunicationControlServices)

        # all start states are successful
        anet.td.start_state.doc("7-1-0") \
            .send(WhoIsRequest(destination=anet.vlan.broadcast_address)).doc("7-1-1") \
            .receive(IAmRequest, pduSource=anet.iut.address).doc("7-1-2") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

