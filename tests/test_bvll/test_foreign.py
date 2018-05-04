#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test BVLL Foreign Devices
-------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.pdu import Address, PDU, LocalBroadcast
from bacpypes.vlan import IPNetwork, IPRouter
from bacpypes.bvll import (
    Result, RegisterForeignDevice,
    ReadForeignDeviceTable, ReadForeignDeviceTableAck,
    DistributeBroadcastToNetwork, ForwardedNPDU,
    OriginalUnicastNPDU, OriginalBroadcastNPDU,
    )

from ..state_machine import StateMachineGroup, TrafficLog
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import (
    SnifferStateMachine, BIPStateMachine,
    BIPSimpleStateMachine, BIPForeignStateMachine, BIPBBMDStateMachine,
    )

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

        # create a traffic log
        self.traffic_log = TrafficLog()

        # make a router
        self.router = IPRouter()

        # make a home LAN
        self.vlan_5 = IPNetwork("192.168.5.0/24")
        self.vlan_5.traffic_log = self.traffic_log
        self.router.add_network(Address("192.168.5.1/24"), self.vlan_5)

        # make a remote LAN
        self.vlan_6 = IPNetwork("192.168.6.0/24")
        self.vlan_6.traffic_log = self.traffic_log
        self.router.add_network(Address("192.168.6.1/24"), self.vlan_6)

        # the foreign device
        self.fd = BIPForeignStateMachine("192.168.6.2/24", self.vlan_6)
        self.append(self.fd)

        # bbmd
        self.bbmd = BIPBBMDStateMachine("192.168.5.3/24", self.vlan_5)
        self.append(self.bbmd)

    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)

        # run the group
        super(TNetwork, self).run()

        # run it for some time
        run_time_machine(time_limit)
        if _debug: TNetwork._debug("    - time machine finished")

        # check for success
        all_success, some_failed = super(TNetwork, self).check_for_success()

        if _debug:
            TNetwork._debug("    - all_success, some_failed: %r, %r", all_success, some_failed)
            for state_machine in self.state_machines:
                if state_machine.running:
                    TNetwork._debug("    %r (running)", state_machine)
                elif not state_machine.current_state:
                    TNetwork._debug("    %r (not started)", state_machine)
                else:
                    TNetwork._debug("    %r", state_machine)
                for direction, pdu in state_machine.transaction_log:
                    TNetwork._debug("        %s %s", direction, str(pdu))

            # traffic log has what was processed on each vlan
            self.traffic_log.dump(TNetwork._debug)

        assert all_success


