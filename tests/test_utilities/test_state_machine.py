#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities State Machine
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from ..state_machine import State, StateMachine, StateMachineGroup, match_pdu
from ..time_machine import reset_time_machine, run_time_machine
from ..trapped_classes import TrappedState, TrappedStateMachine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TPDU:

    def __init__(self, **kwargs):
        if _debug: TPDU._debug("__init__ %r", kwargs)

        self.__dict__.update(kwargs)

    def __repr__(self):
        return '<TPDU {}>'.format(', '.join(
            '{}={}'.format(k, v) for k,v in self.__dict__.items(),
            ))


@bacpypes_debugging
class TestMatchPDU(unittest.TestCase):

    def test_match_pdu(self):
        if _debug: TestMatchPDU._debug("test_match_pdu")

        tpdu = TPDU(x=1)
        Anon = type('Anon', (), {})
        anon = Anon()

        # no criteria passes
        assert match_pdu(tpdu)
        assert match_pdu(anon)

        # matching/not matching types
        assert match_pdu(tpdu, TPDU)
        assert not match_pdu(tpdu, Anon)
        assert match_pdu(tpdu, (TPDU, Anon))

        # matching/not matching attributes
        assert match_pdu(tpdu, x=1)
        assert not match_pdu(tpdu, x=2)
        assert not match_pdu(tpdu, y=1)
        assert not match_pdu(anon, x=1)

        # matching/not matching types and attributes
        assert match_pdu(tpdu, TPDU, x=1)
        assert not match_pdu(tpdu, TPDU, x=2)
        assert not match_pdu(tpdu, TPDU, y=1)


@bacpypes_debugging
class TestState(unittest.TestCase):

    def test_state_doc(self):
        if _debug: TestState._debug("test_state_doc")

        # change the doc string
        ts = State(None)
        ns = ts.doc("test state")
        assert ts.doc_string == "test state"
        assert ns is ts
        if _debug: TestState._debug("    - passed")

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
        if _debug: TestState._debug("    - passed")

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
        if _debug: TestState._debug("    - passed")

    def test_something_else(self):
        if _debug: TestState._debug("test_something_else")
        if _debug: TestState._debug("    - passed")


