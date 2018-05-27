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
from bacpypes.pdu import (
    PDU, Address, LocalBroadcast,
    RemoteStation, RemoteBroadcast,GlobalBroadcast,
    )
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
    ReadPropertyRequest, ReadPropertyACK,
    AbortPDU,
    )

from ..state_machine import match_pdu, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine, current_time

from .helpers import (
    SnifferStateMachine, NetworkLayerStateMachine, RouterNode, ApplicationLayerStateMachine,
    ApplicationNode,
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

        # implementation under test
        self.iut = RouterNode()

        # make a little LAN
        self.vlan1 = Network(name="vlan1", broadcast_address=LocalBroadcast())

        # test device
        self.td = ApplicationLayerStateMachine("1", self.vlan1)
        self.append(self.td)

        # sniffer node
        self.sniffer1 = SnifferStateMachine("2", self.vlan1)
        self.append(self.sniffer1)

        # add the network
        self.iut.add_network("3", self.vlan1, 1)

        # make another little LAN
        self.vlan2 = Network(name="vlan3", broadcast_address=LocalBroadcast())

        # application node, not a state machine
        self.app2 = ApplicationNode("4", self.vlan2)

        # sniffer node
        self.sniffer2 = SnifferStateMachine("5", self.vlan2)
        self.append(self.sniffer2)

        # add the network
        self.iut.add_network("6", self.vlan2, 2)

    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)
        if _debug: TNetwork._debug("    - current_time: %r", current_time())

        # run the group
        super(TNetwork, self).run()
        if _debug: TNetwork._debug("    - current_time: %r", current_time())

        # run it for some time
        run_time_machine(time_limit)
        if _debug: TNetwork._debug("    - current_time: %r", current_time())

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
class TestUnconfirmedRequests(unittest.TestCase):

    def test_local_broadcast(self):
        """Local broadcast, no matching device."""
        if _debug: TestUnconfirmedRequests._debug("test_local_broadcast")

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
        tnet.sniffer2.start_state.success()

        # run the group
        tnet.run()

    def test_remote_broadcast_2(self):
        """Remote broadcast, matching device."""
        if _debug: TestUnconfirmedRequests._debug("test_remote_broadcast_2")

        # create a network
        tnet = TNetwork()

        # test device sends request and sees the response
        tnet.td.start_state.doc("2-1-0") \
            .send(WhoIsRequest(
                destination=RemoteBroadcast(2),
                )).doc("2-1-1") \
            .success()

        # sniffer on network 1 sees the request and the response
        tnet.sniffer1.start_state.doc("2-2-0") \
            .receive(PDU,
                pduData=xtob('01.80.00.00.02'       # who is router to network
                    )
                ).doc("2-2-1") \
            .receive(PDU,
                pduData=xtob('01.80.01.00.02'       # I am router to network
                    )
                ).doc("2-2-1") \
            .receive(PDU,
                pduData=xtob('01.20.00.02.00.ff'    # remote broadcast goes out
                    '10.08'
                    )
                ).doc("2-2-1") \
            .receive(PDU,
                pduData=xtob('01.08.00.02.01.04'    # unicast response
                    '10.00.c4.02.00.00.04.22.04.00.91.00.22.03.e7'
                    )
                ).doc("2-2-2") \
            .timeout(3).doc("2-2-3") \
            .success()

        # network 2 sees local broadcast request and unicast response
        tnet.sniffer2.start_state.doc('2-3-0') \
            .receive(PDU,
                pduData=xtob('01.08.00.01.01.01'    # local broadcast
                    '10.08'
                    )
                ).doc("2-3-1") \
            .receive(PDU,
                pduData=xtob('01.20.00.01.01.01.ff' # unicast response
                    '10.00.c4.02.00.00.04.22.04.00.91.00.22.03.e7'
                    )
                ).doc("2-3-1") \
            .timeout(3).doc("2-3-2") \
            .success()

        # run the group
        tnet.run()

    def test_remote_broadcast_3(self):
        """Remote broadcast, nonexistent network."""
        if _debug: TestUnconfirmedRequests._debug("test_remote_broadcast_3")

        # create a network
        tnet = TNetwork()

        # test device sends request and sees the response
        tnet.td.start_state.doc("3-1-0") \
            .send(WhoIsRequest(
                destination=RemoteBroadcast(3),
                )).doc("3-1-1") \
            .success()

        # sniffer on network 1 sees the request and the response
        tnet.sniffer1.start_state.doc("3-2-0") \
            .receive(PDU,
                pduData=xtob('01.80.00.00.03'       # who is router to network
                    )
                ).doc("3-2-1") \
            .timeout(3).doc("3-2-3") \
            .success()

        # network 2 sees local broadcast looking for network 3
        tnet.sniffer2.start_state.doc('3-3-0') \
            .receive(PDU,
                pduData=xtob('01.88.00.01.01.01.00.00.03'
                    )
                ).doc("3-3-1") \
            .timeout(3).doc("3-3-2") \
            .success()

        # run the group
        tnet.run()

    def test_global_broadcast(self):
        """Global broadcast, matching device."""
        if _debug: TestUnconfirmedRequests._debug("test_global_broadcast")

        # create a network
        tnet = TNetwork()

        # test device sends request and sees the response
        tnet.td.start_state.doc("4-1-0") \
            .send(WhoIsRequest(
                destination=GlobalBroadcast(),
                )).doc("4-1-1") \
            .receive(IAmRequest).doc("4-1-2") \
            .success()

        # sniffer on network 1 sees the request and the response
        tnet.sniffer1.start_state.doc("4-2-0") \
            .receive(PDU,
                pduData=xtob('01.20.ff.ff.00.ff'
                    '10.08'
                    )
                ).doc("4-2-1") \
            .receive(PDU,
                pduData=xtob('01.08.00.02.01.04'
                    '10.00.c4.02.00.00.04.22.04.00.91.00.22.03.e7'
                    )
                ).doc("4-2-2") \
            .timeout(3).doc("4-2-3") \
            .success()

        # network 2 sees local broadcast request and unicast response
        tnet.sniffer2.start_state.doc('4-3-0') \
            .receive(PDU,
                pduData=xtob('01.28.ff.ff.00.00.01.01.01.fe'
                    '10.08'
                    )
                ).doc("4-3-1") \
            .receive(PDU,
                pduData=xtob('01.20.00.01.01.01.ff'
                    '10.00.c4.02.00.00.04.22.04.00.91.00.22.03.e7'
                    )
                ).doc("4-3-3") \
            .timeout(3).doc("4-3-3") \
            .success()

        # run the group
        tnet.run()


