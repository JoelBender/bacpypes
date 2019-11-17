#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Network Discovery
----------------------

The TD is on network 1 with sniffer1, network 2 has sniffer2, network 3 has
sniffer3.  All three networks are connected to one IUT router.
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

from .helpers import SnifferStateMachine, NetworkLayerStateMachine, RouterNode

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

        # network 1
        self.vlan1 = Network(name="vlan1", broadcast_address=LocalBroadcast())
        self.vlan1.traffic_log = self.traffic_log

        # network 1 state machine
        self.td1 = NetworkLayerStateMachine("1", self.vlan1)
        self.append(self.td1)

        # network 2
        self.vlan2 = Network(name="vlan2", broadcast_address=LocalBroadcast())
        self.vlan2.traffic_log = self.traffic_log

        # network 2 state machine
        self.td2 = NetworkLayerStateMachine("2", self.vlan2)
        self.append(self.td2)

        # network 3
        self.vlan3 = Network(name="vlan3", broadcast_address=LocalBroadcast())
        self.vlan3.traffic_log = self.traffic_log

        # network 2 state machine
        self.td3 = NetworkLayerStateMachine("3", self.vlan3)
        self.append(self.td3)

        # implementation under test
        self.iut = RouterNode()

        # add the network connections
        self.iut.add_network("4", self.vlan1, 1)
        self.iut.add_network("5", self.vlan2, 2)
        self.iut.add_network("6", self.vlan3, 3)

    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)

        # run the group
        super(TNetwork, self).run()

        # run it for some time
        run_time_machine(time_limit)
        if _debug:
            TNetwork._debug("    - time machine finished")
            for state_machine in self.state_machines:
                TNetwork._debug("    - machine: %r", state_machine)
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
        tnet.td1.start_state.success()
        tnet.td2.start_state.success()
        tnet.td3.start_state.success()

        # run the group
        tnet.run()


@bacpypes_debugging
class TestNetworkStartup(unittest.TestCase):

    def test_01(self):
        """Broadcast I-Am-Router-To-Network messages."""
        if _debug: TestNetworkStartup._debug("test_01")

        # create a network
        tnet = TNetwork()

        # test device 1 initiates startup, receives I-Am-Router-To-Network
        tnet.td1.start_state.doc("1-1-0") \
            .timeout(1).doc("1-1-1") \
            .call(tnet.iut.nse.startup).doc("1-1-2") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[2, 3],
                ).doc("1-1-3") \
            .success()

        # test device 2 receives I-Am-Router-To-Network
        tnet.td2.start_state.doc("1-2-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1, 3],
                ).doc("1-2-1") \
            .success()

        # test device 3 receives I-Am-Router-To-Network
        tnet.td3.start_state.doc("1-3-0") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1, 2],
                ).doc("1-3-1") \
            .success()

        # run the group
        tnet.run()

