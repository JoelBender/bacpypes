#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test PDU Address
---------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, btox, xtob
from bacpypes.pdu import Address, LocalStation, RemoteStation, \
        LocalBroadcast, RemoteBroadcast, GlobalBroadcast

# some debugging
_debug = 0
_log = ModuleLogger(globals())


class TestAddress(unittest.TestCase):

    def assertMatch(self, addr, t, n, l, a):
        assert addr.addrType == t
        assert addr.addrNet == n
        assert addr.addrLen == l
        assert addr.addrAddr == (a and xtob(a))

    def test_address(self):
        if _debug: TestAddress._debug("test_address")

    def test_local_station(self):
        if _debug: TestAddress._debug("test_local_station")

        # one parameter
        with self.assertRaises(TypeError):
            LocalStation()

        # test integer
        test_addr = LocalStation(1)
        self.assertMatch(test_addr, 2, None, 1, '01')
        assert str(test_addr) == "1"

        test_addr = LocalStation(254)
        self.assertMatch(test_addr, 2, None, 1, 'fe')
        assert str(test_addr) == "254"

        # test bad integer
        with self.assertRaises(ValueError):
            LocalStation(-1)
            LocalStation(256)

        # test bytes
        test_addr = LocalStation(xtob('01'))
        self.assertMatch(test_addr, 2, None, 1, '01')
        assert str(test_addr) == "1"

        test_addr = LocalStation(xtob('fe'))
        self.assertMatch(test_addr, 2, None, 1, 'fe')
        assert str(test_addr) == "254"

        # multi-byte strings are hex encoded
        test_addr = LocalStation(xtob('0102'))
        self.assertMatch(test_addr, 2, None, 2, '0102')
        assert str(test_addr) == "0x0102"

        test_addr = LocalStation(xtob('010203'))
        self.assertMatch(test_addr, 2, None, 3, '010203')
        assert str(test_addr) == "0x010203"

        # match with an IPv4 address
        test_addr = LocalStation(xtob('01020304bac0'))
        self.assertMatch(test_addr, 2, None, 6, '01020304bac0')
        assert str(test_addr) == "1.2.3.4"

    def test_remote_station(self):
        if _debug: TestAddress._debug("test_remote_station")

    def test_local_broadcast(self):
        if _debug: TestAddress._debug("test_local_broadcast")

        test_addr = LocalBroadcast()
        self.assertMatch(test_addr, 1, None, None, None)
        assert str(test_addr) == "*"

    def test_remote_broadcast(self):
        if _debug: TestAddress._debug("test_remote_broadcast")

    def test_global_broadcast(self):
        if _debug: TestAddress._debug("test_global_broadcast")

        test_addr = GlobalBroadcast()
        self.assertMatch(test_addr, 5, None, None, None)
        assert str(test_addr) == "*:*"

bacpypes_debugging(TestAddress)
