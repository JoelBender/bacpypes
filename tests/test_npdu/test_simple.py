#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test NPDU Encoding and Decoding
-------------------------------
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

from ..state_machine import match_pdu, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import SnifferNode, NetworkLayerNode, RouterNode

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
        self.vlan1 = Network(name="vlan1", broadcast_address=LocalBroadcast())

        # test device
        self.td = NetworkLayerNode("1", self.vlan1)
        self.append(self.td)

        # sniffer node
        self.sniffer1 = SnifferNode("2", self.vlan1)
        self.append(self.sniffer1)

        # make another little LAN
        self.vlan2 = Network(name="vlan2", broadcast_address=LocalBroadcast())

        # sniffer node
        self.sniffer2 = SnifferNode("3", self.vlan2)
        self.append(self.sniffer2)

        # implementation under test
        self.iut = RouterNode()

        # add the networks
        self.iut.add_network("4", self.vlan1, 1)
        self.iut.add_network("5", self.vlan2, 2)

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

        # run the group
        tnet.run()


@bacpypes_debugging
class TestWhoIsRouterToNetwork(unittest.TestCase):

    def test_01(self):
        """Test broadcast for any router."""
        if _debug: TestWhoIsRouterToNetwork._debug("test_01")

        # create a network
        tnet = TNetwork()

        # all start states are successful
        tnet.td.start_state.doc("1-1-0") \
            .send(WhoIsRouterToNetwork(
                destination=LocalBroadcast(),
                )).doc("1-1-1") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[2],
                ).doc("1-1-2") \
            .success()

        tnet.sniffer1.start_state.success()

        # nothing received on network 2
        tnet.sniffer2.start_state.doc("1-2-0") \
            .timeout(3).doc("1-2-1") \
            .success()

        # run the group
        tnet.run()

    def test_02(self):
        """Test broadcast for existing router."""
        if _debug: TestWhoIsRouterToNetwork._debug("test_02")

        # create a network
        tnet = TNetwork()

        # all start states are successful
        tnet.td.start_state.doc("2-1-0") \
            .send(WhoIsRouterToNetwork(2,
                destination=LocalBroadcast(),
                )).doc("2-1-1") \
            .receive(IAmRouterToNetwork,
                iartnNetworkList=[2],
                ).doc("2-1-2") \
            .success()

        tnet.sniffer1.start_state.success()

        # nothing received on network 2
        tnet.sniffer2.start_state.doc("2-2-0") \
            .timeout(3).doc("2-2-1") \
            .success()

        # run the group
        tnet.run()

    def test_03(self):
        """Test broadcast for a non-existent router."""
        if _debug: TestWhoIsRouterToNetwork._debug("test_03")

        # create a network
        tnet = TNetwork()

        # send request, receive nothing back
        tnet.td.start_state.doc("3-1-0") \
            .send(WhoIsRouterToNetwork(3,
                destination=LocalBroadcast(),
                )).doc("3-1-1") \
            .timeout(3).doc("3-1-2") \
            .success()

        # sniffer on network 1 sees the request
        tnet.sniffer1.start_state.doc("3-2-0") \
            .receive(PDU,
                pduData=xtob('01.80'        # version, network layer
                    '00 0003'               # message type and network
                    )
                ).doc("3-2-1") \
            .success()

        # sniffer on network 2 sees request forwarded by router
        tnet.sniffer2.start_state.doc("3-3-0") \
            .receive(PDU,
                pduData=xtob('01.88'        # version, network layer, routed
                    '0001 01 01'            # snet/slen/sadr
                    '00 0003'               # message type and network
                    ),
                ).doc("3-3-1") \
            .success()

        # run the group
        tnet.run()

