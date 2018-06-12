#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Network Discovery
----------------------

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

        # implementation under test
        self.iut1 = RouterNode()    # router from vlan1 to vlan2
        self.iut2 = RouterNode()    # router from vlan2 to vlan3

        # make a little LAN
        self.vlan1 = Network(name="vlan1", broadcast_address=LocalBroadcast())
        self.vlan1.traffic_log = self.traffic_log

        # sniffer node
        self.sniffer1 = SnifferStateMachine("1", self.vlan1)
        self.append(self.sniffer1)

        # connect vlan1 to iut1
        self.iut1.add_network("2", self.vlan1, 1)

        # make another little LAN
        self.vlan2 = Network(name="vlan2", broadcast_address=LocalBroadcast())
        self.vlan2.traffic_log = self.traffic_log

        # test device
        self.td = NetworkLayerStateMachine("3", self.vlan2)
        self.append(self.td)

        # sniffer node
        self.sniffer2 = SnifferStateMachine("4", self.vlan2)
        self.append(self.sniffer2)

        # connect vlan2 to both routers
        self.iut1.add_network("5", self.vlan2, 2)
        self.iut2.add_network("6", self.vlan2, 2)

        # make another little LAN
        self.vlan3 = Network(name="vlan3", broadcast_address=LocalBroadcast())
        self.vlan3.traffic_log = self.traffic_log

        # sniffer node
        self.sniffer3 = SnifferStateMachine("7", self.vlan3)
        self.append(self.sniffer3)

        # connect vlan3 to the second router
        self.iut2.add_network("8", self.vlan3, 3)

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
        tnet.td.start_state.success()
        tnet.sniffer1.start_state.success()
        tnet.sniffer2.start_state.success()
        tnet.sniffer3.start_state.success()

        # run the group
        tnet.run()


@bacpypes_debugging
class TestWhoIsRouterToNetwork(unittest.TestCase):

    def test_01(self):
        """Test broadcast for any router."""
        if _debug: TestWhoIsRouterToNetwork._debug("test_01")

        # create a network
        tnet = TNetwork()


        # test device sends request
        s111 = tnet.td.start_state.doc("1-1-0") \
            .send(WhoIsRouterToNetwork(
                destination=LocalBroadcast(),
                )).doc("1-1-1")

        # test device sees both responses
        both = s111 \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1],
                ).doc("1-1-2-a") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[3],
                ).doc("1-1-2-b") \

        # allow the two packets in either order
        s111.receive(IAmRouterToNetwork,
                iartnNetworkList=[3],
                ).doc("1-1-2-c") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[1],
                next_state=both).doc("1-1-2-d") \

        # fail if anything is received after both packets
        both.timeout(3).doc("1-1-3") \
            .success()

        # short circuit the snifferse
        tnet.sniffer1.start_state.success()
        tnet.sniffer2.start_state.success()
        tnet.sniffer3.start_state.success()

        # run the group
        tnet.run()

