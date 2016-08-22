#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities Time Machine
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.task import OneShotTask, FunctionTask, \
    RecurringTask, RecurringFunctionTask
from ..time_machine import TimeMachine, reset_time_machine, run_time_machine

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# reference to time machine
time_machine = None

@bacpypes_debugging
def setup_module(module):
    if _debug: setup_module._debug("setup_module %r", module)
    global time_machine

    # this is a singleton
    time_machine = TimeMachine()

    # make sure this is the same one referenced by the functions
    assert time_machine is reset_time_machine.__globals__['time_machine']
    assert time_machine is run_time_machine.__globals__['time_machine']


@bacpypes_debugging
def teardown_module():
    if _debug: teardown_module._debug("teardown_module")
    global time_machine

    # all done
    time_machine = None


@bacpypes_debugging
class SampleOneShotTask(OneShotTask):

    def __init__(self):
        if _debug: SampleOneShotTask._debug("__init__")
        OneShotTask.__init__(self)

        self.process_task_called = 0

    def process_task(self):
        if _debug: SampleOneShotTask._debug("process_task @ %r", time_machine.current_time)
        self.process_task_called += 1


# flag to make sure the function was called
sample_task_function_called = 0

@bacpypes_debugging
def sample_task_function(*args, **kwargs):
    if _debug: sample_task_function._debug("sample_task_function %r %r @ %r", args, kwargs, time_machine.current_time)
    global sample_task_function_called

    # bump the counter
    sample_task_function_called += 1


@bacpypes_debugging
class SampleRecurringTask(RecurringTask):

    def __init__(self):
        if _debug: SampleRecurringTask._debug("__init__")
        RecurringTask.__init__(self)

        self.process_task_called = 0

    def process_task(self):
        if _debug: SampleRecurringTask._debug("process_task @ %r", time_machine.current_time)
        self.process_task_called += 1


@bacpypes_debugging
class TestTimeMachine(unittest.TestCase):

    def test_time_machine_exists(self):
        if _debug: TestTimeMachine._debug("test_time_machine_exists")

        # time machine created by setUpPackage
        assert time_machine is not None

    def test_empty_run(self):
        if _debug: TestTimeMachine._debug("test_empty_run")

        # reset the time machine
        reset_time_machine()

        # let it run
        run_time_machine(60.0)

        # no time has passed
        assert time_machine.current_time == 0.0

    def test_one_shot_immediate(self):
        if _debug: TestTimeMachine._debug("test_one_shot_immediate")

        # create a function task
        ft = SampleOneShotTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(0.0)
        run_time_machine(60.0)

        # function called, no time has passed
        assert ft.process_task_called == 1
        assert time_machine.current_time == 0.0

    def test_function_task_immediate(self):
        if _debug: TestTimeMachine._debug("test_function_task_immediate")
        global sample_task_function_called

        # create a function task
        ft = FunctionTask(sample_task_function)
        sample_task_function_called = 0

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(0.0)
        run_time_machine(60.0)

        # function called, no time has passed
        assert sample_task_function_called == 1
        assert time_machine.current_time == 0.0

    def test_function_task_delay(self):
        if _debug: TestTimeMachine._debug("test_function_task_delay")
        global sample_task_function_called

        sample_delay = 10.0

        # create a function task
        ft = FunctionTask(sample_task_function)
        sample_task_function_called = 0

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(sample_delay)
        run_time_machine(60.0)

        # function called, no time has passed
        assert sample_task_function_called == 1
        assert time_machine.current_time == sample_delay

    def test_recurring_task_1(self):
        if _debug: TestTimeMachine._debug("test_recurring_task_1")

        # create a function task
        ft = SampleRecurringTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(1000.0)
        run_time_machine(5.0)

        # function called, no time has passed
        assert ft.process_task_called == 4
        assert time_machine.current_time == 5.0

    def test_recurring_task_2(self):
        if _debug: TestTimeMachine._debug("test_recurring_task_2")

        # create a function task
        ft1 = SampleRecurringTask()
        ft2 = SampleRecurringTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft1.install_task(1000.0)
        ft2.install_task(1500.0)
        run_time_machine(5.0)

        # function called, no time has passed
        assert ft1.process_task_called == 4
        assert ft2.process_task_called == 3
        assert time_machine.current_time == 5.0
