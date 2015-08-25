#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Trapped State Machine Classes
-----------------------------
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import Client, Server
from ..state_machine import State, StateMachine

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
        State.__init__(self, *args, **kwargs)

        # reset to initialize
        self.reset()

    def reset(self):
        if _debug: TrappedState._debug("reset")

        # flush the copies
        self.before_send_pdu = None
        self.after_send_pdu = None
        self.before_receive_pdu = None
        self.after_receive_pdu = None
        self.unexpected_receive_pdu = None

        # continue
        State.reset(self)

    def before_send(self, pdu):
        """Called before each PDU about to be sent."""
        if _debug: TrappedState._debug("before_send %r", pdu)

        # keep a copy
        self.before_send_pdu = pdu

        # continue
        State.before_send(self, pdu)

    def after_send(self, pdu):
        """Called after each PDU sent."""
        if _debug: TrappedState._debug("after_send %r", pdu)

        # keep a copy
        self.after_send_pdu = pdu

        # continue
        State.after_send(self, pdu)

    def before_receive(self, pdu):
        """Called with each PDU received before matching."""
        if _debug: TrappedState._debug("before_receive %r", pdu)

        # keep a copy
        self.before_receive_pdu = pdu

        # continue
        State.before_receive(self, pdu)

    def after_receive(self, pdu):
        """Called with PDU received after match."""
        if _debug: TrappedState._debug("after_receive %r", pdu)

        # keep a copy
        self.after_receive_pdu = pdu

        # continue
        State.after_receive(self, pdu)

    def unexpected_receive(self, pdu):
        """Called with PDU that did not match.  Unless this is trapped by the
        state, the default behaviour is to fail."""
        if _debug: TrappedState._debug("unexpected_receive %r", pdu)

        # keep a copy
        self.unexpected_receive_pdu = pdu

        # continue
        State.unexpected_receive(self, pdu)


@bacpypes_debugging
class TrappedStateMachine(StateMachine):

    """
    This class is a simple wrapper around the StateMachine class that keeps the
    latest copy of the pdu parameter in the before_send(), after_send(),
    before_receive(), after_receive() and unexpected_receive() calls.

    It also provides a send() function, so when the machine runs it doesn't
    throw an exception.
    """

    def __init__(self, *args, **kwargs):
        if _debug: TrappedStateMachine._debug("__init__ %r %r", args, kwargs)
        StateMachine.__init__(self, *args, **kwargs)

        # reset to initialize
        self.reset()

    def reset(self):
        if _debug: TrappedStateMachine._debug("reset")

        # flush the copies
        self.before_send_pdu = None
        self.after_send_pdu = None
        self.before_receive_pdu = None
        self.after_receive_pdu = None
        self.unexpected_receive_pdu = None

        # continue
        StateMachine.reset(self)

    def before_send(self, pdu):
        """Called before each PDU about to be sent."""
        if _debug: TrappedStateMachine._debug("before_send %r", pdu)

        # keep a copy
        self.before_send_pdu = pdu

        # continue
        StateMachine.before_send(self, pdu)

    def after_send(self, pdu):
        """Called after each PDU sent."""
        if _debug: TrappedStateMachine._debug("after_send %r", pdu)

        # keep a copy
        self.after_send_pdu = pdu

        # continue
        StateMachine.after_send(self, pdu)

    def before_receive(self, pdu):
        """Called with each PDU received before matching."""
        if _debug: TrappedStateMachine._debug("before_receive %r", pdu)

        # keep a copy
        self.before_receive_pdu = pdu

        # continue
        StateMachine.before_receive(self, pdu)

    def after_receive(self, pdu):
        """Called with PDU received after match."""
        if _debug: TrappedStateMachine._debug("after_receive %r", pdu)

        # keep a copy
        self.after_receive_pdu = pdu

        # continue
        StateMachine.after_receive(self, pdu)

    def unexpected_receive(self, pdu):
        """Called with PDU that did not match.  Unless this is trapped by the
        state, the default behavior is to fail."""
        if _debug: TrappedStateMachine._debug("unexpected_receive %r", pdu)

        # keep a copy
        self.unexpected_receive_pdu = pdu

        # continue
        StateMachine.unexpected_receive(self, pdu)

    def send(self, pdu):
        """Called to send a PDU.
        """
        if _debug: TrappedStateMachine._debug("unexpected_receive %r", pdu)

        # keep a copy
        self.sent = pdu

    def match_pdu(self, pdu, transition_pdu):
        """Very strong match condition."""
        if _debug: TrappedStateMachine._debug("match_pdu %r %r", pdu, transition_pdu)

        # must be identical objects
        return pdu is transition_pdu

#
#   TrappedClient
#


class TrappedClient(Client):

    """
    TrappedClient
    ~~~~~~~~~~~~~

    An instance of this class sits at the top of a stack.
    """

    def __init__(self):
        if _debug: TrappedClient._debug("__init__")
        Client.__init__(self)

        # clear out some references
        self.request_sent = None
        self.confirmation_received = None

    def request(self, pdu):
        if _debug: TrappedClient._debug("request %r", pdu)

        # a reference for checking
        self.request_sent = pdu

        # continue with regular processing
        Client.request(self, pdu)

    def confirmation(self, pdu):
        if _debug: TrappedClient._debug("confirmation %r", pdu)

        # a reference for checking
        self.confirmation_received = pdu

bacpypes_debugging(TrappedClient)


#
#   TrappedServer
#


class TrappedServer(Server):

    """
    TrappedServer
    ~~~~~~~~~~~~~

    An instance of this class sits at the bottom of a stack.
    """

    def __init__(self):
        if _debug: TrappedServer._debug("__init__")
        Server.__init__(self)

        # clear out some references
        self.indication_received = None
        self.response_sent = None

    def indication(self, pdu):
        if _debug: TrappedServer._debug("indication %r", pdu)

        # a reference for checking
        self.indication_received = pdu

    def response(self, pdu):
        if _debug: TrappedServer._debug("response %r", pdu)

        # a reference for checking
        self.response_sent = pdu

        # continue with processing
        Server.response(self, pdu)

bacpypes_debugging(TrappedServer)
