#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test BVLL Simple Devices
------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.pdu import PDU, LocalBroadcast
from bacpypes.bvll import OriginalUnicastNPDU, OriginalBroadcastNPDU
from bacpypes.vlan import IPNetwork

from ..state_machine import match_pdu, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import (
    SnifferStateMachine, BIPSimpleStateMachine,
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

        # make a little LAN
        self.vlan = IPNetwork()

        # test device
        self.td = BIPSimpleStateMachine("192.168.4.1/24", self.vlan)
        self.append(self.td)

        # implementation under test
        self.iut = BIPSimpleStateMachine("192.168.4.2/24", self.vlan)
        self.append(self.iut)

        # sniffer node
        self.sniffer = SnifferStateMachine("192.168.4.254/24", self.vlan)
        self.append(self.sniffer)


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
        tnet.iut.start_state.success()
        tnet.sniffer.start_state.success()

        # run the group
        tnet.run()

    def test_unicast(self):
        """Test a unicast message from TD to IUT."""
        if _debug: TestSimple._debug("test_unicast")

        # create a network
        tnet = TNetwork()

        # make a PDU from node 1 to node 2
        pdu_data = xtob('dead.beef')
        pdu = PDU(pdu_data, source=tnet.td.address, destination=tnet.iut.address)
        if _debug: TestSimple._debug("    - pdu: %r", pdu)

        # test device sends it, iut gets it
        tnet.td.start_state.send(pdu).success()
        tnet.iut.start_state.receive(PDU, pduSource=tnet.td.address).success()

        # sniffer sees message on the wire
        tnet.sniffer.start_state.receive(OriginalUnicastNPDU,
            pduSource=tnet.td.address.addrTuple, 
            pduDestination=tnet.iut.address.addrTuple,
            pduData=pdu_data,
            ).timeout(1.0).success()

        # run the group
        tnet.run()

    def test_broadcast(self):
        """Test a broadcast message from TD to IUT."""
        if _debug: TestSimple._debug("test_broadcast")

        # create a network
        tnet = TNetwork()

        # make a PDU from node 1 to node 2
        pdu_data = xtob('dead.beef')
        pdu = PDU(pdu_data, source=tnet.td.address, destination=LocalBroadcast())
        if _debug: TestSimple._debug("    - pdu: %r", pdu)

        # test device sends it, iut gets it
        tnet.td.start_state.send(pdu).success()
        tnet.iut.start_state.receive(PDU, pduSource=tnet.td.address).success()

        # sniffer sees message on the wire
        tnet.sniffer.start_state.receive(OriginalBroadcastNPDU,
            pduSource=tnet.td.address.addrTuple,
#           pduDestination=('192.168.4.255', 47808),
            pduData=pdu_data,
            ).timeout(1.0).success()

        # run the group
        tnet.run()

