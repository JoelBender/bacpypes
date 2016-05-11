#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities Trapped Services
-------------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import ServiceAccessPoint, ApplicationServiceElement, bind

from ..trapped_classes import TrappedServiceAccessPoint, \
    TrappedApplicationServiceElement

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class EchoAccessPoint(ServiceAccessPoint):

    def sap_indication(self, pdu):
        if _debug: EchoAccessPoint._debug("sap_indication %r", pdu)
        self.sap_response(pdu)

    def sap_confirmation(self, pdu):
        if _debug: EchoAccessPoint._debug("sap_confirmation %r", pdu)
        pass


class TrappedEchoAccessPoint(TrappedServiceAccessPoint, EchoAccessPoint):
    pass


@bacpypes_debugging
class EchoServiceElement(ApplicationServiceElement):

    def indication(self, pdu):
        if _debug: EchoServiceElement._debug("indication %r", pdu)
        self.response(pdu)

    def confirmation(self, pdu):
        if _debug: EchoServiceElement._debug("confirmation %r", pdu)
        pass


class TrappedEchoServiceElement(TrappedApplicationServiceElement, EchoServiceElement):
    pass


@bacpypes_debugging
def setup_module():
    if _debug: setup_module._debug("setup_module")

    # verify the echo access point is trapped correctly
    assert TrappedEchoAccessPoint.__mro__ == (
        TrappedEchoAccessPoint,
        TrappedServiceAccessPoint,
        EchoAccessPoint,
        ServiceAccessPoint,
        object,
        )

    # verify the echo service element is trapped correctly
    assert TrappedEchoServiceElement.__mro__ == (
        TrappedEchoServiceElement,
        TrappedApplicationServiceElement,
        EchoServiceElement,
        ApplicationServiceElement,
        object,
        )


@bacpypes_debugging
class TestApplicationService(unittest.TestCase):

    def test_application_service(self):
        if _debug: TestApplicationService._debug("test_application_service")

        # create an access point and a service element and bind them together
        sap = TrappedEchoAccessPoint()
        ase = TrappedEchoServiceElement()
        bind(ase, sap)

        # make pdu object
        pdu = object()

        # service access point is going to request something
        sap.sap_request(pdu)

        # make sure the request was sent and received
        assert sap.sap_request_sent is pdu
        assert ase.indication_received is pdu

        # make sure the echo response was sent and received
        assert ase.response_sent is pdu
        assert sap.sap_confirmation_received is pdu

        # make another pdu object
        pdu = object()

        # service element is going to request something
        ase.request(pdu)

        # make sure the request was sent and received
        assert ase.request_sent is pdu
        assert sap.sap_indication_received is pdu

        # make sure the echo response was sent and received
        assert sap.sap_response_sent is pdu
        assert ase.confirmation_received is pdu
