#!/usr/bin/python

"""
Test IO Server
"""

import random

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run

from io import IOController, IOServer

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# defaults
CONTROLLER = "test"

#
#   TestController
#

@bacpypes_debugging
class TestController(IOController):

    def __init__(self, name):
        if _debug: TestController._debug('__init__')
        IOController.__init__(self, name)

    def process_io(self, iocb):
        if _debug: TestController._debug('process_io %r', iocb)

        # some random data
        rslt = random.random() * iocb.args[0]

        # send back the result
        self.complete_io(iocb, rslt)

#
#   __main__
#

try:
    # create a parser
    parser = ArgumentParser(description=__doc__)

    # add an option to pick a controller
    parser.add_argument('--controller',
        help="controller name",
        default=CONTROLLER,
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # this is an IO server
    IOServer()

    # create a test controller
    TestController(args.controller)

    _log.debug("running")
    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")

