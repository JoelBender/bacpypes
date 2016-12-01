#!/usr/bin/python

"""
Console Logging
"""

import os
import sys
import logging
import logging.handlers
import argparse

from .debugging import bacpypes_debugging, LoggingFormatter, ModuleLogger

from ConfigParser import ConfigParser as _ConfigParser

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# configuration
BACPYPES_DEBUG = os.getenv('BACPYPES_DEBUG', '')
BACPYPES_MAXBYTES = int(os.getenv('BACPYPES_MAXBYTES', 1048576))
BACPYPES_BACKUPCOUNT = int(os.getenv('BACPYPES_BACKUPCOUNT', 5))

#
#   ConsoleLogHandler
#

def ConsoleLogHandler(loggerRef='', handler=None, level=logging.DEBUG, color=None):
    """Add a handler to stderr with our custom formatter to a logger."""
    if isinstance(loggerRef, logging.Logger):
        pass

    elif isinstance(loggerRef, str):
        # check for root
        if not loggerRef:
            loggerRef = _log

        # check for a valid logger name
        elif loggerRef not in logging.Logger.manager.loggerDict:
            raise RuntimeError("not a valid logger name: %r" % (loggerRef,))

        # get the logger
        loggerRef = logging.getLogger(loggerRef)

    else:
        raise RuntimeError("not a valid logger reference: %r" % (loggerRef,))

    # see if this (or its parent) is a module level logger
    if hasattr(loggerRef, 'globs'):
        loggerRef.globs['_debug'] += 1
    elif hasattr(loggerRef.parent, 'globs'):
        loggerRef.parent.globs['_debug'] += 1

    # make a handler if one wasn't provided
    if not handler:
        handler = logging.StreamHandler()
        handler.setLevel(level)

    # use our formatter
    handler.setFormatter(LoggingFormatter(color))

    # add it to the logger
    loggerRef.addHandler(handler)

    # make sure the logger has at least this level
    loggerRef.setLevel(level)

#
#   ArgumentParser
#

@bacpypes_debugging
class ArgumentParser(argparse.ArgumentParser):

    """
    ArgumentParser extends the one with the same name from the argparse module
    by adding the common command line arguments found in BACpypes applications.

        --buggers                       list the debugging logger names
        --debug [DEBUG [DEBUG ...]]     attach a handler to loggers
        --color                         debug in color
    """

    def __init__(self, **kwargs):
        """Follow normal initialization and add BACpypes arguments."""
        if _debug: ArgumentParser._debug("__init__")
        argparse.ArgumentParser.__init__(self, **kwargs)

        # add a way to get a list of the debugging hooks
        self.add_argument("--buggers",
            help="list the debugging logger names",
            action="store_true",
            )

        # add a way to attach debuggers
        self.add_argument('--debug', nargs='*',
            help="add a log handler to each debugging logger",
            )

        # add a way to turn on color debugging
        self.add_argument("--color",
            help="turn on color debugging",
            action="store_true",
            )

    def parse_args(self, *args, **kwargs):
        """Parse the arguments as usual, then add default processing."""
        if _debug: ArgumentParser._debug("parse_args")

        # pass along to the parent class
        result_args = argparse.ArgumentParser.parse_args(self, *args, **kwargs)

        # check to dump labels
        if result_args.buggers:
            loggers = sorted(logging.Logger.manager.loggerDict.keys())
            for loggerName in loggers:
                sys.stdout.write(loggerName + '\n')
            sys.exit(0)

        # check for debug
        if result_args.debug is None:
            # --debug not specified
            result_args.debug = []
        elif not result_args.debug:
            # --debug, but no arguments
            result_args.debug = ["__main__"]

        # check for debugging from the environment
        if BACPYPES_DEBUG:
            result_args.debug.extend(BACPYPES_DEBUG.split())

        # keep track of which files are going to be used
        file_handlers = {}

        # loop through the bug list
        for i, debug_name in enumerate(result_args.debug):
            color = (i % 6) + 2 if result_args.color else None

            debug_specs = debug_name.split(':')
            if len(debug_specs) == 1:
                ConsoleLogHandler(debug_name, color=color)
            else:
                # the debugger name is just the first component
                debug_name = debug_specs[0]

                # if the file is already being used, use the already created handler
                file_name = debug_specs[1]
                if file_name in file_handlers:
                    handler = file_handlers[file_name]
                else:
                    if len(debug_specs) >= 3:
                        maxBytes = int(debug_specs[2])
                    else:
                        maxBytes = BACPYPES_MAXBYTES
                    if len(debug_specs) >= 4:
                        backupCount = int(debug_specs[3])
                    else:
                        backupCount = BACPYPES_BACKUPCOUNT

                    # create a handler
                    handler = logging.handlers.RotatingFileHandler(
                        file_name, maxBytes=maxBytes, backupCount=backupCount,
                        )
                    handler.setLevel(logging.DEBUG)

                    # save it for more than one instance
                    file_handlers[file_name] = handler

                # use this handler, no color
                ConsoleLogHandler(debug_name, handler=handler)

        # return what was parsed
        return result_args

#
#   ConfigArgumentParser
#

@bacpypes_debugging
class ConfigArgumentParser(ArgumentParser):

    """
    ConfigArgumentParser extends the ArgumentParser with the functionality to
    read in a configuration file.

        --ini INI       provide a separate INI file
    """

    def __init__(self, **kwargs):
        """Follow normal initialization and add BACpypes arguments."""
        if _debug: ConfigArgumentParser._debug("__init__")
        ArgumentParser.__init__(self, **kwargs)

        # add a way to read a configuration file
        self.add_argument('--ini',
            help="device object configuration file",
            default="BACpypes.ini",
            )

    def parse_args(self, *args, **kwargs):
        """Parse the arguments as usual, then add default processing."""
        if _debug: ConfigArgumentParser._debug("parse_args")

        # pass along to the parent class
        result_args = ArgumentParser.parse_args(self, *args, **kwargs)

        # read in the configuration file
        config = _ConfigParser()
        config.read(result_args.ini)
        if _debug: _log.debug("    - config: %r", config)

        # check for BACpypes section
        if not config.has_section('BACpypes'):
            raise RuntimeError("INI file with BACpypes section required")

        # convert the contents to an object
        ini_obj = type('ini', (object,), dict(config.items('BACpypes')))
        if _debug: _log.debug("    - ini_obj: %r", ini_obj)

        # add the object to the parsed arguments
        setattr(result_args, 'ini', ini_obj)

        # return what was parsed
        return result_args

