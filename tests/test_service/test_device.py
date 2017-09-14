#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device Services
--------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.pdu import Address, LocalBroadcast, PDU
from bacpypes.apdu import WhoIsRequest, IAmRequest

from bacpypes.vlan import Network
from bacpypes.service.device import LocalDeviceObject, WhoIsIAmServices

from ..state_machine import match_pdu, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import SnifferNode, ApplicationNode

# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   TNetwork
#

@bacpypes_debugging
class TNetwork(StateMachineGroup):

    def __init__(self):
        if _debug: TNetwork._debug("__init__")
        StateMachineGroup.__init__(self)

        # reset the time machine
        reset_time_machine()
        if _debug: TNetwork._debug("    - time machine reset")

        # make a little LAN
        self.vlan = Network(broadcast_address=LocalBroadcast())

        # test device object
        td_device_object = LocalDeviceObject(
            objectName="td",
            objectIdentifier=("device", 1),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=999,
            )

        # test device
        self.td = ApplicationNode(td_device_object, Address(1), self.vlan)
        self.append(self.td)

        # implementation under test device object
        iut_device_object = LocalDeviceObject(
            objectName="iut",
            objectIdentifier=("device", 2),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=999,
            )

        # implementation under test
        self.iut = ApplicationNode(iut_device_object, Address(2), self.vlan)
        self.append(self.iut)

        # sniffer node
        self.sniffer = SnifferNode(Address(3), self.vlan)
        self.append(self.sniffer)


    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)

        # run the group
        super(TNetwork, self).run()
        if _debug: TNetwork._debug("    - group running")

        # run it for some time
        run_time_machine(time_limit)
        if _debug:
            TNetwork._debug("    - time machine finished")
            for state_machine in self.state_machines:
                TNetwork._debug("    - machine: %r", state_machine)
                for direction, pdu in state_machine.transaction_log:
                    TNetwork._debug("        %s %s", direction, str(pdu))

        # check for success
        all_success, some_failed = super(TNetwork, self).check_for_success()
        assert all_success


@bacpypes_debugging
class TestBasic(unittest.TestCase):

    def test_basic(self):
        """Test basic configuration of a network."""
        if _debug: TestBasic._debug("test_basic")

        # create a network
        tnet = TNetwork()

        # all start states are successful
        tnet.td.start_state.success()
        tnet.iut.start_state.success()
        tnet.sniffer.start_state.success()

        # run the group
        tnet.run()

@bacpypes_debugging
class TestWhoIsIAm(unittest.TestCase):

    def test_whois(self):
        """Test an idle network, nothing happens is success."""
        if _debug: TestWhoIsIAm._debug("test_whois")

        # create a network
        tnet = TNetwork()

        # add the service capability to the iut
        tnet.iut.add_capability(WhoIsIAmServices)

        # all start states are successful
        tnet.td.start_state.doc("1-1-0") \
            .send(WhoIsRequest(destination=tnet.vlan.broadcast_address)).doc("1-1-1") \
            .receive(IAmRequest, pduSource=tnet.iut.address).doc("1-1-2") \
            .success()

        # application layer above the iut is idle
        tnet.iut.start_state.success()

        # no sniffing yet
        tnet.sniffer.start_state.success()

        # run the group
        tnet.run()

