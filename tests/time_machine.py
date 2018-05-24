#!/usr/bin/python

"""
Testing Time Machine
--------------------
"""

import re
import time
from heapq import heappop

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

import bacpypes.core as _core
from bacpypes.task import TaskManager as _TaskManager

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# time machine
time_machine = None

# some patterns
_date_regex = re.compile("^(\d{4})[-](0?[1-9]|1[0-4])[-]([0-3]?\d)$")
_time_regex = re.compile("^(\d+)[:](\d+)(?:[:](\d+)(?:[.](\d+))?)?$")
_deltatime_regex = re.compile("^(\d+(?:[.]\d+))?$")


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
            if _debug: TimeMachine._debug("    - time limit reached or exceeded")
            return False

        if not self.tasks:
            if _debug: TimeMachine._debug("    - no more tasks")
            return False

        # peek at the next task and see when it is supposed to run
        when, n, task = self.tasks[0]
        if when >= self.time_limit:
            if _debug: TimeMachine._debug("    - next task at or exceeds time limit")
            return False

        # there is a task to run
        if _debug: TimeMachine._debug("    - task: %r", task)

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
            when, n, _ = self.tasks[0]
            if when >= self.time_limit:
                if _debug: TimeMachine._debug("    - time limit reached")

                # bump up to the time limit
                self.current_time = self.time_limit

            else:
                # pull it off the list
                when, n, task = heappop(self.tasks)
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
def xdatetime(s, now=None):
    """
    Given a string of the form "[YYYY-MM-DD] [HR:MN[:SC[.HN]]]" where the
    date or time or both are provided, return the seconds since the epoch.

    If the date is provided and the time is not, assume the time is
    midnight, e.g., 0:0:0.0.

    If the time is provided but the date is not, assume the date is the same
    as the date in 'now'.

    If the time is provided as a floating point number, it is a deltatime
    from 'now'.
    """
    if _debug: xdatetime._debug("xdatetime %r", s)

    # assume there is no offset and nothing matches
    seconds_offset = 0.0
    date_match = time_match = deltatime_match = None

    # split the string into two pieces
    h, _, t = s.strip().partition(" ")
    if not h:
        raise RuntimeError("date and/or time required")
    if _debug: xdatetime._debug("    - h, t: %r, %r", h, t)

    if h and t:
        date_match = _date_regex.match(h)
        if not date_match:
            raise RuntimeError("date not matching")

        time_match = _time_regex.match(t)
        if not time_match:
            raise RuntimeError("time not matching")
    else:
        date_match = _date_regex.match(h)
        if not date_match:
            time_match = _time_regex.match(h)
            if not time_match:
                deltatime_match = _deltatime_regex.match(h)
                if not deltatime_match:
                    raise RuntimeError("no match")
                seconds_offset = float(deltatime_match.groups()[0])
                if _debug: xdatetime._debug("    - seconds_offset: %r", seconds_offset)

                if now is None:
                    raise RuntimeError("'now' required for deltatime")

                return now + seconds_offset

    xtuple = []
    if date_match:
        xtuple.extend(int(v) for v in date_match.groups())
    else:
        if now is None:
            raise RuntimeError("'now' required for deltatime")

        xtuple.extend(time.localtime(now)[:3])
    if _debug: xdatetime._debug("    - xtuple: %r", xtuple)

    if time_match:
        time_tuple = list(int(v or "0") for v in time_match.groups())
        if _debug: xdatetime._debug("    - time_tuple: %r", time_tuple)

        xtuple.extend(time_tuple[:3])

        seconds_offset = float(time_tuple[3])
        if seconds_offset:
            seconds_offset /= 10.0 ** len(time_match.groups()[3])
        if _debug: xdatetime._debug("    - seconds_offset: %r", seconds_offset)
    else:
        xtuple.extend([0, 0, 0])
    if _debug: xdatetime._debug("    - xtuple: %r", xtuple)

    # fill it out to length nine, unknown dst
    xtuple.extend([0, 0, -1])
    if _debug: xdatetime._debug("    - xtuple: %r", xtuple)

    # convert it back to seconds since the epoch
    xtime = time.mktime(tuple(xtuple)) + seconds_offset
    if _debug: xdatetime._debug("    - xtime: %r", xtime)

    return xtime


@bacpypes_debugging
def reset_time_machine(start_time=0.0):
    """This function is called to reset the clock before running a set
    of tests.
    """
    if _debug: reset_time_machine._debug("reset_time_machine %r", start_time)
    global time_machine

    # a little error checking
    if not time_machine:
        raise RuntimeError("no time machine")

    # the start might be a special string
    if isinstance(start_time, str):
        start_time = xdatetime(start_time)
        if _debug: reset_time_machine._debug("    - start_time: %r", start_time)

    # begin time at the beginning
    time_machine.tasks = []
    time_machine.current_time = start_time
    time_machine.time_limit = None


@bacpypes_debugging
def run_time_machine(duration=None, stop_time=None):
    """This function is called after a set of tasks have been installed
    and they should run.  The machine will stop when the stop time has been
    reached (maybe the middle of some tests) and can be called again to
    continue running.
    """
    if _debug: run_time_machine._debug("run_time_machine %r %r", duration, stop_time)
    global time_machine

    # a little error checking
    if not time_machine:
        raise RuntimeError("no time machine")
    if time_machine.current_time is None:
        raise RuntimeError("reset the time machine before running")

    # check for duration, calculate the time limit
    if duration is not None:
        # pass the limit to the time machine
        time_machine.time_limit = time_machine.current_time + duration

    elif stop_time is not None:
        # the start might be a special string
        if isinstance(stop_time, str):
            stop_time = xdatetime(stop_time, time_machine.current_time)
            if _debug: reset_time_machine._debug("    - stop_time: %r", stop_time)

        # pass the limit to the time machine
        time_machine.time_limit = stop_time
    else:
        raise RuntimeError("duration or stop_time required")

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

    # update the current time to the time limit
    time_machine.current_time = time_machine.time_limit


def current_time():
    """Return the current time from the time machine."""
    global time_machine

    return time_machine.current_time

