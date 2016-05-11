#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities Server State Machine
-----------------------------------

A server state machine sits at the bottom of a stack, waits for requests,
and generates responses.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import bind

from ..state_machine import ServerStateMachine
from ..time_machine import reset_time_machine, run_time_machine
from ..trapped_classes import TrappedClient

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestServerStateMachine(unittest.TestCase):

    def test_server_state_machine(self):
        if _debug: TestServerStateMachine._debug("test_server_state_machine")

        # create a client state machine, trapped server, and bind them together
        client = TrappedClient()
        server = ServerStateMachine()
        bind(client, server)

        # make pdu object
        pdu = object()

        # make a send transition from start to success, run the machine
        server.start_state.send(pdu).success()

        # run the machine
        server.run()

        # check for success
        assert not server.running
        assert server.current_state.is_success_state

        # make sure the pdu was sent
        assert client.confirmation_received is pdu

        # check the transaction log
        assert len(server.transaction_log) == 1
        assert server.transaction_log[0][1] is pdu