@bacpypes_debugging
class TestStateMachine(unittest.TestCase):

    def test_state_machine_run(self):
        if _debug: TestStateMachine._debug("test_state_machine_run")

        # create a state machine
        tsm = StateMachine()

        # run the machine
        tsm.run()

        # check for still running in the start state
        assert tsm.running
        assert tsm.current_state is tsm.start_state
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_success(self):
        if _debug: TestStateMachine._debug("test_state_machine_success")

        # create a trapped state machine
        tsm = TrappedStateMachine()
        assert isinstance(tsm.start_state, TrappedState)

        # make the start state a success
        tsm.start_state.success()

        # run the machine
        tsm.run()

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_fail(self):
        if _debug: TestStateMachine._debug("test_state_machine_fail")

        # create a trapped state machine
        tsm = TrappedStateMachine()
        assert isinstance(tsm.start_state, TrappedState)

        # make the start state a fail
        tsm.start_state.fail()

        # run the machine
        tsm.run()

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_fail_state
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_send(self):
        if _debug: TestStateMachine._debug("test_state_machine_send")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make pdu object
        pdu = TPDU()

        # make a send transition from start to success, run the machine
        tsm.start_state.send(pdu).success()
        tsm.run()

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state

        # check the callbacks
        assert tsm.start_state.before_send_pdu is pdu
        assert tsm.start_state.after_send_pdu is pdu
        assert tsm.before_send_pdu is pdu
        assert tsm.after_send_pdu is pdu

        # make sure the pdu was sent
        assert tsm.sent is pdu

        # check the transaction log
        assert len(tsm.transaction_log) == 1
        assert tsm.transaction_log[0][1] is pdu
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_receive(self):
        if _debug: TestStateMachine._debug("test_state_machine_receive")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make pdu object
        pdu = TPDU()

        # make a receive transition from start to success, run the machine
        tsm.start_state.receive(TPDU).success()
        tsm.run()

        # check for still running
        assert tsm.running

        # tell the machine it is receiving the pdu
        tsm.receive(pdu)

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state

        # check the callbacks
        assert tsm.start_state.before_receive_pdu is pdu
        assert tsm.start_state.after_receive_pdu is pdu
        assert tsm.before_receive_pdu is pdu
        assert tsm.after_receive_pdu is pdu

        # check the transaction log
        assert len(tsm.transaction_log) == 1
        assert tsm.transaction_log[0][1] is pdu
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_unexpected(self):
        if _debug: TestStateMachine._debug("test_state_machine_unexpected")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make pdu object
        good_pdu = TPDU(a=1)
        bad_pdu = TPDU(b=2)

        # make a receive transition from start to success, run the machine
        tsm.start_state.receive(TPDU, a=1).success()
        tsm.run()

        # check for still running
        assert tsm.running

        # give the machine a bad pdu
        tsm.receive(bad_pdu)

        # check for fail
        assert not tsm.running
        assert tsm.current_state.is_fail_state
        assert tsm.current_state is tsm.unexpected_receive_state

        # check the callback
        assert tsm.unexpected_receive_pdu is bad_pdu

        # check the transaction log
        assert len(tsm.transaction_log) == 1
        assert tsm.transaction_log[0][1] is bad_pdu
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_call(self):
        if _debug: TestStateMachine._debug("test_state_machine_call")

        # simple hook
        self._called = False

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make a send transition from start to success, run the machine
        tsm.start_state.call(setattr, self, '_called', True).success()
        tsm.run()

        # check for success
        assert not tsm.running
        assert tsm.is_success_state

        # check for the call
        assert self._called

    def test_state_machine_call_exception(self):
        if _debug: TestStateMachine._debug("test_state_machine_call_exception")

        # simple hook
        self._called = False

        def fn():
            self._called = True
            raise AssertionError("error")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make a send transition from start to success, run the machine
        tsm.start_state.call(fn).success()
        tsm.run()

        # check for failed call
        assert not tsm.running
        assert tsm.is_fail_state

        # check for the call
        assert self._called

    def test_state_machine_loop_01(self):
        if _debug: TestStateMachine._debug("test_state_machine_loop_01")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make pdu object
        first_pdu = TPDU(a=1)
        if _debug: TestStateMachine._debug("    - first_pdu: %r", first_pdu)
        second_pdu = TPDU(a=2)
        if _debug: TestStateMachine._debug("    - second_pdu: %r", second_pdu)

        # after sending the first pdu, wait for the second
        s0 = tsm.start_state
        s1 = s0.send(first_pdu)
        s2 = s1.receive(TPDU, a=2)
        s2.success()

        # run the machine
        tsm.run()

        # check for still running and waiting
        assert tsm.running
        assert tsm.current_state is s1
        if _debug: TestStateMachine._debug("    - still running and waiting")

        # give the machine the second pdu
        tsm.receive(second_pdu)

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state
        if _debug: TestStateMachine._debug("    - success")

        # check the callbacks
        assert s0.before_send_pdu is first_pdu
        assert s0.after_send_pdu is first_pdu
        assert s1.before_receive_pdu is second_pdu
        assert s1.after_receive_pdu is second_pdu
        if _debug: TestStateMachine._debug("    - callbacks passed")

        # check the transaction log
        assert len(tsm.transaction_log) == 2
        assert tsm.transaction_log[0][1] is first_pdu
        assert tsm.transaction_log[1][1] is second_pdu
        if _debug: TestStateMachine._debug("    - transaction log passed")

    def test_state_machine_loop_02(self):
        if _debug: TestStateMachine._debug("test_state_machine_loop_02")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make pdu object
        first_pdu = TPDU(a=1)
        second_pdu = TPDU(a=2)

        # when the first pdu is received, send the second
        s0 = tsm.start_state
        s1 = s0.receive(TPDU, a=1)
        s2 = s1.send(second_pdu)
        s2.success()

        # run the machine
        tsm.run()

        # check for still running
        assert tsm.running
        if _debug: TestStateMachine._debug("    - still running")

        # give the machine the first pdu
        tsm.receive(first_pdu)

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state
        if _debug: TestStateMachine._debug("    - success")

        # check the callbacks
        assert s0.before_receive_pdu is first_pdu
        assert s0.after_receive_pdu is first_pdu
        assert s1.before_send_pdu is second_pdu
        assert s1.after_send_pdu is second_pdu
        if _debug: TestStateMachine._debug("    - callbacks passed")

        # check the transaction log
        assert len(tsm.transaction_log) == 2
        assert tsm.transaction_log[0][1] is first_pdu
        assert tsm.transaction_log[1][1] is second_pdu
        if _debug: TestStateMachine._debug("    - transaction log passed")


@bacpypes_debugging
class TestStateMachineTimeout1(unittest.TestCase):

    def test_state_machine_timeout_1(self):
        if _debug: TestStateMachineTimeout1._debug("test_state_machine_timeout_1")

        # create a trapped state machine
        tsm = TrappedStateMachine()

        # make a timeout transition from start to success
        tsm.start_state.timeout(1.0).success()

        reset_time_machine()
        if _debug: TestStateMachineTimeout1._debug("    - time machine reset")

        tsm.run()

        run_time_machine(60.0)
        if _debug: TestStateMachineTimeout1._debug("    - time machine finished")

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state
        if _debug: TestStateMachine._debug("    - passed")


