#!/usr/bin/python

"""
BACpypes Testing Utilities
--------------------------
"""

import os
from time import time as _time

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# defaults for testing
BACPYPES_TEST = ""
BACPYPES_TEST_OPTION = ""

# parsed test options
test_options = None


#
#   setUpPackage
#

@bacpypes_debugging
def setUpPackage():
    global test_options

    # create an argument parser
    parser = ArgumentParser(description=__doc__)

    # add an option
    parser.add_argument('--option', help="this is an option",
                        default=os.getenv("BACPYPES_TEST_OPTION") or BACPYPES_TEST_OPTION,
                        )

    # get the debugging args and parse them
    arg_str = os.getenv("BACPYPES_TEST") or BACPYPES_TEST
    test_options = parser.parse_args(arg_str.split())

    if _debug: setUpPackage._debug("setUpPackage")
    if _debug: setUpPackage._debug("    - test_options: %r", test_options)


#
#   tearDownPackage
#


@bacpypes_debugging
def tearDownPackage():
    if _debug: tearDownPackage._debug("tearDownPackage")