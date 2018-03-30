#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Network Discovery
----------------------

The TD is an application on network 1 with sniffer1, network 2 has an
application node and sniffer2.  Both networks are connected to one IUT router.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, btox, xtob

from bacpypes.comm import Client, Server, bind
from bacpypes.pdu import PDU, Address, LocalBroadcast, GlobalBroadcast
from bacpypes.vlan import Network

from bacpypes.npdu import (
    npdu_types, NPDU,
    WhoIsRouterToNetwork, IAmRouterToNetwork, ICouldBeRouterToNetwork,
    RejectMessageToNetwork, RouterBusyToNetwork, RouterAvailableToNetwork,
    RoutingTableEntry, InitializeRoutingTable, InitializeRoutingTableAck,
    EstablishConnectionToNetwork, DisconnectConnectionToNetwork,
    WhatIsNetworkNumber, NetworkNumberIs,
    )
from bacpypes.apdu import (
    WhoIsRequest, IAmRequest,
    )

from ..state_machine import match_pdu, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import SnifferNode, NetworkLayerNode, RouterNode, ApplicationLayerNode

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

        # implementation under test
        self.iut = RouterNode()

        # make a little LAN
        self.vlan1 = Network(name="vlan1", broadcast_address=LocalBroadcast())

        # test device
        self.td = ApplicationLayerNode("1", self.vlan1)
        self.append(self.td)

        # sniffer node
        self.sniffer1 = SnifferNode("2", self.vlan1)
        self.append(self.sniffer1)

        # add the network
        self.iut.add_network("3", self.vlan1, 1)

        # make another little LAN
        self.vlan2 = Network(name="vlan3", broadcast_address=LocalBroadcast())

        # application node
        self.app2 = ApplicationLayerNode("4", self.vlan2)
        self.append(self.app2)

        # sniffer node
        self.sniffer2 = SnifferNode("5", self.vlan2)
        self.append(self.sniffer2)

        # add the network
        self.iut.add_network("6", self.vlan2, 2)

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
        tnet.app2.start_state.success()
        tnet.sniffer2.start_state.success()

        # run the group
        tnet.run()


@bacpypes_debugging
class TestUnconfirmedRequests(unittest.TestCase):

    def test_no_response(self):
        """Local broadcast, no matching device."""
        if _debug: TestSimple._debug("test_no_response")

        # create a network
        tnet = TNetwork()

        # test device sends request, no response
        tnet.td.start_state.doc("1-1-0") \
            .send(WhoIsRequest(
                destination=LocalBroadcast(),
                )).doc("1-1-1") \
            .timeout(3).doc("1-1-2") \
            .success()

        # sniffer on network 1 sees the request and nothing else
        tnet.sniffer1.start_state.doc("1-2-0") \
            .receive(PDU,
                pduData=xtob('01.00'        # version, application layer
                    '10 08'                 # unconfirmed Who-Is
                    )
                ).doc("1-2-1") \
            .timeout(3).doc("1-2-2") \
            .success()

        # no acitivity on network 2
        tnet.app2.start_state.success()
        tnet.sniffer2.start_state.success()

        # run the group
        tnet.run()

    def test_global_broadcast(self):
        """Global broadcast, matching device."""
        if _debug: TestSimple._debug("test_global_broadcast")

        # create a network
        tnet = TNetwork()

        # test device sends request, no response
        tnet.td.start_state.doc("2-1-0") \
            .send(WhoIsRequest(
                destination=GlobalBroadcast(),
                )).doc("2-1-1") \
            .timeout(3).doc("2-1-2") \
            .success()

        # sniffer on network 1 sees the request and nothing else
        tnet.sniffer1.start_state.doc("2-2-0") \
            .receive(PDU,
                pduData=xtob('01.20.ff.ff.00.ff'
                    '10.08'
                    )
                ).doc("2-2-1") \
            .receive(PDU,
                pduData=xtob('01.08.00.02.01.04.10.00.c4.02.00.00.04.22.04.00.91.00.22.03.e7'
                    )
                ).doc("2-2-2") \
            .timeout(3).doc("2-2-3") \
            .success()

        # no monitored activity on app2
        tnet.app2.start_state.success()

        # network 2 has local broadcast request and unicast response
        tnet.sniffer2.start_state.doc('2-3-0') \
            .receive(PDU,
                pduData=xtob('01.28.ff.ff.00.00.01.01.01.fe.10.08'
                    )
                ).doc("2-3-1") \
            .receive(PDU,
                pduData=xtob('01.20.00.01.01.01.ff.10.00.c4.02.00.00.04.22.04.00.91.00.22.03.e7'
                    )
                ).doc("2-3-1") \
            .timeout(3).doc("2-3-2") \
            .success()

        # run the group
        tnet.run()

