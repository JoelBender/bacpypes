#!/usr/bin/env python

"""
Template application that uses the ConsoleCmd class.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   ConsoleCmdTemplate
#

@bacpypes_debugging
class ConsoleCmdTemplate(ConsoleCmd):

    def do_echo(self, args):
        """echo ..."""
        args = args.split()
        if _debug: ConsoleCmdTemplate._debug("do_echo %r", args)

        sys.stdout.write(' '.join(args) + '\n')


def main():
    # build a parser for the command line arguments
    parser = ArgumentParser(description=__doc__)

    # sample additional argument to change the prompt
    parser.add_argument(
        "--prompt", type=str,
        default="> ",
        help="change the prompt",
        )

    # parse the command line arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a console
    this_console = ConsoleCmdTemplate(prompt=args.prompt)
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
