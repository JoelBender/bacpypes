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
from bacpypes.bvll import ReadForeignDeviceTable, ReadForeignDeviceTableAck

from ..state_machine import StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine

from .helpers import SnifferNode, CodecNode, SimpleNode, ForeignNode, BBMDNode

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

        # make a remote LAN
        self.remote_vlan = IPNetwork()
        self.router.add_network(Address("192.168.6.1/24"), self.remote_vlan)

        # the foreign device
        self.fd = ForeignNode("192.168.6.2/24", self.remote_vlan)
        self.append(self.fd)

        # bbmd
        self.bbmd = BBMDNode("192.168.5.3/24", self.home_vlan)
        self.append(self.bbmd)

    def run(self, time_limit=60.0):
        if _debug: TNetwork._debug("run %r", time_limit)

        # run the group
        super(TNetwork, self).run()

        # run it for some time
        run_time_machine(time_limit)
        if _debug: TNetwork._debug("    - time machine finished")

        # check for success
        all_success, some_failed = super(TNetwork, self).check_for_success()
        assert all_success


@bacpypes_debugging
class TestForeign(unittest.TestCase):

    def test_idle(self):
        """Test an idle network, nothing happens is success."""
        if _debug: TestForeign._debug("test_idle")

        # create a network
        tnet = TNetwork()

        # all start states are successful
        tnet.fd.start_state.success()
        tnet.bbmd.start_state.success()

        # run the group
        tnet.run()

    def test_registration(self):
        """Test foreign device registration."""
        if _debug: TestForeign._debug("test_registration")

        # create a network
        tnet = TNetwork()

        # add an addition codec node to the home vlan
        cnode = CodecNode("192.168.5.2/24", tnet.home_vlan)
        tnet.append(cnode)

        # home sniffer node
        home_sniffer = SnifferNode("192.168.5.254/24", tnet.home_vlan)
        tnet.append(home_sniffer)

        # remote sniffer node
        remote_sniffer = SnifferNode("192.168.6.254/24", tnet.remote_vlan)
        tnet.append(remote_sniffer)

        # tell the B/IP layer of the foreign device to register
        tnet.fd.start_state \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 30) \
            .success()

        # sniffer pieces
        registration_request = xxtob('81.05.0006'   # bvlci
            '001e'                                  # time-to-live
            )
        registration_ack = xxtob('81.00.0006.0000') # simple ack

        # remote sniffer sees registration
        remote_sniffer.start_state.doc("1-1-0") \
            .receive(PDU, pduData=registration_request).doc("1-1-1") \
            .receive(PDU, pduData=registration_ack).doc("1-1-2") \
            .set_event('fd-registered').doc("1-1-3") \
            .success()

        # the bbmd is idle
        tnet.bbmd.start_state.success()

        # read the FDT
        cnode.start_state.doc("1-2-0") \
            .wait_event('fd-registered').doc("1-2-1") \
            .send(ReadForeignDeviceTable(destination=tnet.bbmd.address)).doc("1-2-2") \
            .receive(ReadForeignDeviceTableAck).doc("1-2-3") \
            .success()

        # the tnode reads the registration table
        read_fdt_request = xxtob('81.06.0004')      # bvlci
        read_fdt_ack = xxtob('81.07.000e'           # read-ack
            'c0.a8.06.02.ba.c0 001e 0023'           # address, ttl, remaining
            )

        # home sniffer sees registration
        home_sniffer.start_state.doc("1-3-0") \
            .receive(PDU, pduData=registration_request).doc("1-3-1") \
            .receive(PDU, pduData=registration_ack).doc("1-3-2") \
            .receive(PDU, pduData=read_fdt_request).doc("1-3-3") \
            .receive(PDU, pduData=read_fdt_ack).doc("1-3-4") \
            .success()

        # run the group
        tnet.run()

    def test_refresh_registration(self):
        """Test refreshing foreign device registration."""
        if _debug: TestForeign._debug("test_refresh_registration")

        # create a network
        tnet = TNetwork()

        # tell the B/IP layer of the foreign device to register
        tnet.fd.start_state \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 10) \
            .success()

        # the bbmd is idle
        tnet.bbmd.start_state.success()

        # remote sniffer node
        remote_sniffer = SnifferNode("192.168.6.254/24", tnet.remote_vlan)
        tnet.append(remote_sniffer)

        # sniffer pieces
        registration_request = xxtob('81.05.0006'   # bvlci
            '000a'                                  # time-to-live
            )
        registration_ack = xxtob('81.00.0006.0000') # simple ack

        # remote sniffer sees registration
        remote_sniffer.start_state.doc("2-1-0") \
            .receive(PDU, pduData=registration_request).doc("2-1-1") \
            .receive(PDU, pduData=registration_ack).doc("2-1-2") \
            .receive(PDU, pduData=registration_request).doc("2-1-3") \
            .receive(PDU, pduData=registration_ack).doc("2-1-4") \
            .success()

        # run the group
        tnet.run()

    def test_unicast(self):
        """Test a unicast message from the foreign device to the bbmd."""
        if _debug: TestForeign._debug("test_unicast")

        # create a network
        tnet = TNetwork()

        # make a PDU from node 1 to node 2
        pdu_data = xxtob('dead.beef')
        pdu = PDU(pdu_data, source=tnet.fd.address, destination=tnet.bbmd.address)
        if _debug: TestForeign._debug("    - pdu: %r", pdu)

        # register, wait for ack, send some beef
        tnet.fd.start_state.doc("3-1-0") \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 60).doc("3-1-1") \
            .wait_event('fd-registered').doc("3-1-2") \
            .send(pdu).doc("3-1-3") \
            .success()

        # the bbmd is happy when it gets the pdu
        tnet.bbmd.start_state \
            .receive(PDU, pduSource=tnet.fd.address, pduData=pdu_data) \
            .success()

        # remote sniffer node
        remote_sniffer = SnifferNode("192.168.6.254/24", tnet.remote_vlan)
        tnet.append(remote_sniffer)

        # sniffer pieces
        registration_request = xxtob('81.05.0006'   # bvlci
            '003c'                                  # time-to-live (60)
            )
        registration_ack = xxtob('81.00.0006.0000') # simple ack
        unicast_pdu = xxtob('81.0a.0008'            # original unicast bvlci
            'dead.beef'                             # PDU being unicast
            )

        # remote sniffer sees registration
        remote_sniffer.start_state.doc("3-2-0") \
            .receive(PDU, pduData=registration_request).doc("3-2-1") \
            .receive(PDU, pduData=registration_ack).doc("3-2-2") \
            .set_event('fd-registered').doc("3-2-3") \
            .receive(PDU, pduData=unicast_pdu).doc("3-2-4") \
            .success()

        # run the group
        tnet.run()

    def test_broadcast(self):
        """Test a broadcast message from the foreign device to the bbmd."""
        if _debug: TestForeign._debug("test_broadcast")

        # create a network
        tnet = TNetwork()

        # make a broadcast pdu
        pdu_data = xxtob('dead.beef')
        pdu = PDU(pdu_data, destination=LocalBroadcast())
        if _debug: TestForeign._debug("    - pdu: %r", pdu)

        # register, wait for ack, send some beef
        tnet.fd.start_state.doc("4-1-0") \
            .call(tnet.fd.bip.register, tnet.bbmd.address, 60).doc("4-1-1") \
            .wait_event('4-registered').doc("4-1-2") \
            .send(pdu).doc("4-1-3") \
            .success()

        # the bbmd is happy when it gets the pdu
        tnet.bbmd.start_state \
            .receive(PDU, pduSource=tnet.fd.address, pduData=pdu_data) \
            .success()

        # home sniffer node
        home_node = SimpleNode("192.168.5.254/24", tnet.home_vlan)
        tnet.append(home_node)

        # home node happy when getting the pdu, broadcast by the bbmd
        home_node.start_state.doc("4-2-0") \
            .receive(PDU, pduSource=tnet.fd.address, pduData=pdu_data).doc("4-2-1") \
            .success()

        # remote sniffer node
        remote_sniffer = SnifferNode("192.168.6.254/24", tnet.remote_vlan)
        tnet.append(remote_sniffer)

        # sniffer pieces
        registration_request = xxtob('81.05.0006'   # bvlci
            '003c'                                  # time-to-live (60)
            )
        registration_ack = xxtob('81.00.0006.0000') # simple ack
        distribute_pdu = xxtob('81.09.0008'         # bvlci
            'deadbeef'                              # PDU to broadcast
            )

        # remote sniffer sees registration
        remote_sniffer.start_state.doc("4-3-0") \
            .receive(PDU, pduData=registration_request).doc("4-3-1") \
            .receive(PDU, pduData=registration_ack).doc("4-3-2") \
            .set_event('4-registered') \
            .receive(PDU, pduData=distribute_pdu).doc("4-3-3") \
            .success()

        # run the group
        tnet.run(4.0)

