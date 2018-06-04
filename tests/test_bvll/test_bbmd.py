#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test BBMD
---------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.pdu import Address, PDU, LocalBroadcast
from bacpypes.vlan import IPNetwork, IPRouter
from bacpypes.bvll import (
    Result,
    WriteBroadcastDistributionTable,
    ReadBroadcastDistributionTable, ReadBroadcastDistributionTableAck,
    ForwardedNPDU,
    RegisterForeignDevice,
    ReadForeignDeviceTable, ReadForeignDeviceTableAck,
    DeleteForeignDeviceTableEntry,
    DistributeBroadcastToNetwork,
    OriginalUnicastNPDU,
    OriginalBroadcastNPDU,
    )

from bacpypes.apdu import (
    WhoIsRequest, IAmRequest,
    ReadPropertyRequest, ReadPropertyACK,
    AbortPDU,
    )

from ..state_machine import StateMachineGroup, TrafficLog
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import (
    SnifferStateMachine, BIPStateMachine, BIPSimpleStateMachine,
    BIPForeignStateMachine, BIPBBMDStateMachine,
    BIPSimpleNode, BIPBBMDNode,
    BIPSimpleApplicationLayerStateMachine,
    BIPBBMDApplication,
    )

# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   TNetwork
#

@bacpypes_debugging
class TNetwork(StateMachineGroup):

    def __init__(self, count):
        if _debug: TNetwork._debug("__init__ %r", count)
        StateMachineGroup.__init__(self)

        # reset the time machine
        reset_time_machine()
        if _debug: TNetwork._debug("    - time machine reset")

        # create a traffic log
        self.traffic_log = TrafficLog()

        # make a router
        self.router = IPRouter()

        # make the networks
        self.vlan = []
        for net in range(1, count + 1):
            # make a network and set the traffic log
            ip_network = IPNetwork("192.168.{}.0/24".format(net))
            ip_network.traffic_log = self.traffic_log

            # make a router
            router_address = Address("192.168.{}.1/24".format(net))
            self.router.add_network(router_address, ip_network)

            self.vlan.append(ip_network)

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
                    TNetwork._debug("        %s %r", direction, pdu)

            # traffic log has what was processed on each vlan
            self.traffic_log.dump(TNetwork._debug)

        assert all_success


@bacpypes_debugging
class TestNonBBMD(unittest.TestCase):

    def setup_method(self, method):
        """This function is called before each test method is called and is
        given a reference to the test method."""
        if _debug: TestNonBBMD._debug("setup_method %r", method)

        # create a network
        self.tnet = TNetwork(1)

        # test device
        self.td = BIPStateMachine("192.168.1.2/24", self.tnet.vlan[0])
        self.tnet.append(self.td)

        # implementation under test
        self.iut = BIPSimpleNode("192.168.1.3/24", self.tnet.vlan[0])

    def test_write_bdt_fail(self):
        """Test writing a BDT."""
        if _debug: TestNonBBMD._debug("test_write_bdt_fail")

        # read the broadcast distribution table, get a nack
        self.td.start_state.doc("1-1-0") \
            .send(WriteBroadcastDistributionTable(destination=self.iut.address)).doc("1-1-1") \
            .receive(Result, bvlciResultCode=0x0010).doc("1-1-2") \
            .success()

        # run the group
        self.tnet.run()

    def test_read_bdt_fail(self):
        """Test reading a BDT."""
        if _debug: TestNonBBMD._debug("test_read_bdt_fail")

        # read the broadcast distribution table, get a nack
        self.td.start_state.doc("1-2-0") \
            .send(ReadBroadcastDistributionTable(destination=self.iut.address)).doc("1-2-1") \
            .receive(Result, bvlciResultCode=0x0020).doc("1-2-2") \
            .success()

        # run the group
        self.tnet.run()

    def test_register_fail(self):
        """Test registering as a foreign device to a non-BBMD."""
        if _debug: TestNonBBMD._debug("test_read_fdt_success")

        # read the broadcast distribution table, get a nack
        self.td.start_state.doc("1-3-0") \
            .send(RegisterForeignDevice(10, destination=self.iut.address)).doc("1-3-1") \
            .receive(Result, bvlciResultCode=0x0030).doc("1-3-2") \
            .success()

        # run the group
        self.tnet.run()

    def test_read_fdt_fail(self):
        """Test reading an FDT from a non-BBMD."""
        if _debug: TestNonBBMD._debug("test_read_fdt_success")

        # read the broadcast distribution table, get a nack
        self.td.start_state.doc("1-4-0") \
            .send(ReadForeignDeviceTable(destination=self.iut.address)).doc("1-4-1") \
            .receive(Result, bvlciResultCode=0x0040).doc("1-4-2") \
            .success()

        # run the group
        self.tnet.run()

    def test_delete_fail(self):
        """Test deleting an FDT entry from a non-BBMD."""
        if _debug: TestNonBBMD._debug("test_delete_fail")

        # read the broadcast distribution table, get a nack
        self.td.start_state.doc("1-5-0") \
            .send(DeleteForeignDeviceTableEntry(Address("1.2.3.4"), destination=self.iut.address)).doc("1-5-1") \
            .receive(Result, bvlciResultCode=0x0050).doc("1-5-2") \
            .success()

        # run the group
        self.tnet.run()

    def test_distribute_fail(self):
        """Test asking a non-BBMD to distribute a broadcast."""
        if _debug: TestNonBBMD._debug("test_delete_fail")

        # read the broadcast distribution table, get a nack
        self.td.start_state.doc("1-6-0") \
            .send(DistributeBroadcastToNetwork(xtob('deadbeef'), destination=self.iut.address)).doc("1-6-1") \
            .receive(Result, bvlciResultCode=0x0060).doc("1-6-2") \
            .success()

        # run the group
        self.tnet.run()


