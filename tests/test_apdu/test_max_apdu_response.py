#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Max APDU Response
----------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestMaxAPDUResponse(unittest.TestCase):

    def test_max_apdu_response_encode(self):
        if _debug: TestAddress._debug("test_max_apdu_response_encode")

    def test_max_apdu_response_decode(self):
        if _debug: TestAddress._debug("test_max_apdu_response_decode")
