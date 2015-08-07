#!/usr/bin/python

"""
Testing Task Manager
--------------------
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.task import TaskManager as _TaskManager

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# test task manager
test_task_manager = None

#
#   TaskManager
#

# @bacpypes_debugging - implicit via metaclass
class TaskManager(_TaskManager):

    def __init__(self):
        if _debug: TaskManager._debug("__init__")
        global test_task_manager

        # pass along initialization
        _TaskManager.__init__(self)

        # initialize the time
        self._time = None

        # a little error checking
        if test_task_manager:
            raise RuntimeError("test task manager already created")

        # save a reference
        test_task_manager = self

    def get_time(self):
        if _debug: TaskManager._debug("get_time")

        # return the fake time
        return self._time

    def install_task(self, task):
        if _debug: TaskManager._debug("install_task %r @ %r", task, task.taskTime)

        _TaskManager.install_task(self, task)

    def suspend_task(self, task):
        if _debug: TaskManager._debug("suspend_task %r", task)

        _TaskManager.suspend_task(self, task)

    def resume_task(self, task):
        if _debug: TaskManager._debug("resume_task %r", task)

        _TaskManager.resume_task(self, task)

    def get_next_task(self):
        """get the next task if there's one that should be processed,
        and return how long it will be until the next one should be
        processed."""
        if _debug: TaskManager._debug("get_next_task")

        task = None
        delta = None

        if self.tasks:
            # pull it off the list
            when, task = heappop(self.tasks)
            if _debug: TaskManager._debug("    - when, task: %r, %r", when, task)

            # mark that it is no longer scheduled
            task.isScheduled = False

            # advance the time
            self.time = when

            # do not wait, time has moved
            delta = 0.0

        else:
            if _debug: TaskManager._debug("    - no more tasks")

        # return the task to run and how long to wait for the next one
        return (task, delta)

    def process_task(self, task):
        if _debug: TaskManager._debug("process_task %r", task)

        _TaskManager.process_task(self, task)

#
#   task_manager_reset
#

@bacpypes_debugging
def task_manager_reset():
    """This function is called to reset the clock before running a set 
    of tests.
    """
    if _debug: task_manager_reset._debug("task_manager_reset")
    global test_task_manager

    # a little error checking
    if not test_task_manager:
        raise RuntimeError("no test task manager")

    # begin time at the beginning
    test_task_manager._time = 0.0

#
#   task_manager_run
#

@bacpypes_debugging
def task_manager_run():
    """This function is called after a set of tasks have been installed
    and they should all run.
    """
    if _debug: task_manager_run._debug("task_manager_run")
    global test_task_manager

    # a little error checking
    if not test_task_manager:
        raise RuntimeError("no test task manager")

    # run until there is nothing left to do
    run_once()