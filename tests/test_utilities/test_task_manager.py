#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Utilities State Machine
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.task import OneShotTask, FunctionTask, \
    RecurringTask, RecurringFunctionTask
from ..task_manager import TaskManager, reset_task_manager, run_task_manager

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# reference to test task manager
test_task_manager = None

#
#   setUpModule
#


@bacpypes_debugging
def setUpModule():
    if _debug: setUpModule._debug("setUpModule")
    global test_task_manager

    # this is a singleton
    test_task_manager = TaskManager()

    # make sure this is the same one referenced by the functions
    assert test_task_manager is reset_task_manager.__globals__['test_task_manager']
    assert test_task_manager is run_task_manager.__globals__['test_task_manager']


@bacpypes_debugging
def tearDownModule():
    if _debug: tearDownModule._debug("tearDownModule")
    global test_task_manager

    # all done
    test_task_manager = None


#
#   SampleOneShotTask
#

@bacpypes_debugging
class SampleOneShotTask(OneShotTask):

    def __init__(self):
        if _debug: SampleOneShotTask._debug("__init__")
        OneShotTask.__init__(self)

        self.process_task_called = 0

    def process_task(self):
        if _debug: SampleOneShotTask._debug("process_task")
        self.process_task_called += 1


#
#   sample_task_function
#

# flag to make sure the function was called
sample_task_function_called = 0

@bacpypes_debugging
def sample_task_function(*args, **kwargs):
    if _debug: sample_task_function._debug("sample_task_function %r %r", args, kwargs)
    global sample_task_function_called

    # bump the counter
    sample_task_function_called += 1


@bacpypes_debugging
class TestTaskManager(unittest.TestCase):

    def test_manager_exists(self):
        if _debug: TestTaskManager._debug("test_manager_exists")

        # task manager created by setUpPackage
        assert test_task_manager is not None

    def test_empty_run(self):
        if _debug: TestTaskManager._debug("test_empty_run")

        # reset the manager
        reset_task_manager()

        # let it run
        run_task_manager()

        # no time has passed
        assert test_task_manager.current_time == 0.0

    def test_one_shot_immediate(self):
        if _debug: TestTaskManager._debug("test_one_shot_immediate")

        # create a function task
        ft = SampleOneShotTask()

        # reset the manager, install the task, let it run
        reset_task_manager()
        ft.install_task(0.0)
        run_task_manager()

        # function called, no time has passed
        assert ft.process_task_called == 1
        assert test_task_manager.current_time == 0.0

    def test_function_task_immediate(self):
        if _debug: TestTaskManager._debug("test_function_task_immediate")
        global sample_task_function_called

        # create a function task
        ft = FunctionTask(sample_task_function)
        sample_task_function_called = 0

        # reset the manager, install the task, let it run
        reset_task_manager()
        ft.install_task(0.0)
        run_task_manager()

        # function called, no time has passed
        assert sample_task_function_called == 1
        assert test_task_manager.current_time == 0.0

    def test_function_task_delay(self):
        if _debug: TestTaskManager._debug("test_function_task_delay")
        global sample_task_function_called

        sample_delay = 10.0

        # create a function task
        ft = FunctionTask(sample_task_function)
        sample_task_function_called = 0

        # reset the manager, install the task, let it run
        reset_task_manager()
        ft.install_task(sample_delay)
        run_task_manager()

        # function called, no time has passed
        assert sample_task_function_called == 1
        assert test_task_manager.current_time == sample_delay
