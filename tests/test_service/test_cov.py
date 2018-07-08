#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test COV Service
----------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.service.cov import ChangeOfValueServices

from .helpers import ApplicationNetwork

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestBasic(unittest.TestCase):

    def test_basic(self):
        """Test basic configuration of a network."""
        if _debug: TestBasic._debug("test_basic")

        # create a network
        anet = ApplicationNetwork("test_basic")

        # add the service capability to the IUT
        anet.iut.add_capability(ChangeOfValueServices)

        # all start states are successful
        anet.td.start_state.success()
        anet.iut.start_state.success()

        # run the group
        anet.run()

