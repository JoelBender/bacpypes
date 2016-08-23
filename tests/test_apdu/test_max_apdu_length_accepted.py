#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Max APDU Length Accepted
-----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestMaxAPDULengthAccepted(unittest.TestCase):

    def test_max_apdu_length_accepted_encode(self):
        if _debug: TestMaxAPDULengthAccepted._debug("test_max_apdu_length_accepted_encode")

    def test_max_apdu_length_accepted_decode(self):
        if _debug: TestMaxAPDULengthAccepted._debug("test_max_apdu_length_accepted_decode")
