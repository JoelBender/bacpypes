#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test NPDU Encoding and Decoding
-------------------------------
"""

import string
import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, btox, xtob

from bacpypes.comm import Client, Server, bind
from bacpypes.pdu import PDU, Address, LocalBroadcast

from bacpypes.npdu import (
    npdu_types, NPDU,
    WhoIsRouterToNetwork, IAmRouterToNetwork, ICouldBeRouterToNetwork,
    RejectMessageToNetwork, RouterBusyToNetwork, RouterAvailableToNetwork,
    RoutingTableEntry, InitializeRoutingTable, InitializeRoutingTableAck,
    EstablishConnectionToNetwork, DisconnectConnectionToNetwork,
    WhatIsNetworkNumber, NetworkNumberIs,
    )

from ..trapped_classes import TrappedClient, TrappedServer
from ..state_machine import match_pdu

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class NPDUCodec(Client, Server):

    def __init__(self):
        if _debug: NPDUCodec._debug("__init__")

        Client.__init__(self)
        Server.__init__(self)

    def indication(self, npdu):
        if _debug: NPDUCodec._debug("indication %r", npdu)

        # first as a generic NPDU
        xpdu = NPDU()
        npdu.encode(xpdu)

        # now as a vanilla PDU
        ypdu = PDU()
        xpdu.encode(ypdu)
        if _debug: NPDUCodec._debug("    - encoded: %r", ypdu)

        # send it downstream
        self.request(ypdu)

    def confirmation(self, pdu):
        if _debug: NPDUCodec._debug("confirmation %r", pdu)

        # decode as a generic NPDU
        xpdu = NPDU()
        xpdu.decode(pdu)

        # do a deeper decode of the NPDU
        ypdu = npdu_types[xpdu.npduNetMessage]()
        ypdu.decode(xpdu)

        # send it upstream
        self.response(ypdu)


@bacpypes_debugging
class TestNPDUCodec(unittest.TestCase):

    def setup_method(self, method):
        """This function is called before each test method is called as is
        given a reference to the test method."""
        if _debug: TestNPDUCodec._debug("setup_method %r", method)

        # minature trapped stack
        self.client = TrappedClient()
        self.codec = NPDUCodec()
        self.server = TrappedServer()
        bind(self.client, self.codec, self.server)

    def request(self, pdu):
        """Pass the PDU to the client to send down the stack."""
        self.client.request(pdu)

    def indication(self, pdu_type=None, **pdu_attrs):
        """Check what the server received."""
        assert match_pdu(self.server.indication_received, pdu_type, **pdu_attrs)

    def response(self, pdu):
        """Pass the PDU to the server to send up the stack."""
        self.server.response(pdu)

    def confirmation(self, pdu_type=None, **pdu_attrs):
        """Check what the client received."""
        assert match_pdu(self.client.confirmation_received, pdu_type, **pdu_attrs)

    def test_who_is_router_to_network(self):
        """Test the Result encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_who_is_router_to_network")

        # Request successful
        pdu_bytes = xtob('01.80'        # version, network layer message
            '00 0001'                   # message type and network
            )

        self.request(WhoIsRouterToNetwork(1))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(WhoIsRouterToNetwork, wirtnNetwork=1)

    def test_i_am_router_to_network_empty(self):
        """Test the IAmRouterToNetwork with no networks encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_i_am_router_to_network_empty")

        # Request successful
        network_list = []
        pdu_bytes = xtob('01.80'        # version, network layer message
            '01'                        # message type, no networks
            )

        self.request(IAmRouterToNetwork(network_list))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(IAmRouterToNetwork, iartnNetworkList=network_list)

    def test_i_am_router_to_networks(self):
        """Test the IAmRouterToNetwork with multiple networks encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_i_am_router_to_networks")

        # Request successful
        network_list = [1, 2, 3]
        pdu_bytes = xtob('01.80'        # version, network layer message
            '01 0001 0002 0003'         # message type and network list
            )

        self.request(IAmRouterToNetwork(network_list))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(IAmRouterToNetwork, iartnNetworkList=network_list)

    def test_i_could_be_router_to_network(self):
        """Test the ICouldBeRouterToNetwork encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_i_could_be_router_to_network")

        # Request successful
        pdu_bytes = xtob('01.80'        # version, network layer message
            '02 0001 02'                # message type, network, performance
            )

        self.request(ICouldBeRouterToNetwork(1, 2))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ICouldBeRouterToNetwork, icbrtnNetwork=1, icbrtnPerformanceIndex=2)

    def test_reject_message_to_network(self):
        """Test the RejectMessageToNetwork encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_reject_message_to_network")

        # Request successful
        pdu_bytes = xtob('01.80'        # version, network layer message
            '03 01 0002'                # message type, network, performance
            )

        self.request(RejectMessageToNetwork(1, 2))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(RejectMessageToNetwork, rmtnRejectionReason=1, rmtnDNET=2)

    def test_router_busy_to_network_empty(self):
        """Test the RouterBusyToNetwork with no networks encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_router_busy_to_network_empty")

        # Request successful
        network_list = []
        pdu_bytes = xtob('01.80'        # version, network layer message
            '04'                        # message type, no networks
            )

        self.request(RouterBusyToNetwork(network_list))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(RouterBusyToNetwork, rbtnNetworkList=network_list)

    def test_router_busy_to_networks(self):
        """Test the RouterBusyToNetwork with multiple networks encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_router_busy_to_networks")

        # Request successful
        network_list = [1, 2, 3]
        pdu_bytes = xtob('01.80'        # version, network layer message
            '04 0001 0002 0003'         # message type and network list
            )

        self.request(RouterBusyToNetwork(network_list))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(RouterBusyToNetwork, rbtnNetworkList=network_list)

    def test_router_available_to_network_empty(self):
        """Test the RouterAvailableToNetwork with no networks encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_router_available_to_network_empty")

        # Request successful
        network_list = []
        pdu_bytes = xtob('01.80'        # version, network layer message
            '05'                        # message type, no networks
            )

        self.request(RouterAvailableToNetwork(network_list))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(RouterAvailableToNetwork, ratnNetworkList=network_list)

    def test_router_available_to_networks(self):
        """Test the RouterAvailableToNetwork with multiple networks encoding and decoding."""
        if _debug: TestNPDUCodec._debug("test_router_available_to_networks")

        # Request successful
        network_list = [1, 2, 3]
        pdu_bytes = xtob('01.80'        # version, network layer message
            '05 0001 0002 0003'         # message type and network list
            )

        self.request(RouterAvailableToNetwork(network_list))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(RouterAvailableToNetwork, ratnNetworkList=network_list)

    def test_initialize_routing_table_empty(self):
        """Test the InitializeRoutingTable with no routing table entries."""
        if _debug: TestNPDUCodec._debug("test_initialize_routing_table_empty")

        # Request successful
        pdu_bytes = xtob('01.80'        # version, network layer message
            '06 00'                     # message type and list length
            )

        self.request(InitializeRoutingTable())
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(InitializeRoutingTable, irtTable=[])

    def test_initialize_routing_table_01(self):
        """Test the RouterAvailableToNetwork with a routing table entry."""
        if _debug: TestNPDUCodec._debug("test_initialize_routing_table_01")

        # build a routing table entry
        rte = RoutingTableEntry(1, 2, xtob(''))
        rt_entries = [rte]

        # Request successful
        pdu_bytes = xtob('01.80'        # version, network layer message
            '06 01'                     # message type and list length
                '0001 02 00'            # network, port number, port info
            )

        self.request(InitializeRoutingTable(rt_entries))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(InitializeRoutingTable, irtTable=rt_entries)

    def test_initialize_routing_table_02(self):
        """Test the RouterAvailableToNetwork with a routing table entry."""
        if _debug: TestNPDUCodec._debug("test_initialize_routing_table_02")

        # build a routing table entry
        rte = RoutingTableEntry(3, 4, xtob('deadbeef'))
        rt_entries = [rte]

        # Request successful
        pdu_bytes = xtob('01.80'        # version, network layer message
            '06 01'                     # message type and list length
                '0003 04 04 DEADBEEF'   # network, port number, port info
            )

        self.request(InitializeRoutingTable(rt_entries))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(InitializeRoutingTable, irtTable=rt_entries)

