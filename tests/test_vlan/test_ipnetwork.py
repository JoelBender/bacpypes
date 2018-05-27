#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test IPNetwork
------------

This module tests the basic functionality of a crudely simulated IPv4 network,
source and destination addresses are tuples like those used for sockets and
the UDPDirector.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address, LocalBroadcast, PDU
from bacpypes.comm import bind
from bacpypes.vlan import IPNetwork, IPNode, IPRouter

from ..state_machine import ClientStateMachine, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TNetwork(StateMachineGroup):

    def __init__(self, node_count, address_pattern):
        if _debug: TNetwork._debug("__init__ %r", node_count)
        StateMachineGroup.__init__(self)

        self.vlan = IPNetwork()

        for i in range(node_count):
            node_address = Address(address_pattern.format(i + 1))
            node = IPNode(node_address, self.vlan)
            if _debug: TNetwork._debug("    - node: %r", node)

            # bind a client state machine to the node
            csm = ClientStateMachine()
            bind(csm, node)

            # add it to this group
            self.append(csm)

    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)

        # reset the time machine
        reset_time_machine()
        if _debug: TNetwork._debug("    - time machine reset")

        # run the group
        super(TNetwork, self).run()

        # run it for some time
        run_time_machine(time_limit)
        if _debug: TNetwork._debug("    - time machine finished")

        # check for success
        all_success, some_failed = super(TNetwork, self).check_for_success()
        assert all_success