@bacpypes_debugging
class TestStateMachineTimeout2(unittest.TestCase):

    def test_state_machine_timeout_2(self):
        if _debug: TestStateMachineTimeout2._debug("test_state_machine_timeout_2")

        # make some pdu's
        first_pdu = TPDU(a=1)
        second_pdu = TPDU(a=2)

        # create a trapped state machine
        tsm = TrappedStateMachine()
        s0 = tsm.start_state

        # send something, wait, send something, wait, success
        s1 = s0.send(first_pdu)
        s2 = s1.timeout(1.0)
        s3 = s2.send(second_pdu)
        s4 = s3.timeout(1.0).success()

        reset_time_machine()
        if _debug: TestStateMachineTimeout2._debug("    - time machine reset")

        tsm.run()

        run_time_machine(60.0)
        if _debug: TestStateMachineTimeout2._debug("    - time machine finished")

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state

        # check the transaction log
        assert len(tsm.transaction_log) == 2
        assert tsm.transaction_log[0][1] is first_pdu
        assert tsm.transaction_log[1][1] is second_pdu
        if _debug: TestStateMachine._debug("    - passed")


@bacpypes_debugging
class TestStateMachineGroup(unittest.TestCase):

    def test_state_machine_group_success(self):
        if _debug: TestStateMachineGroup._debug("test_state_machine_group_success")

        # create a state machine group
        smg = StateMachineGroup()

        # create a trapped state machine, start state is success
        tsm = TrappedStateMachine()
        tsm.start_state.success()

        # add it to the group
        smg.append(tsm)

        reset_time_machine()
        if _debug: TestStateMachineGroup._debug("    - time machine reset")

        # tell the group to run
        smg.run()

        run_time_machine(60.0)
        if _debug: TestStateMachineGroup._debug("    - time machine finished")

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state
        assert not smg.is_running
        assert smg.is_success_state
        if _debug: TestStateMachine._debug("    - passed")

    def test_state_machine_group_fail(self):
        if _debug: TestStateMachineGroup._debug("test_state_machine_group_fail")

        # create a state machine group
        smg = StateMachineGroup()

        # create a trapped state machine, start state is fail
        tsm = TrappedStateMachine()
        tsm.start_state.fail()

        # add it to the group
        smg.append(tsm)

        reset_time_machine()
        if _debug: TestStateMachineGroup._debug("    - time machine reset")

        # tell the group to run
        smg.run()

        run_time_machine(60.0)
        if _debug: TestStateMachineGroup._debug("    - time machine finished")

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_fail_state
        assert not smg.is_running
        assert smg.is_fail_state
        if _debug: TestStateMachine._debug("    - passed")


@bacpypes_debugging
class TestStateMachineEvents(unittest.TestCase):

    def test_state_machine_event_01(self):
        if _debug: TestStateMachineEvents._debug("test_state_machine_event_01")

        # create a state machine group
        smg = StateMachineGroup()

        # create a trapped state machine, start state is success
        tsm1 = TrappedStateMachine()
        tsm1.start_state.set_event('e').success()
        smg.append(tsm1)

        # create another trapped state machine, waiting for the event
        tsm2 = TrappedStateMachine()
        tsm2.start_state.wait_event('e').success()
        smg.append(tsm2)

        reset_time_machine()
        if _debug: TestStateMachineEvents._debug("    - time machine reset")

        # tell the group to run
        smg.run()

        run_time_machine(60.0)
        if _debug: TestStateMachineEvents._debug("    - time machine finished")

        # check for success
        assert tsm1.current_state.is_success_state
        assert tsm2.current_state.is_success_state
        assert not smg.is_running
        assert smg.is_success_state
        if _debug: TestStateMachineEvents._debug("    - passed")

    def test_state_machine_event_02(self):
        if _debug: TestStateMachineEvents._debug("test_state_machine_event_02")

        # create a state machine group
        smg = StateMachineGroup()

        # create a trapped state machine, waiting for an event
        tsm1 = TrappedStateMachine()
        tsm1.start_state.wait_event('e').success()
        smg.append(tsm1)

        # create another trapped state machine, start state is success
        tsm2 = TrappedStateMachine()
        tsm2.start_state.set_event('e').success()
        smg.append(tsm2)

        reset_time_machine()
        if _debug: TestStateMachineEvents._debug("    - time machine reset")

        # tell the group to run
        smg.run()

        run_time_machine(60.0)
        if _debug: TestStateMachineEvents._debug("    - time machine finished")

        # check for success
        assert tsm1.current_state.is_success_state
        assert tsm2.current_state.is_success_state
        assert not smg.is_running
        assert smg.is_success_state
        if _debug: TestStateMachineEvents._debug("    - passed")

