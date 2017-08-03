#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Network
------------

This module tests the basic functionality of a VLAN network.  Each test "runs"
on a VLAN with two nodes, node_1 and node_2, and each has a state machine.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address, PDU
from bacpypes.comm import bind
from bacpypes.vlan import Network, Node

from ..state_machine import ClientStateMachine, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class ZPDU():

    def __init__(self, cls=None, **kwargs):
        if _debug: ZPDU._debug("__init__ %r", kwargs)

        self.cls = cls
        self.kwargs = kwargs

    def __eq__(self, pdu):
        if _debug: ZPDU._debug("__eq__ %r", pdu)

        # match the object type if it was provided
        if self.cls is not None:
            if not isinstance(pdu, self.cls):
                if _debug: ZPDU._debug("    - wrong class")
                return False

        # match the attribute names and values
        for k, v in self.kwargs.items():
            if not hasattr(pdu, k):
                if _debug: ZPDU._debug("    - missing attribute: %r", k)
                return False
            if getattr(pdu, k) != v:
                if _debug: ZPDU._debug("    - %s value: %r", k, v)
                return False

        # nothing failed
        return True


@bacpypes_debugging
class ZStateMachineGroup(StateMachineGroup):

    def run(self, time_limit=60.0):
        if _debug: ZStateMachineGroup._debug("run %r", time_limit)

        # reset the time machine
        reset_time_machine()
        if _debug: ZStateMachineGroup._debug("    - time machine reset")

        # run the group
        super(ZStateMachineGroup, self).run()

        # run it for some time
        run_time_machine(time_limit)
        if _debug: ZStateMachineGroup._debug("    - time machine finished")

        # check for success
        all_success, some_failed = super(ZStateMachineGroup, self).check_for_success()
        assert all_success


@bacpypes_debugging
class TestVLAN(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        if _debug: TestVLAN._debug("__init__ %r %r", args, kwargs)
        super(TestVLAN, self).__init__(*args, **kwargs)

        # create a network and bound nodes
        self.vlan = Network()
        self.node_1 = Node(Address(1), self.vlan)
        self.node_2 = Node(Address(2), self.vlan)

        # create state machines and bind them to nodes
        self.csm_1 = ClientStateMachine()
        bind(self.csm_1, self.node_1)
        self.csm_2 = ClientStateMachine()
        bind(self.csm_2, self.node_2)

        # create a state machine group so they both run together
        self.csm_group = ZStateMachineGroup()
        self.csm_group.append(self.csm_1)
        self.csm_group.append(self.csm_2)

    def test_idle(self):
        if _debug: TestVLAN._debug("test_idle")

        # make a send transition from start to success, run the machine
        self.csm_1.start_state.success()
        self.csm_2.start_state.success()

        # run the group
        self.csm_group.run()

    def test_send_receive(self):
        if _debug: TestVLAN._debug("test_send_receive")

        # make a PDU from node 1 to node 2
        pdu = PDU(b'data', source=self.node_1.address, destination=self.node_2.address)
        if _debug: TestVLAN._debug("    - pdu: %r", pdu)

        # make a send transition from start to success, run the machine
        self.csm_1.start_state.send(pdu).success()
        self.csm_2.start_state.receive(ZPDU(
            pduSource=Address(1),
            )).success()

        # run the group
        self.csm_group.run()

