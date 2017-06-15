#!/usr/bin/python

"""
Testing Time Machine
--------------------
"""

from heapq import heappop

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.core import run_once
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
        if _debug: TimeMachine._debug("get_time")

        # return the fake time
        return self.current_time

    def install_task(self, task):
        if _debug: TimeMachine._debug("install_task %r @ %r", task, task.taskTime)

        _TaskManager.install_task(self, task)

    def suspend_task(self, task):
        if _debug: TimeMachine._debug("suspend_task %r", task)

        _TaskManager.suspend_task(self, task)

    def resume_task(self, task):
        if _debug: TimeMachine._debug("resume_task %r", task)

        _TaskManager.resume_task(self, task)

    def get_next_task(self):
        """get the next task if there's one that should be processed,
        and return how long it will be until the next one should be
        processed."""
        if _debug: TimeMachine._debug("get_next_task @ %r", self.current_time)
        if _debug: TimeMachine._debug("    - self.tasks: %r", self.tasks)

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
        if _debug: TimeMachine._debug("process_task %r", task)

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
    time_machine.current_time = 0.0
    time_machine.time_limit = None


@bacpypes_debugging
def run_time_machine(time_limit):
    """This function is called after a set of tasks have been installed
    and they should all run.
    """
    if _debug: run_time_machine._debug("run_time_machine %r", time_limit)
    global time_machine

    # a little error checking
    if not time_machine:
        raise RuntimeError("no time machine")
    if time_limit <= 0.0:
        raise ValueError("time limit required")

    # pass the limit to the time machine
    time_machine.time_limit = time_limit

    # run until there is nothing left to do
    run_once()
