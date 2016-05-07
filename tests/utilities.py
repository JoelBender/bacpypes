#!/usr/bin/python

"""
BACpypes Testing Utilities
--------------------------
"""

import os

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

# use a task manager specific to testing
from .time_machine import TimeMachine

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# defaults for testing
BACPYPES_TEST = ""
BACPYPES_TEST_OPTION = ""

# parsed test options
test_options = None


@bacpypes_debugging
def setup_package():
    global test_options

    # create an argument parser
    parser = ArgumentParser(description=__doc__)

    # add an option
    parser.add_argument(
        '--option', help="this is an option",
        default=os.getenv("BACPYPES_TEST_OPTION") or BACPYPES_TEST_OPTION,
        )

    # get the debugging args and parse them
    arg_str = os.getenv("BACPYPES_TEST") or BACPYPES_TEST
    test_options = parser.parse_args(arg_str.split())

    if _debug: setup_package._debug("setup_package")
    if _debug: setup_package._debug("    - test_options: %r", test_options)

    time_machine = TimeMachine()
    if _debug: setup_package._debug("    - time_machine: %r", time_machine)


@bacpypes_debugging
def teardown_package():
    if _debug: teardown_package._debug("teardown_package")
