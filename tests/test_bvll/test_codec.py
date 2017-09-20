#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test BVLL Encoding and Decoding
-------------------------------
"""

import string
import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, btox, xtob

from bacpypes.comm import bind
from bacpypes.pdu import PDU, Address, LocalBroadcast

from bacpypes.bvll import Result, WriteBroadcastDistributionTable, \
    ReadBroadcastDistributionTable, ReadBroadcastDistributionTableAck, \
    ForwardedNPDU, RegisterForeignDevice, ReadForeignDeviceTable, \
    ReadForeignDeviceTableAck, FDTEntry, DeleteForeignDeviceTableEntry, \
    DistributeBroadcastToNetwork, OriginalUnicastNPDU, \
    OriginalBroadcastNPDU
from bacpypes.bvllservice import AnnexJCodec

from ..trapped_classes import TrappedClient, TrappedServer
from ..state_machine import match_pdu

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestAnnexJCodec(unittest.TestCase):

    def setup_method(self, method):
        """This function is called before each test method is called as is
        given a reference to the test method."""
        if _debug: TestAnnexJCodec._debug("setup_method %r", method)

        # minature trapped stack
        self.client = TrappedClient()
        self.codec = AnnexJCodec()
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

    def test_result(self):
        """Test the Result encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_codec_01")

        # Request successful
        pdu_bytes = xtob('81.00.0006.0000')

        self.request(Result(0))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(Result, bvlciResultCode=0)

        # Request error condition
        pdu_bytes = xtob('81.00.0006.0001')

        self.request(Result(1))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(Result, bvlciResultCode=1)

    def test_write_broadcast_distribution_table(self):
        """Test the WriteBroadcastDistributionTable encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_write_broadcast_distribution_table")

        # write an empty table
        pdu_bytes = xtob('81.01.0004')

        self.request(WriteBroadcastDistributionTable([]))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(WriteBroadcastDistributionTable, bvlciBDT=[])

        # write a table with an element
        addr = Address('192.168.0.254/24')
        pdu_bytes = xtob('81.01.000e'
            'c0.a8.00.fe.ba.c0 ff.ff.ff.00'     # address and mask
            )

        self.request(WriteBroadcastDistributionTable([addr]))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(WriteBroadcastDistributionTable, bvlciBDT=[addr])

    def test_read_broadcast_distribution_table(self):
        """Test the ReadBroadcastDistributionTable encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_read_broadcast_distribution_table")

        # read the table
        pdu_bytes = xtob('81.02.0004')

        self.request(ReadBroadcastDistributionTable())
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ReadBroadcastDistributionTable)

    def test_read_broadcast_distribution_table_ack(self):
        """Test the ReadBroadcastDistributionTableAck encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_read_broadcast_distribution_table_ack")

        # read returns an empty table
        pdu_bytes = xtob('81.03.0004')

        self.request(ReadBroadcastDistributionTableAck([]))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ReadBroadcastDistributionTableAck, bvlciBDT=[])

        # read returns a table with an element
        addr = Address('192.168.0.254/24')
        pdu_bytes = xtob('81.03.000e'          # bvlci
            'c0.a8.00.fe.ba.c0 ff.ff.ff.00'     # address and mask
            )

        self.request(ReadBroadcastDistributionTableAck([addr]))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ReadBroadcastDistributionTableAck, bvlciBDT=[addr])

    def test_forwarded_npdu(self):
        """Test the ForwardedNPDU encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_forwarded_npdu")

        # read returns a table with an element
        addr = Address('192.168.0.1')
        xpdu = xtob('deadbeef')
        pdu_bytes = xtob('81.04.000e'  # bvlci
            'c0.a8.00.01.ba.c0'         # original source address
            'deadbeef'                  # forwarded PDU
            )

        self.request(ForwardedNPDU(addr, xpdu))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ForwardedNPDU, bvlciAddress=addr, pduData=xpdu)

    def test_register_foreign_device(self):
        """Test the RegisterForeignDevice encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_register_foreign_device")

        # register as a foreign device with a 30 second time-to-live
        pdu_bytes = xtob('81.05.0006'  # bvlci
            '001e'                      # time-to-live
            )

        self.request(RegisterForeignDevice(30))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(RegisterForeignDevice, bvlciTimeToLive=30)

    def test_read_foreign_device_table(self):
        """Test the ReadForeignDeviceTable encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_read_foreign_device_table")

        # read returns an empty table
        pdu_bytes = xtob('81.06.0004')

        self.request(ReadForeignDeviceTable())
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ReadForeignDeviceTable)

    def test_read_foreign_device_table_ack(self):
        """Test the ReadForeignDeviceTableAck encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_read_foreign_device_table_ack")

        # read returns an empty table
        pdu_bytes = xtob('81.07.0004')

        self.request(ReadForeignDeviceTableAck([]))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ReadForeignDeviceTableAck, bvlciFDT=[])

        # read returns a table with one entry
        fdte = FDTEntry()
        fdte.fdAddress = Address("192.168.0.10")
        fdte.fdTTL = 30
        fdte.fdRemain = 15
        pdu_bytes = xtob('81.07.000e'  # bvlci
            'c0.a8.00.0a.ba.c0'         # address
            '001e.000f'                 # ttl and remaining
            )

        self.request(ReadForeignDeviceTableAck([fdte]))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(ReadForeignDeviceTableAck, bvlciFDT=[fdte])

    def test_delete_foreign_device_table_entry(self):
        """Test the DeleteForeignDeviceTableEntry encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_delete_foreign_device_table_entry")

        # delete an element
        addr = Address('192.168.0.11/24')
        pdu_bytes = xtob('81.08.000a'  # bvlci
            'c0.a8.00.0b.ba.c0'         # address of entry to be deleted
            )

        self.request(DeleteForeignDeviceTableEntry(addr))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(DeleteForeignDeviceTableEntry, bvlciAddress=addr)

    def test_distribute_broadcast_to_network(self):
        """Test the DistributeBroadcastToNetwork encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_distribute_broadcast_to_network")

        # read returns a table with an element
        xpdu = xtob('deadbeef')
        pdu_bytes = xtob('81.09.0008'  # bvlci
            'deadbeef'                  # PDU to broadcast
            )

        self.request(DistributeBroadcastToNetwork(xpdu))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(DistributeBroadcastToNetwork, pduData=xpdu)

    def test_original_unicast_npdu(self):
        """Test the OriginalUnicastNPDU encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_original_unicast_npdu")

        # read returns a table with an element
        xpdu = xtob('deadbeef')
        pdu_bytes = xtob('81.0a.0008'  # bvlci
            'deadbeef'                  # PDU being unicast
            )

        self.request(OriginalUnicastNPDU(xpdu))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(OriginalUnicastNPDU, pduData=xpdu)

    def test_original_broadcast_npdu(self):
        """Test the OriginalBroadcastNPDU encoding and decoding."""
        if _debug: TestAnnexJCodec._debug("test_original_broadcast_npdu")

        # read returns a table with an element
        xpdu = xtob('deadbeef')
        pdu_bytes = xtob('81.0b.0008'  # bvlci
            'deadbeef'                  # PDU being broadcast
            )

        self.request(OriginalBroadcastNPDU(xpdu))
        self.indication(pduData=pdu_bytes)

        self.response(PDU(pdu_bytes))
        self.confirmation(OriginalBroadcastNPDU, pduData=xpdu)