@bacpypes_debugging
class TestVLAN(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        if _debug: TestVLAN._debug("__init__ %r %r", args, kwargs)
        super(TestVLAN, self).__init__(*args, **kwargs)

    def test_idle(self):
        """Test that a very quiet network can exist.  This is not a network
        test so much as a state machine group test.
        """
        if _debug: TestVLAN._debug("test_idle")

        # two element network
        tnet = TNetwork(2, "192.168.1.{}/24")
        tnode1, tnode2 = tnet.state_machines

        # set the start states of both machines to success
        tnode1.start_state.success()
        tnode2.start_state.success()

        # run the group
        tnet.run()

    def test_send_receive(self):
        """Test that a node can send a message to another node.
        """
        if _debug: TestVLAN._debug("test_send_receive")

        # two element network
        tnet = TNetwork(2, "192.168.2.{}/24")
        tnode1, tnode2 = tnet.state_machines

        # make a PDU from node 1 to node 2
        pdu = PDU(b'data',
            source=('192.168.2.1', 47808),
            destination=('192.168.2.2', 47808),
            )
        if _debug: TestVLAN._debug("    - pdu: %r", pdu)

        # node 1 sends the pdu, mode 2 gets it
        tnode1.start_state.send(pdu).success()
        tnode2.start_state.receive(PDU,
            pduSource=('192.168.2.1', 47808),
            ).success()

        # run the group
        tnet.run()

    def test_broadcast(self):
        """Test that a node can send out a 'local broadcast' message which will
        be received by every other node.
        """
        if _debug: TestVLAN._debug("test_broadcast")

        # three element network
        tnet = TNetwork(3, "192.168.3.{}/24")
        tnode1, tnode2, tnode3 = tnet.state_machines

        # make a broadcast PDU
        pdu = PDU(b'data',
            source=('192.168.3.1', 47808),
            destination=('192.168.3.255', 47808),
            )
        if _debug: TestVLAN._debug("    - pdu: %r", pdu)

        # node 1 sends the pdu, node 2 and 3 each get it
        tnode1.start_state.send(pdu).success()
        tnode2.start_state.receive(PDU,
            pduSource=('192.168.3.1', 47808),
            ).success()
        tnode3.start_state.receive(PDU,
            pduSource=('192.168.3.1', 47808)
            ).success()

        # run the group
        tnet.run()

    def test_spoof_fail(self):
        """Test verifying that a node cannot send out packets with a source
        address other than its own, see also test_spoof_pass().
        """
        if _debug: TestVLAN._debug("test_spoof_fail")

        # one element network
        tnet = TNetwork(1, "192.168.4.{}/24")
        tnode1, = tnet.state_machines

        # make a unicast PDU with the wrong source
        pdu = PDU(b'data',
            source=('192.168.4.2', 47808),
            destination=('192.168.4.3', 47808),
            )

        # the node sends the pdu and would be a success but...
        tnode1.start_state.send(pdu).success()

        # when the node attempts to send it raises an error
        with self.assertRaises(RuntimeError):
            tnet.run()

    def test_spoof_pass(self):
        """Test allowing a node to send out packets with a source address
        other than its own, see also test_spoof_fail().
        """
        if _debug: TestVLAN._debug("test_spoof_pass")

        # one node network
        tnet = TNetwork(1, "192.168.5.{}/24")
        tnode1, = tnet.state_machines

        # reach into the network and enable spoofing for the node
        tnet.vlan.nodes[0].spoofing = True

        # make a unicast PDU from a fictitious node
        pdu = PDU(b'data',
            source=('192.168.5.3', 47808),
            destination=('192.168.5.1', 47808),
            )

        # node 1 sends the pdu, but gets it back as if it was from node 3
        tnode1.start_state.send(pdu).receive(PDU,
            pduSource=('192.168.5.3', 47808),
            ).success()

        # run the group
        tnet.run()

    def test_promiscuous_pass(self):
        """Test 'promiscuous mode' of a node which allows it to receive every
        packet sent on the network.  This is like the network is a hub, or
        the node is connected to a 'monitor' port on a managed switch.
        """
        if _debug: TestVLAN._debug("test_promiscuous_pass")

        # three element network
        tnet = TNetwork(3, "192.168.6.{}/24")
        tnode1, tnode2, tnode3 = tnet.state_machines

        # reach into the network and enable promiscuous mode
        tnet.vlan.nodes[2].promiscuous = True

        # make a PDU from node 1 to node 2
        pdu = PDU(b'data',
            source=('192.168.6.1', 47808),
            destination=('192.168.6.2', 47808),
            )

        # node 1 sends the pdu to node 2, node 3 also gets a copy
        tnode1.start_state.send(pdu).success()
        tnode2.start_state.receive(PDU,
            pduSource=('192.168.6.1', 47808),
            ).success()
        tnode3.start_state.receive(PDU,
            pduDestination=('192.168.6.2', 47808),
            ).success()

        # run the group
        tnet.run()

    def test_promiscuous_fail(self):
        if _debug: TestVLAN._debug("test_promiscuous_fail")

        # three element network
        tnet = TNetwork(3, "192.168.7.{}/24")
        tnode1, tnode2, tnode3 = tnet.state_machines

        # make a PDU from node 1 to node 2
        pdu = PDU(b'data',
            source=('192.168.7.1', 47808),
            destination=('192.168.7.2', 47808),
            )

        # node 1 sends the pdu to node 2, node 3 waits and gets nothing
        tnode1.start_state.send(pdu).success()
        tnode2.start_state.receive(PDU,
            pduSource=('192.168.7.1', 47808),
            ).success()

        # if node 3 receives anything it will trigger unexpected receive and fail
        tnode3.start_state.timeout(1).success()

        # run the group
        tnet.run()


@bacpypes_debugging
class TestRouter(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        if _debug: TestRouter._debug("__init__ %r %r", args, kwargs)
        super(TestRouter, self).__init__(*args, **kwargs)

    def setup_method(self, method):
        """This function is called before each test method is called as is
        given a reference to the test method."""
        if _debug: TestRouter._debug("setup_method %r", method)

        # create a state machine group that has all nodes on all networks
        self.smg = StateMachineGroup()

        # make some networks
        vlan10 = IPNetwork()
        vlan20 = IPNetwork()

        # make a router and add the networks
        trouter = IPRouter()
        trouter.add_network(Address("192.168.10.1/24"), vlan10)
        trouter.add_network(Address("192.168.20.1/24"), vlan20)

        # add nodes to the networks
        for pattern, lan in (
                ("192.168.10.{}/24", vlan10),
                ("192.168.20.{}/24", vlan20),
                ):
            for i in range(2):
                node_address = Address(pattern.format(i + 2))
                node = IPNode(node_address, lan)
                if _debug: TestRouter._debug("    - node: %r", node)

                # bind a client state machine to the node
                csm = ClientStateMachine()
                bind(csm, node)

                # add it to the group
                self.smg.append(csm)

    def teardown_method(self, method):
        """This function is called after each test method has been called and
        is given a reference to the test method."""
        if _debug: TestRouter._debug("teardown_method %r", method)

        # reset the time machine
        reset_time_machine()
        if _debug: TestRouter._debug("    - time machine reset")

        # run the group
        self.smg.run()

        # run it for some time
        run_time_machine(60.0)
        if _debug: TestRouter._debug("    - time machine finished")

        # check for success
        all_success, some_failed = self.smg.check_for_success()
        assert all_success

    def test_idle(self):
        if _debug: TestRouter._debug("test_idle")

        # all successful
        for csm in self.smg.state_machines:
            csm.start_state.success()

    def test_send_receive(self):
        """Test that a node can send a message to another node on
        a different network.
        """
        if _debug: TestRouter._debug("test_send_receive")

        # unpack the state machines
        csm_10_2, csm_10_3, csm_20_2, csm_20_3 = self.smg.state_machines

        # make a PDU from network 10 node 1 to network 20 node 2
        pdu = PDU(b'data',
            source=('192.168.10.2', 47808),
            destination=('192.168.20.3', 47808),
            )
        if _debug: TestVLAN._debug("    - pdu: %r", pdu)

        # node 1 sends the pdu, mode 2 gets it
        csm_10_2.start_state.send(pdu).success()
        csm_20_3.start_state.receive(PDU,
            pduSource=('192.168.10.2', 47808),
            ).success()

        # other nodes get nothing
        csm_10_3.start_state.timeout(1).success()
        csm_20_2.start_state.timeout(1).success()

    def test_local_broadcast(self):
        """Test that a node can send a message to all of the other nodes on
        the same network.
        """
        if _debug: TestRouter._debug("test_local_broadcast")

        # unpack the state machines
        csm_10_2, csm_10_3, csm_20_2, csm_20_3 = self.smg.state_machines

        # make a broadcast PDU from network 10 node 1
        pdu = PDU(b'data',
            source=('192.168.10.2', 47808),
            destination=('192.168.10.255', 47808),
            )
        if _debug: TestVLAN._debug("    - pdu: %r", pdu)

        # node 10-2 sends the pdu, node 10-3 gets pdu, nodes 20-2 and 20-3 dont
        csm_10_2.start_state.send(pdu).success()
        csm_10_3.start_state.receive(PDU,
            pduSource=('192.168.10.2', 47808),
            ).success()
        csm_20_2.start_state.timeout(1).success()
        csm_20_3.start_state.timeout(1).success()

    def test_remote_broadcast(self):
        """Test that a node can send a message to all of the other nodes on
        a different network.
        """
        if _debug: TestRouter._debug("test_remote_broadcast")

        # unpack the state machines
        csm_10_2, csm_10_3, csm_20_2, csm_20_3 = self.smg.state_machines

        # make a PDU from network 10 node 1 to network 20 node 2
        pdu = PDU(b'data',
            source=('192.168.10.2', 47808),
            destination=('192.168.20.255', 47808),
            )
        if _debug: TestVLAN._debug("    - pdu: %r", pdu)

        # node 10-2 sends the pdu, node 10-3 gets nothing, nodes 20-2 and 20-3 get it
        csm_10_2.start_state.send(pdu).success()
        csm_10_3.start_state.timeout(1).success()
        csm_20_2.start_state.receive(PDU,
            pduSource=('192.168.10.2', 47808),
            ).success()
        csm_20_3.start_state.receive(PDU,
            pduSource=('192.168.10.2', 47808),
            ).success()

