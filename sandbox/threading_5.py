#!/usr/bin/python

"""
This application demonstrates doing something at a regular interval.
"""

import sys
import time
from threading import Thread

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run, stop
from bacpypes.task import recurring_function

# some debugging
_debug = 0
_log = ModuleLogger(globals())


def write_flush(text):
    """Print the text, flush immediately."""
    sys.stdout.write(text)
    sys.stdout.flush()


@recurring_function(3000.0)
def ding():
    """Do something in the BACpypes run loop."""
    write_flush(".")


class BACpypesThread(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        _log.debug("running")

        run()

        _log.debug("fini")

    def stop(self):
        stop()
        self.join()


def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)

    # now parse the arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make the thread object and start it
    bacpypes_thread = BACpypesThread()
    bacpypes_thread.start()

    # main thread
    while True:
        write_flush("#")
        time.sleep(2)

    # tell the thread to stop
    bacpypes_thread.stop()


if __name__ == "__main__":
    main()
