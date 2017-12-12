#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities Time Machine
----------------------------
"""

import time
import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.task import OneShotTask, FunctionTask, RecurringTask
from ..time_machine import TimeMachine, reset_time_machine, run_time_machine, \
    xdatetime

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# reference to time machine
time_machine = None


@bacpypes_debugging
def almost_equal(x, y):
    """Compare two arrays of floats."""
    # must be the same length
    if len(x) != len(y):
        return False

    # absolute value of the difference is tollerable
    for xx, yy in zip(x, y):
        if abs(xx - yy) > 0.000001:
            return False

    # good to go
    return True


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

        self.process_task_called = []

    def process_task(self):
        global time_machine
        if _debug: SampleOneShotTask._debug("process_task @ %r", time_machine.current_time)

        # add the current time
        self.process_task_called.append(time_machine.current_time)


# flag to make sure the function was called
sample_task_function_called = []

@bacpypes_debugging
def sample_task_function(*args, **kwargs):
    global sample_task_function_called, time_machine
    if _debug: sample_task_function._debug("sample_task_function %r %r @ %r", args, kwargs, time_machine.current_time)

    # bump the counter
    sample_task_function_called.append(time_machine.current_time)


@bacpypes_debugging
class SampleRecurringTask(RecurringTask):

    def __init__(self):
        if _debug: SampleRecurringTask._debug("__init__")
        RecurringTask.__init__(self)

        self.process_task_called = []

    def process_task(self):
        global time_machine
        if _debug: SampleRecurringTask._debug("process_task @ %r %s",
            time_machine.current_time,
            time.strftime("%x %X", time.gmtime(time_machine.current_time)),
            )

        # add the current time
        self.process_task_called.append(time_machine.current_time)


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

        # 60 seconds have passed
        assert time_machine.current_time == 60.0

    def test_one_shot_immediate_1(self):
        if _debug: TestTimeMachine._debug("test_one_shot_immediate_1")

        # create a function task
        ft = SampleOneShotTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(0.0)
        run_time_machine(60.0)

        # function called, 60 seconds have passed
        assert almost_equal(ft.process_task_called, [0.0])
        assert time_machine.current_time == 60.0

    def test_one_shot_immediate_2(self):
        if _debug: TestTimeMachine._debug("test_one_shot_immediate_2")

        # create a function task
        ft = SampleOneShotTask()

        # run the function sometime later
        t1 = xdatetime("2000-06-06")
        if _debug: TestTimeMachine._debug("    - t1: %r", t1)

        # reset the time machine to midnight, install the task, let it run
        reset_time_machine(start_time="2000-01-01")
        ft.install_task(t1)
        run_time_machine(stop_time="2001-01-01")

        # function called at correct time
        assert almost_equal(ft.process_task_called, [t1])

    def test_function_task_immediate(self):
        if _debug: TestTimeMachine._debug("test_function_task_immediate")
        global sample_task_function_called

        # create a function task
        ft = FunctionTask(sample_task_function)
        sample_task_function_called = []

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(0.0)
        run_time_machine(60.0)

        # function called, 60 seconds have passed
        assert almost_equal(sample_task_function_called, [0.0])
        assert time_machine.current_time == 60.0

    def test_function_task_delay(self):
        if _debug: TestTimeMachine._debug("test_function_task_delay")
        global sample_task_function_called

        sample_delay = 10.0

        # create a function task
        ft = FunctionTask(sample_task_function)
        sample_task_function_called = []

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(sample_delay)
        run_time_machine(60.0)

        # function called, 60 seconds have passed
        assert almost_equal(sample_task_function_called, [sample_delay])
        assert time_machine.current_time == 60.0

    def test_recurring_task_1(self):
        if _debug: TestTimeMachine._debug("test_recurring_task_1")

        # create a function task
        ft = SampleRecurringTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(1000.0)
        run_time_machine(5.0)

        # function called, 5 seconds have passed
        assert almost_equal(ft.process_task_called, [1.0, 2.0, 3.0, 4.0])
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

        # function called, 5 seconds have passed
        assert almost_equal(ft1.process_task_called, [1.0, 2.0, 3.0, 4.0])
        assert almost_equal(ft2.process_task_called, [1.5, 3.0, 4.5])
        assert time_machine.current_time == 5.0

    def test_recurring_task_3(self):
        if _debug: TestTimeMachine._debug("test_recurring_task_3")

        # create a function task
        ft = SampleRecurringTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(1000.0, offset=100.0)
        run_time_machine(5.0)

        # function called, 5 seconds have passed
        assert almost_equal(ft.process_task_called, [0.1, 1.1, 2.1, 3.1, 4.1])
        assert time_machine.current_time == 5.0

    def test_recurring_task_4(self):
        if _debug: TestTimeMachine._debug("test_recurring_task_4")

        # create a function task
        ft = SampleRecurringTask()

        # reset the time machine, install the task, let it run
        reset_time_machine()
        ft.install_task(1000.0, offset=-100.0)
        run_time_machine(5.0)

        # function called, 5 seconds have passed
        assert almost_equal(ft.process_task_called, [0.9, 1.9, 2.9, 3.9, 4.9])
        assert time_machine.current_time == 5.0

    def test_recurring_task_5(self):
        if _debug: TestTimeMachine._debug("test_recurring_task_5")

        # create a function task
        ft = SampleRecurringTask()

        # reset the time machine, install the task, let it run
        reset_time_machine(start_time="2000-01-01")
        ft.install_task(86400.0 * 1000.0)
        run_time_machine(stop_time="2000-02-01")

        # function called every day
        assert len(ft.process_task_called) == 31

