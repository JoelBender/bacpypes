#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test I-Am-Router-To-Network API
-------------------------------

Network 1 has sniffer1, the TD is on network 2 with sniffer2, network 3 has
sniffer3.  Network 1 and 2 are connected with a router, network 2 and 3
are connected by a different router.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, btox, xtob

from bacpypes.comm import Client, Server, bind
from bacpypes.pdu import PDU, Address, LocalBroadcast
from bacpypes.vlan import Network

from bacpypes.npdu import (
    npdu_types, NPDU,
    WhoIsRouterToNetwork, IAmRouterToNetwork, ICouldBeRouterToNetwork,
    RejectMessageToNetwork, RouterBusyToNetwork, RouterAvailableToNetwork,
    RoutingTableEntry, InitializeRoutingTable, InitializeRoutingTableAck,
    EstablishConnectionToNetwork, DisconnectConnectionToNetwork,
    WhatIsNetworkNumber, NetworkNumberIs,
    )

from ..state_machine import match_pdu, StateMachineGroup, TrafficLog
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import NetworkLayerStateMachine, RouterStateMachine

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

        # implementation under test
        self.iut = RouterStateMachine()
        self.append(self.iut)

        # make a little LAN
        self.vlan1 = Network(name="vlan1", broadcast_address=LocalBroadcast())
        self.vlan1.traffic_log = self.traffic_log

        # sniffer node
        self.sniffer1 = NetworkLayerStateMachine("1", self.vlan1)
        self.append(self.sniffer1)

        # make another little LAN
        self.vlan2 = Network(name="vlan2", broadcast_address=LocalBroadcast())
        self.vlan2.traffic_log = self.traffic_log

        # sniffer node
        self.sniffer2 = NetworkLayerStateMachine("3", self.vlan2)
        self.append(self.sniffer2)

        # make another little LAN
        self.vlan3 = Network(name="vlan3", broadcast_address=LocalBroadcast())
        self.vlan3.traffic_log = self.traffic_log

        # sniffer node
        self.sniffer3 = NetworkLayerStateMachine("4", self.vlan3)
        self.append(self.sniffer3)

        # connect the vlans to the router
        self.iut.add_network("5", self.vlan1, 1)
        self.iut.add_network("6", self.vlan2, 2)
        self.iut.add_network("7", self.vlan3, 3)

    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)

        # run the group
        super(TNetwork, self).run()

        # run it for some time
        run_time_machine(time_limit)
        if _debug:
            TNetwork._debug("    - time machine finished")

            # list the state machines which shows their current state
            for state_machine in self.state_machines:
                TNetwork._debug("    - machine: %r", state_machine)

                # each one has a list of sent/received pdus
                for direction, pdu in state_machine.transaction_log:
                    TNetwork._debug("        %s %s", direction, str(pdu))

            # traffic log has what was processed on each vlan
            self.traffic_log.dump(TNetwork._debug)

        # check for success
        all_success, some_failed = super(TNetwork, self).check_for_success()
        assert all_success


@bacpypes_debugging
class TestSimple(unittest.TestCase):

    def test_idle(self):
        """Test an idle network, nothing happens is success."""
        if _debug: TestSimple._debug("test_idle")

        # create a network
        tnet = TNetwork()

        # all start states are successful
        tnet.iut.start_state.success()
        tnet.sniffer1.start_state.success()
        tnet.sniffer2.start_state.success()
        tnet.sniffer3.start_state.success()

        # run the group
        tnet.run()


