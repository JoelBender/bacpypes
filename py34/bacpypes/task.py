#!/usr/bin/python

"""
Task
"""

import sys

from time import time as _time
from heapq import heapify, heappush, heappop

from .singleton import SingletonLogging
from .debugging import DebugContents, Logging, ModuleLogger, bacpypes_debugging

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
_task_manager = None
_unscheduled_tasks = []

# only defined for linux platforms
if sys.platform in ('linux2', 'darwin'):
    from .event import WaitableEvent
    #
    #   _Trigger
    #
    #   An instance of this class is used in the task manager to break
    #   the asyncore.loop() call.  In this case, handle_read will
    #   immediately "clear" the event.
    #

    class _Trigger(WaitableEvent, Logging):

        def handle_read(self):
            if _debug: _Trigger._debug("handle_read")

            # read in the character, highlander
            data = self.recv(1)
            if _debug: _Trigger._debug("    - data: %r", data)
else:
    _Trigger = None

#
#   _Task
#

class _Task(DebugContents, Logging):

    _debug_contents = ('taskTime', 'isScheduled')

    def __init__(self):
        self.taskTime = None
        self.isScheduled = False

    def install_task(self, when=None, delta=None):
        global _task_manager, _unscheduled_tasks

        # check for delta from now
        if (when is None) and (delta is not None):
            if not _task_manager:
                raise RuntimeError("no task manager")

            when = _task_manager.get_time() + delta

        # fallback to the inited value
        if when is None:
            when = self.taskTime
        if when is None:
            raise RuntimeError("schedule missing, use zero for 'now'")
        self.taskTime = when

        # pass along to the task manager
        if not _task_manager:
            _unscheduled_tasks.append(self)
        else:
            _task_manager.install_task(self)

    def process_task(self):
        raise RuntimeError("process_task must be overridden")

    def suspend_task(self):
        global _task_manager

        # pass along to the task manager
        if not _task_manager:
            _unscheduled_tasks.remove(self)
        else:
            _task_manager.suspend_task(self)

    def resume_task(self):
        global _task_manager

        _task_manager.resume_task(self)

    def __lt__(self, other):
        return id(self) < id(other)

#
#   OneShotTask
#

class OneShotTask(_Task):

    def __init__(self, when=None):
        _Task.__init__(self)
        self.taskTime = when

#
#   OneShotDeleteTask
#

class OneShotDeleteTask(_Task):

    def __init__(self, when=None):
        _Task.__init__(self)
        self.taskTime = when

#
#   OneShotFunction
#

@bacpypes_debugging
def OneShotFunction(fn, *args, **kwargs):

    class OneShotFunctionTask(OneShotDeleteTask):

        def process_task(self):
            OneShotFunction._debug("process_task %r %s %s", fn, repr(args), repr(kwargs))
            fn(*args, **kwargs)

    task = OneShotFunctionTask()

    # if there is no task manager, postpone the install
    if not _task_manager:
        _unscheduled_tasks.append(task)
    else:
        task.install_task(_task_manager.get_time())

    return task

#
#   FunctionTask
#

def FunctionTask(fn, *args, **kwargs):
    _log.debug("FunctionTask %r %r %r", fn, args, kwargs)

    class _FunctionTask(OneShotDeleteTask):

        def process_task(self):
            _log.debug("process_task (%r %r %r)", fn, args, kwargs)
            fn(*args, **kwargs)

    task = _FunctionTask()
    _log.debug("    - task: %r", task)

    return task

#
#   RecurringTask
#

@bacpypes_debugging
class RecurringTask(_Task):

    _debug_contents = ('taskInterval',)

    def __init__(self, interval=None):
        if _debug: RecurringTask._debug("__init__ interval=%r", interval)
        _Task.__init__(self)

        # save the interval, but do not automatically install
        self.taskInterval = interval

    def install_task(self, interval=None):
        if _debug: RecurringTask._debug("install_task interval=%r", interval)
        global _task_manager, _unscheduled_tasks

        # set the interval if it hasn't already been set
        if interval is not None:
            self.taskInterval = interval
        if self.taskInterval is None:
            raise RuntimeError("interval unset, use ctor or install_task parameter")
        if self.taskInterval <= 0.0:
            raise RuntimeError("interval must be greater than zero")

        # if there is no task manager, postpone the install
        if not _task_manager:
            if _debug: RecurringTask._debug("    - no task manager")
            _unscheduled_tasks.append(self)

        else:
            # get ready for the next interval (aligned)
            now = _task_manager.get_time()
            interval = self.taskInterval / 1000.0
            self.taskTime = now + interval - (now % interval)
            if _debug: RecurringTask._debug("    - task time: %r", self.taskTime)

            # install it
            _task_manager.install_task(self)

