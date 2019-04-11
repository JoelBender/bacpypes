#!/usr/bin/python

"""
To Do List

A ToDoItem is a thing that builds an IOCB to be given to a contoller.  Items
are appended to a ToDoList which acts like a supervisor to make sure the
items get done.  An item becomes "active" when the ToDoList asks the item
for its IOCB.

Items may be "threaded" which means that an item must wait until some previously
created item is complete before it becomes active.

The ToDoList can activate more than one item at a time.  Its idle() function
is called when there are no more active or pending items.
"""

import random

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run, deferred
from bacpypes.iocb import IOCB, IOController
from bacpypes.task import FunctionTask

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None


#
#   ToDoItem
#

@bacpypes_debugging
class ToDoItem:

    def __init__(self, _thread=None):
        if _debug: ToDoItem._debug("__init__")

        # basic status information
        self._completed = False

        # may depend on another item to complete
        self._thread = _thread

    def prepare(self):
        if _debug: ToDoItem._debug("prepare")
        raise NotImplementedError

#
#   ToDoList
#

@bacpypes_debugging
class ToDoList:

    def __init__(self, controller, active_limit=1):
        if _debug: ToDoList._debug("__init__")

        # save a reference to the controller for workers
        self.controller = controller

        # limit to the number of active workers
        self.active_limit = active_limit

        # no workers, nothing active
        self.pending = []
        self.active = set()

        # launch already deferred
        self.launch_deferred = False

    def append(self, item):
        if _debug: ToDoList._debug("append %r", item)

        # add the item to the list of pending items
        self.pending.append(item)

        # if an item can be started, schedule to launch it
        if len(self.active) < self.active_limit and not self.launch_deferred:
            if _debug: ToDoList._debug("    - will launch")

            self.launch_deferred = True
            deferred(self.launch)

    def launch(self):
        if _debug: ToDoList._debug("launch")

        # find some workers and launch them
        while self.pending and (len(self.active) < self.active_limit):
            # look for the next to_do_item that can be started
            for i, item in enumerate(self.pending):
                if not item._thread:
                    break
                if item._thread._completed:
                    break
            else:
                if _debug: ToDoList._debug("    - waiting")
                break
            if _debug: ToDoList._debug("    - item: %r", item)

            # remove it from the pending list, add it to active
            del self.pending[i]
            self.active.add(item)

            # prepare it and capture the IOCB
            iocb = item.prepare()
            if _debug: ToDoList._debug("    - iocb: %r", iocb)

            # break the reference to the completed to_do_item
            item._thread = None
            iocb._to_do_item = item

            # add our completion routine
            iocb.add_callback(self.complete)

            # submit it to our controller
            self.controller.request_io(iocb)

        # clear the deferred flag
        self.launch_deferred = False
        if _debug: ToDoList._debug("    - done launching")

        # check for idle
        if (not self.active) and (not self.pending):
            self.idle()

    def complete(self, iocb):
        if _debug: ToDoList._debug("complete %r", iocb)

        # extract the to_do_item
        item = iocb._to_do_item
        if _debug: ToDoList._debug("    - item: %r", item)

        # mark it completed, remove it from active
        item._completed = True
        self.active.remove(item)

        # find another to_do_item
        if not self.launch_deferred:
            if _debug: ToDoList._debug("    - will launch")

            self.launch_deferred = True
            deferred(self.launch)

    def idle(self):
        if _debug: ToDoList._debug("idle")

#
#   SomethingController
#

@bacpypes_debugging
class SomethingController(IOController):

    def process_io(self, iocb):
        if _debug: SomethingController._debug("process_io %r", iocb)

        # simulate taking some time to complete this request
        task_delta = random.random() * 3.0
        print("{}, {}, {:4.2f}s".format(iocb.args, iocb.kwargs, task_delta))

        task = FunctionTask(self.complete_io, iocb, True)
        task.install_task(delta=task_delta)
        if _debug: SomethingController._debug("    - task: %r", task)

#
#   SomethingToDo
#

@bacpypes_debugging
class SomethingToDo(ToDoItem):

    def __init__(self, *args, **kwargs):
        if _debug: SomethingToDo._debug("__init__")
        ToDoItem.__init__(self, _thread=kwargs.get("_thread", None))

        self.args = args
        self.kwargs = kwargs

    def prepare(self):
        if _debug: SomethingToDo._debug("prepare(%d)", self.args[0])

        # build an IOCB and add the completion callback
        iocb = IOCB(*self.args, **self.kwargs)
        iocb.add_callback(self.complete)
        if _debug: SomethingToDo._debug("    - iocb: %r", iocb)

        return iocb

    def complete(self, iocb):
        if _debug: SomethingToDo._debug("complete(%d)", self.args[0])

#
#   main
#

def main():
    global args

    # parse the command line arguments
    args = ArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a controller for to_do_item requests
    controller = SomethingController()
    if _debug: _log.debug("    - controller: %r", controller)

    for i in range(3):
        # make a list bound to the contoller
        to_do_list = ToDoList(controller, active_limit=2)
        if _debug: _log.debug("    - to_do_list: %r", to_do_list)

        for j in range(5):
            to_do_list.append(SomethingToDo(i, j))

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()

