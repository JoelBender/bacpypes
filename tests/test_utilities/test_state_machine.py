#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities State Machine
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from ..utilities import State, StateMachine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TrappedState(State):

    """
    This class is a simple wrapper around the State class that keeps the
    latest copy of the pdu parameter in the before_send(), after_send(),
    before_receive(), after_receive() and unexpected_receive() calls.
    """

    def __init__(self, *args, **kwargs):
        if _debug: TrappedState._debug("__init__ %r %r", args, kwargs)
        super(TrappedState, self).__init__(*args, **kwargs)

        # reset to initialize
        self.reset()

    def reset(self):
        if _debug: TrappedState._debug("reset")

        # flush the copies
        self._before_send_pdu = None
        self._after_send_pdu = None
        self._before_receive_pdu = None
        self._after_receive_pdu = None
        self._unexpected_receive_pdu = None

        # continue
        super(TrappedState, self).reset()

    def before_send(self, pdu):
        """Called before each PDU about to be sent."""
        if _debug: TrappedState._debug("before_send %r", pdu)

        # keep a copy
        self._before_send_pdu = pdu

        # continue
        super(TrappedState, self).before_send(pdu)

    def after_send(self, pdu):
        """Called after each PDU sent."""
        if _debug: TrappedState._debug("after_send %r", pdu)

        # keep a copy
        self._after_send_pdu = pdu

        # continue
        super(TrappedState, self).after_send(pdu)

    def before_receive(self, pdu):
        """Called with each PDU received before matching."""
        if _debug: TrappedState._debug("before_receive %r", pdu)

        # keep a copy
        self._before_receive_pdu = pdu

        # continue
        super(TrappedState, self).before_receive(pdu)

    def after_receive(self, pdu):
        """Called with PDU received after match."""
        if _debug: TrappedState._debug("after_receive %r", pdu)

        # keep a copy
        self._after_receive_pdu = pdu

        # continue
        super(TrappedState, self).after_receive(pdu)

    def unexpected_receive(self, pdu):
        """Called with PDU that did not match.  Unless this is trapped by the
        state, the default behaviour is to fail."""
        if _debug: TrappedState._debug("unexpected_receive %r", pdu)

        # keep a copy
        self._unexpected_receive_pdu = pdu

        # continue
        super(TrappedState, self).unexpected_receive(pdu)


@bacpypes_debugging
class TestState(unittest.TestCase):

    def test_state_doc(self):
        if _debug: TestState._debug("test_state_doc")

        # change the doc string
        ts = State(None)
        ns = ts.doc("test state")
        assert ts.doc_string == "test state"
        assert ns is ts

    def test_state_success(self):
        if _debug: TestState._debug("test_state_success")

        # create a state and flag it success
        ts = State(None)
        ns = ts.success()
        assert ts.is_success_state
        assert ns is ts

        with self.assertRaises(RuntimeError):
            ts.success()
        with self.assertRaises(RuntimeError):
            ts.fail()

    def test_state_fail(self):
        if _debug: TestState._debug("test_state_fail")

        # create a state and flag it fail
        ts = State(None)
        ns = ts.fail()
        assert ts.is_fail_state
        assert ns is ts

        with self.assertRaises(RuntimeError):
            ts.success()
        with self.assertRaises(RuntimeError):
            ts.fail()

    def test_something_else(self):
        if _debug: TestState._debug("test_something_else")

@bacpypes_debugging
class TestStateMachine(unittest.TestCase):

    def test_state_machine(self):
        if _debug: TestStateMachine._debug("test_state_machine")