@bacpypes_debugging
class TestBBMD(unittest.TestCase):

    def test_14_2_1_1(self):
        """14.2.1.1 Execute Forwarded-NPDU (One-hop Distribution)."""
        if _debug: TestBBMD._debug("test_14_2_1_1")

        # create a network
        tnet = TNetwork(2)

        # implementation under test
        iut = BIPBBMDApplication("192.168.1.2/24", tnet.vlan[0])
        if _debug: TestBBMD._debug("    - iut.bip: %r", iut.bip)

        # BBMD on net 2
        bbmd1 = BIPBBMDNode("192.168.2.2/24", tnet.vlan[1])

        # add the IUT as a one-hop peer
        bbmd1.bip.add_peer(Address("192.168.1.2/24"))
        if _debug: TestBBMD._debug("    - bbmd1.bip: %r", bbmd1.bip)

        # test device
        td = BIPSimpleApplicationLayerStateMachine("192.168.2.3/24", tnet.vlan[1])
        tnet.append(td)

        # listener looks for extra traffic
        listener = BIPStateMachine("192.168.1.3/24", tnet.vlan[0])
        listener.mux.node.promiscuous = True
        tnet.append(listener)

        # broadcast a forwarded NPDU
        td.start_state.doc("2-1-0") \
            .send(WhoIsRequest(destination=LocalBroadcast())).doc("2-1-1") \
            .receive(IAmRequest).doc("2-1-2") \
            .success()

        # listen for the directed broadcast, then the original unicast,
        # then fail if there's anything else
        listener.start_state.doc("2-2-0") \
            .receive(ForwardedNPDU).doc("2-2-1") \
            .receive(OriginalUnicastNPDU).doc("2-2-2") \
            .timeout(3).doc("2-2-3") \
            .success()

        # run the group
        tnet.run()

    def test_14_2_1_2(self):
        """14.2.1.1 Execute Forwarded-NPDU (Two-hop Distribution)."""
        if _debug: TestBBMD._debug("test_14_2_1_2")

        # create a network
        tnet = TNetwork(2)

        # implementation under test
        iut = BIPBBMDApplication("192.168.1.2/24", tnet.vlan[0])
        if _debug: TestBBMD._debug("    - iut.bip: %r", iut.bip)

        # BBMD on net 2
        bbmd1 = BIPBBMDNode("192.168.2.2/24", tnet.vlan[1])

        # add the IUT as a two-hop peer
        bbmd1.bip.add_peer(Address("192.168.1.2/32"))
        if _debug: TestBBMD._debug("    - bbmd1.bip: %r", bbmd1.bip)

        # test device
        td = BIPSimpleApplicationLayerStateMachine("192.168.2.3/24", tnet.vlan[1])
        tnet.append(td)

        # listener looks for extra traffic
        listener = BIPStateMachine("192.168.1.3/24", tnet.vlan[0])
        listener.mux.node.promiscuous = True
        tnet.append(listener)

        # broadcast a forwarded NPDU
        td.start_state.doc("2-3-0") \
            .send(WhoIsRequest(destination=LocalBroadcast())).doc("2-3-1") \
            .receive(IAmRequest).doc("2-3-2") \
            .success()

        # listen for the forwarded NPDU.  The packet will be sent upstream which
        # will generate the original unicast going back, then it will be
        # re-broadcast on the local LAN.  Fail if there's anything after that.
        s241 = listener.start_state.doc("2-4-0") \
            .receive(ForwardedNPDU).doc("2-4-1")

        # look for the original unicast going back, followed by the rebroadcast
        # of the forwarded NPDU on the local LAN
        both = s241 \
            .receive(OriginalUnicastNPDU).doc("2-4-1-a") \
            .receive(ForwardedNPDU).doc("2-4-1-b")

        # fail if anything is received after both packets
        both.timeout(3).doc("2-4-4") \
            .success()

        # allow the two packets in either order
        s241.receive(ForwardedNPDU).doc("2-4-2-a") \
            .receive(OriginalUnicastNPDU, next_state=both).doc("2-4-2-b")

        # run the group
        tnet.run()