@bacpypes_debugging
class TestForeign(unittest.TestCase):

    def test_idle(self):
        """Test an idle network, nothing happens is success."""
        if _debug: TestForeign._debug("test_idle")

        # create a network
        tnet = TNetwork()

        # all start states are successful
        tnet.fd.start_state.success()
        tnet.bbmd.start_state.success()

        # run the group
        tnet.run()

    def test_registration(self):
        """Test foreign device registration."""
        if _debug: TestForeign._debug("test_registration")

        # create a network
        tnet = TNetwork()

        # tell the B/IP layer of the foreign device to register
        tnet.fd.start_state \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 30) \
            .success()

        # remote sniffer node
        remote_sniffer = SnifferStateMachine("192.168.6.254/24", tnet.vlan_6)
        tnet.append(remote_sniffer)

        # sniffer traffic
        remote_sniffer.start_state.doc("1-1-0") \
            .receive(RegisterForeignDevice).doc("1-1-1") \
            .receive(Result).doc("1-1-2") \
            .set_event('fd-registered').doc("1-1-3") \
            .success()

        # the bbmd is idle
        tnet.bbmd.start_state.success()

        # home snooper node
        home_snooper = BIPStateMachine("192.168.5.2/24", tnet.vlan_5)
        tnet.append(home_snooper)

        # snooper will read the foreign device table
        home_snooper.start_state.doc("1-2-0") \
            .wait_event('fd-registered').doc("1-2-1") \
            .send(ReadForeignDeviceTable(destination=tnet.bbmd.address)).doc("1-2-2") \
            .receive(ReadForeignDeviceTableAck).doc("1-2-3") \
            .success()

        # home sniffer node
        home_sniffer = SnifferStateMachine("192.168.5.254/24", tnet.vlan_5)
        tnet.append(home_sniffer)

        # sniffer traffic
        home_sniffer.start_state.doc("1-3-0") \
            .receive(RegisterForeignDevice).doc("1-3-1") \
            .receive(Result).doc("1-3-2") \
            .receive(ReadForeignDeviceTable).doc("1-3-3") \
            .receive(ReadForeignDeviceTableAck).doc("1-3-4") \
            .success()

        # run the group
        tnet.run()

    def test_refresh_registration(self):
        """Test refreshing foreign device registration."""
        if _debug: TestForeign._debug("test_refresh_registration")

        # create a network
        tnet = TNetwork()

        # tell the B/IP layer of the foreign device to register
        tnet.fd.start_state \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 10) \
            .success()

        # the bbmd is idle
        tnet.bbmd.start_state.success()

        # remote sniffer node
        remote_sniffer = SnifferStateMachine("192.168.6.254/24", tnet.vlan_6)
        tnet.append(remote_sniffer)

        # sniffer traffic
        remote_sniffer.start_state.doc("2-1-0") \
            .receive(RegisterForeignDevice).doc("2-1-1") \
            .receive(Result).doc("2-1-2") \
            .receive(RegisterForeignDevice).doc("2-1-3") \
            .receive(Result).doc("2-1-4") \
            .success()

        # run the group
        tnet.run()

    def test_unicast(self):
        """Test a unicast message from the foreign device to the bbmd."""
        if _debug: TestForeign._debug("test_unicast")

        # create a network
        tnet = TNetwork()

        # make a PDU from node 1 to node 2
        pdu_data = xtob('dead.beef')
        pdu = PDU(pdu_data, source=tnet.fd.address, destination=tnet.bbmd.address)
        if _debug: TestForeign._debug("    - pdu: %r", pdu)

        # register, wait for ack, send some beef
        tnet.fd.start_state.doc("3-1-0") \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 60).doc("3-1-1") \
            .wait_event('3-registered').doc("3-1-2") \
            .send(pdu).doc("3-1-3") \
            .success()

        # the bbmd is happy when it gets the pdu
        tnet.bbmd.start_state \
            .receive(PDU, pduSource=tnet.fd.address, pduData=pdu_data) \
            .success()

        # remote sniffer node
        remote_sniffer = SnifferStateMachine("192.168.6.254/24", tnet.vlan_6)
        tnet.append(remote_sniffer)

        # sniffer traffic
        remote_sniffer.start_state.doc("3-2-0") \
            .receive(RegisterForeignDevice).doc("3-2-1") \
            .receive(Result).doc("3-2-2") \
            .set_event('3-registered').doc("3-2-3") \
            .receive(OriginalUnicastNPDU).doc("3-2-4") \
            .success()

        # run the group
        tnet.run()

    def test_broadcast(self):
        """Test a broadcast message from the foreign device to the bbmd."""
        if _debug: TestForeign._debug("test_broadcast")

        # create a network
        tnet = TNetwork()

        # make a broadcast pdu
        pdu_data = xtob('dead.beef')
        pdu = PDU(pdu_data, destination=LocalBroadcast())
        if _debug: TestForeign._debug("    - pdu: %r", pdu)

        # register, wait for ack, send some beef
        tnet.fd.start_state.doc("4-1-0") \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 60).doc("4-1-1") \
            .wait_event('4-registered').doc("4-1-2") \
            .send(pdu).doc("4-1-3") \
            .success()

        # the bbmd is happy when it gets the pdu
        tnet.bbmd.start_state.doc("4-2-0") \
            .receive(PDU, pduSource=tnet.fd.address, pduData=pdu_data).doc("4-2-1") \
            .success()

        # home simple node
        home_node = BIPSimpleStateMachine("192.168.5.254/24", tnet.vlan_5)
        tnet.append(home_node)

        # home node happy when getting the pdu, broadcast by the bbmd
        home_node.start_state.doc("4-3-0") \
            .receive(PDU, pduSource=tnet.fd.address, pduData=pdu_data).doc("4-3-1") \
            .success()

        # remote sniffer node
        remote_sniffer = SnifferStateMachine("192.168.6.254/24", tnet.vlan_6)
        tnet.append(remote_sniffer)

        # remote traffic
        remote_sniffer.start_state.doc("4-4-0") \
            .receive(RegisterForeignDevice).doc("4-4-1") \
            .receive(Result).doc("4-4-2") \
            .set_event('4-registered') \
            .receive(DistributeBroadcastToNetwork).doc("4-4-3") \
            .success()

        # run the group
        tnet.run(4.0)