#
#   RecurringFunctionTask
#

@bacpypes_debugging
def RecurringFunctionTask(interval, fn, *args, **kwargs):
    if _debug: RecurringFunctionTask._debug("RecurringFunctionTask %r %r %r", fn, args, kwargs)

    class _RecurringFunctionTask(RecurringTask):
        def __init__(self, interval):
            RecurringTask.__init__(self, interval)

        def process_task(self):
            if _debug: RecurringFunctionTask._debug("process_task %r %r %r", fn, args, kwargs)
            fn(*args, **kwargs)

    task = _RecurringFunctionTask(interval)
    if _debug: RecurringFunctionTask._debug("    - task: %r", task)

    return task

#
#   recurring_function
#

@bacpypes_debugging
def recurring_function(interval):
    def recurring_function_decorator(fn):
        class _RecurringFunctionTask(RecurringTask):
            def process_task(self):
                if _debug: recurring_function._debug("process_task %r", fn)
                fn()
            def __call__(self, *args, **kwargs):
                fn(*args, **kwargs)
        task = _RecurringFunctionTask(interval)
        task.install_task()

        return task

    return recurring_function_decorator

#
#   TaskManager
#

# @bacpypes_debugging - implicit via metaclass
class TaskManager(SingletonLogging):

    def __init__(self):
        if _debug: TaskManager._debug("__init__")
        global _task_manager, _unscheduled_tasks

        # initialize
        self.tasks = []
        if _Trigger:
            self.trigger = _Trigger()
        else:
            self.trigger = None

        # task manager is this instance
        _task_manager = self

        # there may be tasks created that couldn't be scheduled
        # because a task manager wasn't created yet.
        if _unscheduled_tasks:
            for task in _unscheduled_tasks:
                task.install_task()

    def get_time(self):
        if _debug: TaskManager._debug("get_time")

        # return the real time
        return _time()

    def install_task(self, task):
        if _debug: TaskManager._debug("install_task %r @ %r", task, task.taskTime)

        # if the taskTime is None is hasn't been computed correctly
        if task.taskTime is None:
            raise RuntimeError("task time is None")

        # if this is already installed, suspend it
        if task.isScheduled:
            self.suspend_task(task)

        # save this in the task list
        heappush( self.tasks, (task.taskTime, task) )
        if _debug: TaskManager._debug("    - tasks: %r", self.tasks)

        task.isScheduled = True

        # trigger the event
        if self.trigger:
            self.trigger.set()

    def suspend_task(self, task):
        if _debug: TaskManager._debug("suspend_task %r", task)

        # remove this guy
        for i, (when, curtask) in enumerate(self.tasks):
            if task is curtask:
                if _debug: TaskManager._debug("    - task found")
                del self.tasks[i]

                task.isScheduled = False
                heapify(self.tasks)
                break
        else:
            if _debug: TaskManager._debug("    - task not found")

        # trigger the event
        if self.trigger:
            self.trigger.set()

    def resume_task(self, task):
        if _debug: TaskManager._debug("resume_task %r", task)

        # just re-install it
        self.install_task(task)

    def get_next_task(self):
        """get the next task if there's one that should be processed,
        and return how long it will be until the next one should be
        processed."""
        if _debug: TaskManager._debug("get_next_task")

        # get the time
        now = _time()

        task = None
        delta = None

        if self.tasks:
            # look at the first task
            when, nxttask = self.tasks[0]
            if when <= now:
                # pull it off the list and mark that it's no longer scheduled
                heappop(self.tasks)
                task = nxttask
                task.isScheduled = False

                if self.tasks:
                    when, nxttask = self.tasks[0]
                    # peek at the next task, return how long to wait
                    delta = max(when - now, 0.0)
            else:
                delta = when - now

        # return the task to run and how long to wait for the next one
        return (task, delta)

    def process_task(self, task):
        if _debug: TaskManager._debug("process_task %r", task)

        # process the task
        task.process_task()

        # see if it should be rescheduled
        if isinstance(task, RecurringTask):
            task.install_task()
        elif isinstance(task, OneShotDeleteTask):
            del task
