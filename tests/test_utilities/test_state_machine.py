#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities State Machine
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from ..state_machine import State, StateMachine, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine
from ..trapped_classes import TrappedState, TrappedStateMachine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


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

    def test_state_machine_run(self):
        if _debug: TestStateMachine._debug("test_state_machine_run")

        # create a state machine
        tsm = StateMachine()

        # run the machine
        tsm.run()

        # check for still running in the start state
        assert tsm.running
        assert tsm.current_state is tsm.start_state

    def test_state_machine_success(self):
        if _debug: TestStateMachine._debug("test_state_machine_success")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)
        assert isinstance(tsm.start_state, TrappedState)

        # make the start state a success
        tsm.start_state.success()

        # run the machine
        tsm.run()

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state

    def test_state_machine_fail(self):
        if _debug: TestStateMachine._debug("test_state_machine_fail")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)
        assert isinstance(tsm.start_state, TrappedState)

        # make the start state a fail
        tsm.start_state.fail()

        # run the machine
        tsm.run()

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_fail_state

    def test_state_machine_send(self):
        if _debug: TestStateMachine._debug("test_state_machine_send")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)

        # make pdu object
        pdu = object()

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

    def test_state_machine_receive(self):
        if _debug: TestStateMachine._debug("test_state_machine_receive")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)

        # make pdu object
        pdu = object()

        # make a receive transition from start to success, run the machine
        tsm.start_state.receive(pdu).success()
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

    def test_state_machine_unexpected(self):
        if _debug: TestStateMachine._debug("test_state_machine_unexpected")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)

        # make pdu object
        good_pdu = object()
        bad_pdu = object()

        # make a receive transition from start to success, run the machine
        tsm.start_state.receive(good_pdu).success()
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

    def test_state_machine_loop_01(self):
        if _debug: TestStateMachine._debug("test_state_machine_loop_01")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)

        # make pdu object
        first_pdu = object()
        second_pdu = object()

        # after sending the first pdu, wait for the second
        s0 = tsm.start_state
        s1 = s0.send(first_pdu)
        s2 = s1.receive(second_pdu)
        s2.success()

        # run the machine
        tsm.run()

        # check for still running and waiting
        assert tsm.running
        assert tsm.current_state is s1

        # give the machine the second pdu
        tsm.receive(second_pdu)

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state

        # check the callbacks
        assert s0.before_send_pdu is first_pdu
        assert s0.after_send_pdu is first_pdu
        assert s1.before_receive_pdu is second_pdu
        assert s1.after_receive_pdu is second_pdu

        # check the transaction log
        assert len(tsm.transaction_log) == 2
        assert tsm.transaction_log[0][1] is first_pdu
        assert tsm.transaction_log[1][1] is second_pdu

    def test_state_machine_loop_02(self):
        if _debug: TestStateMachine._debug("test_state_machine_loop_02")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)

        # make pdu object
        first_pdu = object()
        second_pdu = object()

        # when the first pdu is received, send the second
        s0 = tsm.start_state
        s1 = s0.receive(first_pdu)
        s2 = s1.send(second_pdu)
        s2.success()

        # run the machine
        tsm.run()

        # check for still running
        assert tsm.running

        # give the machine the first pdu
        tsm.receive(first_pdu)

        # check for success
        assert not tsm.running
        assert tsm.current_state.is_success_state

        # check the callbacks
        assert s0.before_receive_pdu is first_pdu
        assert s0.after_receive_pdu is first_pdu
        assert s1.before_send_pdu is second_pdu
        assert s1.after_send_pdu is second_pdu

        # check the transaction log
        assert len(tsm.transaction_log) == 2
        assert tsm.transaction_log[0][1] is first_pdu
        assert tsm.transaction_log[1][1] is second_pdu


@bacpypes_debugging
class TestStateMachineTimeout1(unittest.TestCase):

    def test_state_machine_timeout_1(self):
        if _debug: TestStateMachineTimeout1._debug("test_state_machine_timeout_1")

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)

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


@bacpypes_debugging
class TestStateMachineTimeout2(unittest.TestCase):

    def test_state_machine_timeout_2(self):
        if _debug: TestStateMachineTimeout2._debug("test_state_machine_timeout_2")

        # make some pdu's
        first_pdu = object()
        second_pdu = object()

        # create a trapped state machine
        tsm = TrappedStateMachine(state_subclass=TrappedState)
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


@bacpypes_debugging
class TestStateMachineGroup(unittest.TestCase):

    def test_state_machine_group_success(self):
        if _debug: TestStateMachineGroup._debug("test_state_machine_group_success")

        # create a state machine group
        smg = StateMachineGroup()

        # create a trapped state machine, start state is success
        tsm = TrappedStateMachine(state_subclass=TrappedState)
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
        assert smg.is_success_state

    def test_state_machine_group_fail(self):
        if _debug: TestStateMachineGroup._debug("test_state_machine_group_fail")

        # create a state machine group
        smg = StateMachineGroup()

        # create a trapped state machine, start state is fail
        tsm = TrappedStateMachine(state_subclass=TrappedState)
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
        assert smg.is_fail_state
