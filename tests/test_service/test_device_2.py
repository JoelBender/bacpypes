#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test APDU Decoding
------------------
"""

import sys
import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.comm import bind
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, LocalBroadcast
from bacpypes.primitivedata import OpeningTag
from bacpypes.constructeddata import Any
from bacpypes.apdu import (
    APDU,
    ReadPropertyRequest,
    ReadPropertyACK,
    Error,
)

from bacpypes.vlan import Network, Node

from bacpypes.app import ApplicationIOController
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.local.device import LocalDeviceObject

from ..state_machine import (
    StateMachine,
    StateMachineGroup,
    ClientStateMachine,
    TrafficLog,
)
from ..time_machine import reset_time_machine, run_time_machine


# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class ApplicationNetwork(StateMachineGroup):
    def __init__(self, test_name):
        if _debug:
            ApplicationNetwork._debug("__init__ %r", test_name)
        StateMachineGroup.__init__(self)

        # reset the time machine
        reset_time_machine()
        if _debug:
            ApplicationNetwork._debug("    - time machine reset")

        # create a traffic log
        self.traffic_log = TrafficLog()

        # make a little LAN
        self.vlan = Network(broadcast_address=LocalBroadcast())
        self.vlan.traffic_log = self.traffic_log

        # test device object
        self.td_device_object = LocalDeviceObject(
            objectName="td",
            objectIdentifier=("device", 10),
            maxApduLengthAccepted=1024,
            segmentationSupported="noSegmentation",
            vendorIdentifier=999,
        )

        # test device
        self.td = ApplicationStateMachine(self.td_device_object, self.vlan)
        self.append(self.td)

        # error device generates bad packets
        self.ed = ApplicationLayerStateMachine(20, self.vlan)
        self.append(self.ed)

    def run(self, time_limit=60.0):
        if _debug:
            ApplicationNetwork._debug("run %r", time_limit)

        # run the group
        super(ApplicationNetwork, self).run()
        if _debug:
            ApplicationNetwork._debug("    - group running")

        # run it for some time
        run_time_machine(time_limit)
        if _debug:
            ApplicationNetwork._debug("    - time machine finished")
            for state_machine in self.state_machines:
                ApplicationNetwork._debug("    - machine: %r", state_machine)
                for direction, pdu in state_machine.transaction_log:
                    ApplicationNetwork._debug("        %s %s", direction, str(pdu))

            # traffic log has what was processed on each vlan
            self.traffic_log.dump(ApplicationNetwork._debug)

        # check for success
        all_success, some_failed = super(ApplicationNetwork, self).check_for_success()
        ApplicationNetwork._debug(
            "    - all_success, some_failed: %r, %r", all_success, some_failed
        )
        assert all_success


class _NetworkServiceElement(NetworkServiceElement):
    """
    This class turns off the deferred startup function call that broadcasts
    I-Am-Router-To-Network and Network-Number-Is messages.
    """

    _startup_disabled = True


@bacpypes_debugging
class ApplicationStateMachine(ApplicationIOController, StateMachine):
    def __init__(self, localDevice, vlan):
        if _debug:
            ApplicationStateMachine._debug("__init__ %r %r", localDevice, vlan)

        # build an address and save it
        self.address = Address(localDevice.objectIdentifier[1])
        if _debug:
            ApplicationStateMachine._debug("    - address: %r", self.address)

        # continue with initialization
        ApplicationIOController.__init__(self, localDevice)
        StateMachine.__init__(self, name=localDevice.objectName)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = _NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a node, added to the network
        self.node = Node(self.address, vlan)

        # bind the network service to the node, no network number
        self.nsap.bind(self.node)

    def send(self, apdu):
        if _debug:
            ApplicationStateMachine._debug("send(%s) %r", self.name, apdu)

        # build an IOCB to wrap the request
        iocb = IOCB(apdu)
        self.request_io(iocb)

    def indication(self, apdu):
        if _debug:
            ApplicationStateMachine._debug("indication(%s) %r", self.name, apdu)

        # let the state machine know the request was received
        self.receive(apdu)

        # allow the application to process it
        super(ApplicationStateMachine, self).indication(apdu)

    def confirmation(self, apdu):
        if _debug:
            ApplicationStateMachine._debug("confirmation(%s) %r", self.name, apdu)

        # forward the confirmation to the state machine
        self.receive(apdu)

        # allow the application to process it
        super(ApplicationStateMachine, self).confirmation(apdu)


@bacpypes_debugging
class ApplicationLayerStateMachine(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug:
            ApplicationLayerStateMachine._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # build a name, save the address
        self.name = "app @ %s" % (address,)
        self.address = Address(address)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()
        if _debug:
            ApplicationLayerStateMachine._debug("    - nsap: %r", self.nsap)

        # bind this as a client of the network service access point
        bind(self, self.nsap)

        # create a node, added to the network
        self.node = Node(self.address, vlan)
        if _debug:
            ApplicationLayerStateMachine._debug("    - node: %r", self.node)

        # bind the stack to the local network
        self.nsap.bind(self.node)


@bacpypes_debugging
class TestAPDUDecodingError(unittest.TestCase):
    def test_apdu_bad_reply(self):
        """Confirmed Request - Bad Reply"""
        if _debug:
            TestAPDUDecodingError._debug("test_apdu_bad_reply")

        # create a network
        anet = ApplicationNetwork("test_apdu_bad_reply")

        # make a bad value
        a = Any()
        a.tagList.append(OpeningTag(1))

        # create a bad APDU to send back
        bad_apdu = ReadPropertyACK(
            objectIdentifier=("analogValue", 1),
            propertyIdentifier="presentValue",
            propertyValue=a,
        )
        bad_apdu.pduDestination = anet.td.address
        bad_apdu.apduInvokeID = 1

        # send a request to a non-existent device, get it rejected
        anet.td.start_state.doc("8-1-0") \
            .send(
                ReadPropertyRequest(
                    objectIdentifier=("analogValue", 1),
                    propertyIdentifier="presentValue",
                    destination=anet.ed.address,
                )).doc("8-1-1") \
            .receive(
                Error,
                errorClass=7,  # communication
                errorCode=57,  # invalidTag
                ).doc("8-1-2") \
            .success()

        # error device sends back a badly encoded response
        anet.ed.start_state.doc("8-2-0") \
            .receive(APDU).doc("8-2-1") \
            .send(bad_apdu).doc("8-2-2") \
            .success()

        # run the group
        anet.run()
