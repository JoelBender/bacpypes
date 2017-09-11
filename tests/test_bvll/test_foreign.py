#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test BVLL Foreign Devices
-------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.pdu import Address, PDU, LocalBroadcast
from bacpypes.vlan import IPNetwork, IPRouter

from ..state_machine import match_pdu, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import SnifferNode, SimpleNode, ForeignNode, BBMDNode

# some debugging
_debug = 0
_log = ModuleLogger(globals())


# extended form of xtob that first removes whitespace and period seperators
xxtob = lambda s: xtob(''.join(s.split()).replace('.', ''))


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

        # make a router
        self.router = IPRouter()

        # make a home LAN
        self.home_vlan = IPNetwork()
        self.router.add_network(Address("192.168.5.1/24"), self.home_vlan)

        # home sniffer node
        self.home_sniffer = SnifferNode("192.168.5.254/24", self.home_vlan)
        self.append(self.home_sniffer)

        # make a remote LAN
        self.remote_vlan = IPNetwork()
        self.router.add_network(Address("192.168.6.1/24"), self.remote_vlan)

        # remote sniffer node
        self.remote_sniffer = SnifferNode("192.168.6.254/24", self.remote_vlan)
        self.append(self.remote_sniffer)

        # the foreign device
        self.fd = ForeignNode("192.168.6.2/24", self.remote_vlan)
        self.append(self.fd)

        # intermediate test node
        self.tnode = SimpleNode("192.168.5.2/24", self.home_vlan)
        self.append(self.tnode)

        # bbmd
        self.bbmd = BBMDNode("192.168.5.3/24", self.home_vlan)
        self.append(self.bbmd)

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
        tnet.home_sniffer.start_state.success()
        tnet.remote_sniffer.start_state.success()
        tnet.fd.start_state.success()
        tnet.tnode.start_state.success()
        tnet.bbmd.start_state.success()

        # run the group
        tnet.run()