@bacpypes_debugging
class TestConfirmedRequests(unittest.TestCase):

    def test_remote_read_2(self):
        """Remote read property, matching device."""
        if _debug: TestConfirmedRequests._debug("test_remote_read_2")

        # create a network
        tnet = TNetwork()

        # test device sends request and sees the response
        tnet.td.start_state.doc("5-1-0") \
            .send(ReadPropertyRequest(
                destination=RemoteStation(2, 4),
                objectIdentifier=('device', 4),
                propertyIdentifier='vendorIdentifier',
                )).doc("5-1-1") \
            .receive(ReadPropertyACK).doc("5-1-2") \
            .success()

        # sniffer on network 1 sees the request and the response
        tnet.sniffer1.start_state.doc("5-2-0") \
            .receive(PDU,
                pduData=xtob('01.80.00.00.02'       # who is router to network
                    )
                ).doc("5-2-1") \
            .receive(PDU,
                pduData=xtob('01.80.01.00.02'       # I am router to network
                    )
                ).doc("5-2-2") \
            .receive(PDU,
                pduData=xtob('01.24.00.02.01.04.ff'                 # request
                    '02.44.01.0c.0c.02.00.00.04.19.78'
                    )
                ).doc("5-2-3") \
            .receive(PDU,
                pduData=xtob('01.08.00.02.01.04'                    # ack
                    '30.01.0c.0c.02.00.00.04.19.78.3e.22.03.e7.3f'
                    )
                ).doc("5-2-4") \
            .timeout(3).doc("5-2-5") \
            .success()

        # network 2 sees routed request and unicast response
        tnet.sniffer2.start_state.doc('5-3-0') \
            .receive(PDU,
                pduData=xtob('01.0c.00.01.01.01'                    # request
                    '02.44.01.0c.0c.02.00.00.04.19.78'
                    )
                ).doc("5-3-1") \
            .receive(PDU,
                pduData=xtob('01.20.00.01.01.01.ff'                 # ack
                    '30.01.0c.0c.02.00.00.04.19.78.3e.22.03.e7.3f'
                    )
                ).doc("5-3-2") \
            .timeout(3).doc("5-3-3") \
            .success()

        # run the group
        tnet.run()

    def test_remote_read_3(self):
        """Remote read property, nonexistent device."""
        if _debug: TestConfirmedRequests._debug("test_remote_read_3")

        # create a network
        tnet = TNetwork()

        # test device sends request and sees the response
        tnet.td.start_state.doc("6-1-0") \
            .send(ReadPropertyRequest(
                destination=RemoteStation(3, 5),
                objectIdentifier=('device', 5),
                propertyIdentifier='vendorIdentifier',
                )).doc("6-1-1") \
            .receive(AbortPDU,
                apduAbortRejectReason=65,
                ).doc("6-1-2") \
            .success()

        # sniffer on network 1 sees the request for a path
        tnet.sniffer1.start_state.doc("6-2-0") \
            .receive(PDU,
                pduData=xtob('01.80.00.00.03'       # who is router to network
                    )
                ).doc("6-2-1") \
            .timeout(3).doc("6-2-2") \
            .success()

        # network 2 sees local broadcast looking for network 3
        tnet.sniffer2.start_state.doc('6-3-0') \
            .receive(PDU,
                pduData=xtob('01.88.00.01.01.01.00.00.03'
                    )
                ).doc("6-3-1") \
            .timeout(3).doc("6-3-2") \
            .success()

        # run the group
        tnet.run()