@bacpypes_debugging
class TestIAmRouterToNetwork(unittest.TestCase):

    def test_01(self):
        """Test sending complete path to all adapters."""
        if _debug: TestIAmRouterToNetwork._debug("test_01")

        # create a network
        tnet = TNetwork()

        # test device sends request
        tnet.iut.start_state.doc("1-1-0") \
            .call(tnet.iut.nse.i_am_router_to_network).doc("1-1-1") \
            .success()

        # network 1 sees router to networks 2 and 3
        tnet.sniffer1.start_state.doc("1-2-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[2, 3],
                ).doc("1-2-1") \
            .success()

        # network 2 sees router to networks 1 and 3
        tnet.sniffer2.start_state.doc("1-3-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1, 3],
                ).doc("1-3-1") \
            .success()

        # network 3 sees router to networks 1 and 2
        tnet.sniffer3.start_state.doc("1-4-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1, 2],
                ).doc("1-4-1") \
            .success()

        # run the group
        tnet.run()

    def test_02(self):
        """Test sending to a specific adapter."""
        if _debug: TestIAmRouterToNetwork._debug("test_02")

        # create a network
        tnet = TNetwork()

        # extract the adapter to network 1
        net_1_adapter = tnet.iut.nsap.adapters[1]
        if _debug: TestIAmRouterToNetwork._debug("    - net_1_adapter: %r", net_1_adapter)

        # test device sends request
        tnet.iut.start_state.doc("2-1-0") \
            .call(tnet.iut.nse.i_am_router_to_network, adapter=net_1_adapter).doc("2-1-1") \
            .success()

        # network 1 sees router to networks 2 and 3
        tnet.sniffer1.start_state.doc("2-2-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[2, 3],
                ).doc("2-2-1") \
            .success()

        # network 2 sees nothing
        tnet.sniffer2.start_state.doc("2-3-0") \
            .timeout(10).doc("2-3-1") \
            .success()

        # network 3 sees nothing
        tnet.sniffer3.start_state.doc("2-4-0") \
            .timeout(10).doc("2-4-1") \
            .success()

        # run the group
        tnet.run()

    def test_03(self):
        """Test sending to a network broadcast address."""
        if _debug: TestIAmRouterToNetwork._debug("test_03")

        # create a network
        tnet = TNetwork()

        # test device sends request
        tnet.iut.start_state.doc("3-1-0") \
            .call(tnet.iut.nse.i_am_router_to_network,
                destination=Address("1:*"),
                ).doc("3-1-1") \
            .success()

        # network 1 sees router to networks 2 and 3
        tnet.sniffer1.start_state.doc("3-2-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[2, 3],
                ).doc("3-2-1") \
            .success()

        # network 2 sees nothing
        tnet.sniffer2.start_state.doc("3-3-0") \
            .timeout(10).doc("3-3-1") \
            .success()

        # network 3 sees nothing
        tnet.sniffer3.start_state.doc("3-4-0") \
            .timeout(10).doc("3-4-1") \
            .success()

        # run the group
        tnet.run()

    def test_04(self):
        """Test sending a specific network to all other networks."""
        if _debug: TestIAmRouterToNetwork._debug("test_04")

        # create a network
        tnet = TNetwork()

        # test device sends request
        tnet.iut.start_state.doc("4-1-0") \
            .call(tnet.iut.nse.i_am_router_to_network, network=1).doc("4-1-1") \
            .success()

        # network 1 sees nothing
        tnet.sniffer1.start_state.doc("4-2-0") \
            .timeout(10).doc("4-2-1") \
            .success()

        # network 2 sees router to network 1
        tnet.sniffer2.start_state.doc("4-3-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1],
                ).doc("4-3-1") \
            .success()

        # network 3 sees router to network 1
        tnet.sniffer3.start_state.doc("4-4-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1],
                ).doc("4-4-1") \
            .success()

        # run the group
        tnet.run()

    def test_05(self):
        """Test sending a specific network to a specific address, in this
        case sending to the sniffer on network 2."""
        if _debug: TestIAmRouterToNetwork._debug("test_05")

        # create a network
        tnet = TNetwork()

        # test device sends request
        tnet.iut.start_state.doc("5-1-0") \
            .call(tnet.iut.nse.i_am_router_to_network,
                destination=Address("2:3"),
                network=1,
                ).doc("5-1-1") \
            .success()

        # network 1 sees nothing
        tnet.sniffer1.start_state.doc("5-2-0") \
            .timeout(10).doc("5-2-1") \
            .success()

        # network 2 sees router to network 1
        tnet.sniffer2.start_state.doc("5-3-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1],
                ).doc("5-3-1") \
            .success()

        # network 3 sees nothing
        tnet.sniffer3.start_state.doc("5-4-0") \
            .timeout(10).doc("5-4-1") \
            .success()

        # run the group
        tnet.run()

    def test_06(self):
        """Similar to test_05, sending a specific network to a specific
        address, in this case sending to the sniffer on network 2 by
        providing an adapter and a local address."""
        if _debug: TestIAmRouterToNetwork._debug("test_06")

        # create a network
        tnet = TNetwork()

        # extract the adapter to network 1
        net_2_adapter = tnet.iut.nsap.adapters[2]
        if _debug: TestIAmRouterToNetwork._debug("    - net_2_adapter: %r", net_2_adapter)

        # test device sends request
        tnet.iut.start_state.doc("6-1-0") \
            .call(tnet.iut.nse.i_am_router_to_network,
                adapter=net_2_adapter,
                destination=Address("3"),
                network=1,
                ).doc("6-1-1") \
            .success()

        # network 1 sees nothing
        tnet.sniffer1.start_state.doc("6-2-0") \
            .timeout(10).doc("6-2-1") \
            .success()

        # network 2 sees router to network 1
        tnet.sniffer2.start_state.doc("6-3-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1],
                ).doc("6-3-1") \
            .success()

        # network 3 sees nothing
        tnet.sniffer3.start_state.doc("6-4-0") \
            .timeout(10).doc("6-4-1") \
            .success()

        # run the group
        tnet.run()

