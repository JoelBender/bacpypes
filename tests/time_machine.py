#!/usr/bin/python

"""
Testing Time Machine
--------------------
"""

from heapq import heappop

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

import bacpypes.core as _core
from bacpypes.task import TaskManager as _TaskManager

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# time machine
time_machine = None


# @bacpypes_debugging - implicit via metaclass
class TimeMachine(_TaskManager):

    def __init__(self):
        if _debug: TimeMachine._debug("__init__")
        global time_machine

        # pass along initialization
        _TaskManager.__init__(self)

        # initialize the time
        self.current_time = None
        self.time_limit = None

        # a little error checking
        if time_machine:
            raise RuntimeError("time machine already created")

        # save a reference
        time_machine = self

    def get_time(self):
        if _debug: TimeMachine._debug("get_time @ %r:", self.current_time)

        # return the fake time
        return self.current_time

    def install_task(self, task):
        if _debug: TimeMachine._debug("install_task @ %r: %r @ %r", self.current_time, task, task.taskTime)

        _TaskManager.install_task(self, task)

    def suspend_task(self, task):
        if _debug: TimeMachine._debug("suspend_task @ %r: %r", self.current_time, task)

        _TaskManager.suspend_task(self, task)

    def resume_task(self, task):
        if _debug: TimeMachine._debug("resume_task @ %r: %r", self.current_time, task)

        _TaskManager.resume_task(self, task)

    def more_to_do(self):
        """Get the next task if there's one that should be processed."""
        if _debug: TimeMachine._debug("more_to_do @ %r:", self.current_time)

        # check if there are deferred functions
        if _core.deferredFns:
            if _debug: TimeMachine._debug("    - deferred functions")
            return True

        if _debug: TimeMachine._debug("    - time_limit: %r", self.time_limit)
        if _debug: TimeMachine._debug("    - tasks: %r", self.tasks)

        if (self.time_limit is not None) and (self.current_time >= self.time_limit):
            if _debug: TimeMachine._debug("    - time limit reached")
            return False

        if not self.tasks:
            if _debug: TimeMachine._debug("    - no more tasks")
            return False

        # peek at the next task and see when it is supposed to run
        when, task = self.tasks[0]
        if when >= self.time_limit:
            if _debug: TimeMachine._debug("    - time limit reached")
            return False
        if _debug: TimeMachine._debug("    - task: %r", task)

        # there is a task to run
        return True

    def get_next_task(self):
        """get the next task if there's one that should be processed,
        and return how long it will be until the next one should be
        processed."""
        if _debug: TimeMachine._debug("get_next_task @ %r:", self.current_time)
        if _debug: TimeMachine._debug("    - time_limit: %r", self.time_limit)
        if _debug: TimeMachine._debug("    - tasks: %r", self.tasks)

        task = None
        delta = None

        if (self.time_limit is not None) and (self.current_time >= self.time_limit):
            if _debug: TimeMachine._debug("    - time limit reached")

        elif not self.tasks:
            if _debug: TimeMachine._debug("    - no more tasks")

        else:
            # peek at the next task and see when it is supposed to run
            when, _ = self.tasks[0]
            if when >= self.time_limit:
                if _debug: TimeMachine._debug("    - time limit reached")

                # bump up to the time limit
                self.current_time = self.time_limit

            else:
                # pull it off the list
                when, task = heappop(self.tasks)
                if _debug: TimeMachine._debug("    - when, task: %r, %s", when, task)

                # mark that it is no longer scheduled
                task.isScheduled = False

                # advance the time
                self.current_time = when

                # do not wait, time has moved
                delta = 0.0

        # return the task to run and how long to wait for the next one
        return (task, delta)

    def process_task(self, task):
        if _debug: TimeMachine._debug("process_task @ %r: %r", self.current_time, task)

        _TaskManager.process_task(self, task)


@bacpypes_debugging
def reset_time_machine():
    """This function is called to reset the clock before running a set
    of tests.
    """
    if _debug: reset_time_machine._debug("reset_time_machine")
    global time_machine

    # a little error checking
    if not time_machine:
        raise RuntimeError("no time machine")

    # begin time at the beginning
    time_machine.tasks = []
    time_machine.current_time = 0.0
    time_machine.time_limit = None


@bacpypes_debugging
def run_time_machine(time_limit):
    """This function is called after a set of tasks have been installed
    and they should run.  The machine will stop when the limit has been
    reached (maybe the middle of some tests) and can be called again to
    continue running.
    """
    if _debug: run_time_machine._debug("run_time_machine %r", time_limit)
    global time_machine

    # a little error checking
    if not time_machine:
        raise RuntimeError("no time machine")
    if time_limit <= 0.0:
        raise ValueError("time limit required")
    if time_machine.current_time is None:
        raise RuntimeError("reset the time machine before running")

    # pass the limit to the time machine
    time_machine.time_limit = time_machine.current_time + time_limit

    # check if there are deferred functions
    if _core.deferredFns:
        if _debug: run_time_machine._debug("    - deferred functions!")

    # run until there is nothing left to do
    while True:
        _core.run_once()
        if _debug: run_time_machine._debug("    - ran once")

        if not time_machine.more_to_do():
            if _debug: run_time_machine._debug("    - no more to do")
            break


def current_time():
    """Return the current time from the time machine."""
    global time_machine

    return time_machine.current_time

