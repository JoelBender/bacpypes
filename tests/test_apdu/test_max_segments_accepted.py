#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Max Segments Accepted
--------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.apdu import encode_max_segments_accepted, decode_max_segments_accepted

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestMaxSegmentsAccepted(unittest.TestCase):

    def test_max_segments_accepted_encode(self):
        if _debug: TestMaxSegmentsAccepted._debug("test_max_segments_accepted_encode")

        assert encode_max_segments_accepted(None) == 0
        assert encode_max_segments_accepted(2) == 1

    def test_max_segments_accepted_decode(self):
        if _debug: TestMaxSegmentsAccepted._debug("test_max_segments_accepted_decode")

        assert decode_max_segments_accepted(0) == None
        assert decode_max_segments_accepted(1) == 2
