#!/usr/bin/python

"""
Console Logging
"""

import sys
import logging
import argparse

from .debugging import bacpypes_debugging, LoggingFormatter, ModuleLogger

from configparser import ConfigParser as _ConfigParser

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   ConsoleLogHandler
#

def ConsoleLogHandler(loggerRef='', level=logging.DEBUG, color=None):
    """Add a stream handler to stderr with our custom formatter to a logger."""
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

    # make a debug handler
    hdlr = logging.StreamHandler()
    hdlr.setLevel(level)

    # use our formatter
    hdlr.setFormatter(LoggingFormatter(color))

    # add it to the logger
    loggerRef.addHandler(hdlr)

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
        --debug [DBEUG [DEBUG ...]]     attach a console to loggers
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
            help="add console log handler to each debugging logger",
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
            bug_list = []
        elif not result_args.debug:
            # --debug, but no arguments
            bug_list = ["__main__"]
        else:
            # --debug with arguments
            bug_list = result_args.debug

        # attach any that are specified
        if result_args.color:
            for i, debug_name in enumerate(bug_list):
                ConsoleLogHandler(debug_name, color=(i % 6) + 2)
        else:
            for debug_name in bug_list:
                ConsoleLogHandler(debug_name)

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

