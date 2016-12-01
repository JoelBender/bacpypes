#!/usr/bin/python

"""
Core
"""

import sys
import asyncore
import signal
import time
import traceback

from .task import TaskManager
from .debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
running = False
taskManager = None
deferredFns = []
sleeptime = 0.0

#
#   run
#

SPIN = 1.0

@bacpypes_debugging
def run(spin=SPIN):
    if _debug: run._debug("run spin=%r", spin)
    global running, taskManager, deferredFns, sleeptime

    # reference the task manager (a singleton)
    taskManager = TaskManager()

    # count how many times we are going through the loop
    loopCount = 0

    running = True
    while running:
#       if _debug: run._debug("    - time: %r", time.time())
        loopCount += 1

        # get the next task
        task, delta = taskManager.get_next_task()

        try:
            # if there is a task to process, do it
            if task:
                # if _debug: run._debug("    - task: %r", task)
                taskManager.process_task(task)

            # if delta is None, there are no tasks, default to spinning
            if delta is None:
                delta = spin

            # there may be threads around, sleep for a bit
            if sleeptime and (delta > sleeptime):
                time.sleep(sleeptime)
                delta -= sleeptime

            # if there are deferred functions, use a small delta
            if deferredFns:
                delta = min(delta, 0.001)
#           if _debug: run._debug("    - delta: %r", delta)

            # loop for socket activity
            asyncore.loop(timeout=delta, count=1)

            # check for deferred functions
            while deferredFns:
                # get a reference to the list
                fnlist = deferredFns
                deferredFns = []

                # call the functions
                for fn, args, kwargs in fnlist:
#                   if _debug: run._debug("    - call: %r %r %r", fn, args, kwargs)
                    fn( *args, **kwargs)

                # done with this list
                del fnlist

        except KeyboardInterrupt:
            if _debug: run._info("keyboard interrupt")
            running = False
        except Exception as err:
            if _debug: run._exception("an error has occurred: %s", err)

    running = False

#
#   run_once
#

@bacpypes_debugging
def run_once():
    """
    Make a pass through the scheduled tasks and deferred functions just
    like the run() function but without the asyncore call (so there is no
    socket IO actviity) and the timers.
    """
    if _debug: run_once._debug("run_once")
    global taskManager, deferredFns

    # reference the task manager (a singleton)
    taskManager = TaskManager()

    try:
        delta = 0.0
        while delta == 0.0:
            # get the next task
            task, delta = taskManager.get_next_task()
            if _debug: run_once._debug("    - task, delta: %r, %r", task, delta)

            # if there is a task to process, do it
            if task:
                taskManager.process_task(task)

            # check for deferred functions
            while deferredFns:
                # get a reference to the list
                fnlist = deferredFns
                deferredFns = []

                # call the functions
                for fn, args, kwargs in fnlist:
                    if _debug: run_once._debug("    - call: %r %r %r", fn, args, kwargs)
                    fn( *args, **kwargs)

                # done with this list
                del fnlist

    except KeyboardInterrupt:
        if _debug: run_once._info("keyboard interrupt")
    except Exception as err:
        if _debug: run_once._exception("an error has occurred: %s", err)

#
#   stop
#

@bacpypes_debugging
def stop(*args):
    """Call to stop running, may be called with a signum and frame
    parameter if called as a signal handler."""
    if _debug: stop._debug("stop")
    global running, taskManager

    if args:
        sys.stderr.write("===== TERM Signal, %s\n" % time.strftime("%d-%b-%Y %H:%M:%S"))
        sys.stderr.flush()

    running = False

    # trigger the task manager event
    if taskManager and taskManager.trigger:
        if _debug: stop._debug("    - trigger")
        taskManager.trigger.set()

# set a TERM signal handler
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, stop)

#
#   print_stack
#

@bacpypes_debugging
def print_stack(sig, frame):
    """Signal handler to print a stack trace and some interesting values."""
    if _debug: print_stack._debug("print_stack, %r, %r", sig, frame)
    global running, deferredFns, sleeptime

    sys.stderr.write("==== USR1 Signal, %s\n" % time.strftime("%d-%b-%Y %H:%M:%S"))

    sys.stderr.write("---------- globals\n")
    sys.stderr.write("    running: %r\n" % (running,))
    sys.stderr.write("    deferredFns: %r\n" % (deferredFns,))
    sys.stderr.write("    sleeptime: %r\n" % (sleeptime,))

    sys.stderr.write("---------- stack\n")
    traceback.print_stack(frame)

    # make a list of interesting frames
    flist = []
    f = frame
    while f.f_back:
        flist.append(f)
        f = f.f_back

    # reverse the list so it is in the same order as print_stack
    flist.reverse()
    for f in flist:
        sys.stderr.write("---------- frame: %s\n" % (f,))
        for k, v in f.f_locals.items():
            sys.stderr.write("    %s: %r\n" % (k, v))

    sys.stderr.flush()

# set a USR1 signal handler to print a stack trace
if hasattr(signal, 'SIGUSR1'):
    signal.signal(signal.SIGUSR1, print_stack)

#
#   deferred
#

@bacpypes_debugging
def deferred(fn, *args, **kwargs):
#   if _debug:
#       deferred._debug("deferred %r %r %r", fn, args, kwargs)
#       for filename, lineno, _, _ in traceback.extract_stack()[-6:-1]:
#           deferred._debug("    %s:%s" % (filename.split('/')[-1], lineno))
    global deferredFns, taskManager

    # append it to the list
    deferredFns.append((fn, args, kwargs))

    # trigger the task manager event
    if taskManager and taskManager.trigger:
#       if _debug: deferred._debug("    - trigger")
        taskManager.trigger.set()

#
#   enable_sleeping
#

@bacpypes_debugging
def enable_sleeping(stime=0.001):
    if _debug: enable_sleeping._debug("enable_sleeping %r", stime)
    global sleeptime

    # set the sleep time
    sleeptime = stime
