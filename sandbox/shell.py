#!/usr/bin/python3

"""
Template application that uses the ConsoleCmd class.
"""

import sys
import time
import argparse

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None

#
#   Shell
#

@bacpypes_debugging
class Shell(ConsoleCmd):

    def __init__(self):
        if _debug: Shell._debug("__init__")
        global args

        prompt = args.prompt
        if args.args:
            command_input = StringIO(' '.join(args.args))

            # turn off raw input
            self.use_rawinput = False

            # continue with initialization
            ConsoleCmd.__init__(self, stdin=command_input, prompt='')

            # turn off interactive (bug in ConsoleCmd)
            self.interactive = False
        else:
            ConsoleCmd.__init__(self, prompt=args.prompt)

    def do_echo(self, args):
        """echo ..."""
        args = args.split()
        if _debug: Shell._debug("do_echo %r", args)

        sys.stdout.write(' '.join(args) + '\n')

    def do_sleep(self, args):
        """sleep ..."""
        args = args.split()
        if _debug: Shell._debug("do_sleep %r", args)

        if not args:
            sys.stderr.write("sleep: time required\n")
            return

        sleep_time = float(args[0])
        if _debug: Shell._debug("    - sleep_time: %r", sleep_time)

        time.sleep(sleep_time)


def main():
    global args

    # build a parser for the command line arguments
    parser = ArgumentParser(description=__doc__)

    # sample additional argument to change the prompt
    parser.add_argument(
        "--prompt", type=str,
        default="> ",
        help="change the prompt",
        )

    # accept everything else
    parser.add_argument('args', nargs=argparse.REMAINDER)

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a console
    this_console = Shell()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
