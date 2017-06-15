#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities Client State Machine
-----------------------------------

A client state machine sits at the top of a stack and is used to generate
requests and match responses.
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import bind

from ..state_machine import ClientStateMachine
from ..time_machine import reset_time_machine, run_time_machine
from ..trapped_classes import TrappedServer

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestClientStateMachine(unittest.TestCase):

    def test_client_state_machine(self):
        if _debug: TestClientStateMachine._debug("test_client_state_machine")

        # create a client state machine, trapped server, and bind them together
        client = ClientStateMachine()
        server = TrappedServer()
        bind(client, server)

        # make pdu object
        pdu = object()

        # make a send transition from start to success, run the machine
        client.start_state.send(pdu).success()

        # run the machine
        client.run()

        # check for success
        assert not client.running
        assert client.current_state.is_success_state

        # make sure the pdu was sent
        assert server.indication_received is pdu

        # check the transaction log
        assert len(client.transaction_log) == 1
        assert client.transaction_log[0][1] is pdu
