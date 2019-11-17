#!/usr/bin/python

"""
Console Logging
"""

import os
import sys
import json
import logging
import logging.handlers
import argparse

from .settings import Settings, settings, os_settings, dict_settings
from .debugging import bacpypes_debugging, LoggingFormatter, ModuleLogger

from configparser import ConfigParser as _ConfigParser

# some debugging
_debug = 0
_log = ModuleLogger(globals())

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
        --route-aware                   turn on route aware
    """

    def __init__(self, **kwargs):
        """Follow normal initialization and add BACpypes arguments."""
        if _debug: ArgumentParser._debug("__init__")
        argparse.ArgumentParser.__init__(self, **kwargs)

        # load settings from the environment
        self.update_os_env()
        if _debug: ArgumentParser._debug("    - os environment")

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
            default=None,
            )

        # add a way to turn on route aware
        self.add_argument("--route-aware",
            help="turn on route aware",
            action="store_true",
            default=None,
            )

    def update_os_env(self):
        """Update the settings with values from the environment, if provided."""
        if _debug: ArgumentParser._debug("update_os_env")

        # use settings function
        os_settings()
        if _debug: ArgumentParser._debug("    - settings: %r", settings)

    def parse_args(self, *args, **kwargs):
        """Parse the arguments as usual, then add default processing."""
        if _debug: ArgumentParser._debug("parse_args")

        # pass along to the parent class
        result_args = argparse.ArgumentParser.parse_args(self, *args, **kwargs)

        # update settings
        self.expand_args(result_args)
        if _debug: ArgumentParser._debug("    - args expanded")

        # add debugging loggers
        self.interpret_debugging(result_args)
        if _debug: ArgumentParser._debug("    - interpreted debugging")

        # return what was parsed and expanded
        return result_args

    def expand_args(self, result_args):
        """Expand the arguments and/or update the settings."""
        if _debug: ArgumentParser._debug("expand_args %r", result_args)

        # check for debug
        if result_args.debug is None:
            if _debug: ArgumentParser._debug("    - debug not specified")
        elif not result_args.debug:
            if _debug: ArgumentParser._debug("    - debug with no args")
            settings.debug.update(["__main__"])
        else:
            if _debug: ArgumentParser._debug("    - debug: %r", result_args.debug)
            settings.debug.update(result_args.debug)

        # check for color
        if result_args.color is None:
            if _debug: ArgumentParser._debug("    - color not specified")
        else:
            if _debug: ArgumentParser._debug("    - color: %r", result_args.color)
            settings.color = result_args.color

        # check for route aware
        if result_args.route_aware is None:
            if _debug: ArgumentParser._debug("    - route_aware not specified")
        else:
            if _debug: ArgumentParser._debug("    - route_aware: %r", result_args.route_aware)
            settings.route_aware = result_args.route_aware

    def interpret_debugging(self, result_args):
        """Take the result of parsing the args and interpret them."""
        if _debug:
            ArgumentParser._debug("interpret_debugging %r", result_args)
            ArgumentParser._debug("    - settings: %r", settings)

        # check to dump labels
        if result_args.buggers:
            loggers = sorted(logging.Logger.manager.loggerDict.keys())
            for loggerName in loggers:
                sys.stdout.write(loggerName + '\n')
            sys.exit(0)

        # keep track of which files are going to be used
        file_handlers = {}

        # loop through the bug list
        for i, debug_name in enumerate(settings.debug):
            color = (i % 6) + 2 if settings.color else None

            debug_specs = debug_name.split(':')
            if (len(debug_specs) == 1) and (not settings.debug_file):
                ConsoleLogHandler(debug_name, color=color)
            else:
                # the debugger name is just the first component
                debug_name = debug_specs.pop(0)

                if debug_specs:
                    file_name = debug_specs.pop(0)
                else:
                    file_name = settings.debug_file

                # if the file is already being used, use the already created handler
                if file_name in file_handlers:
                    handler = file_handlers[file_name]
                else:
                    if debug_specs:
                        maxBytes = int(debug_specs.pop(0))
                    else:
                        maxBytes = settings.max_bytes
                    if debug_specs:
                        backupCount = int(debug_specs.pop(0))
                    else:
                        backupCount = settings.backup_count

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
    read in an INI configuration file.

        --ini INI       provide a separate INI file
    """

    def __init__(self, **kwargs):
        """Follow normal initialization and add BACpypes arguments."""
        if _debug: ConfigArgumentParser._debug("__init__")
        ArgumentParser.__init__(self, **kwargs)

        # add a way to read a configuration file
        self.add_argument('--ini',
            help="device object configuration file",
            default=settings.ini,
            )

    def update_os_env(self):
        """Update the settings with values from the environment, if provided."""
        if _debug: ConfigArgumentParser._debug("update_os_env")

        # start with normal env vars
        ArgumentParser.update_os_env(self)

        # provide a default value for the INI file name
        settings["ini"] = os.getenv("BACPYPES_INI", "BACpypes.ini")

    def expand_args(self, result_args):
        """Take the result of parsing the args and interpret them."""
        if _debug: ConfigArgumentParser._debug("expand_args %r", result_args)

        # read in the configuration file
        config = _ConfigParser()
        config.read(result_args.ini)
        if _debug: _log.debug("    - config: %r", config)

        # check for BACpypes section
        if not config.has_section('BACpypes'):
            raise RuntimeError("INI file with BACpypes section required")

        # convert the contents to an object
        ini_obj = Settings(dict(config.items('BACpypes')))
        if _debug: _log.debug("    - ini_obj: %r", ini_obj)

        # add the object to the parsed arguments
        setattr(result_args, 'ini', ini_obj)

        # continue with normal expansion
        ArgumentParser.expand_args(self, result_args)

#
#   JSONArgumentParser
#


@bacpypes_debugging
class JSONArgumentParser(ArgumentParser):

    """
    JSONArgumentParser extends the ArgumentParser with the functionality to
    read in a JSON configuration file.

        --json JSON    provide a separate JSON file
    """

    def __init__(self, **kwargs):
        """Follow normal initialization and add BACpypes arguments."""
        if _debug: JSONArgumentParser._debug("__init__")
        ArgumentParser.__init__(self, **kwargs)

        # add a way to read a configuration file
        self.add_argument('--json',
            help="configuration file",
            default=settings.json,
            )

    def update_os_env(self):
        """Update the settings with values from the environment, if provided."""
        if _debug: JSONArgumentParser._debug("update_os_env")

        # start with normal env vars
        ArgumentParser.update_os_env(self)

        # provide a default value for the INI file name
        settings["json"] = os.getenv("BACPYPES_JSON", "BACpypes.json")

    def expand_args(self, result_args):
        """Take the result of parsing the args and interpret them."""
        if _debug: JSONArgumentParser._debug("expand_args %r", result_args)

        # read in the settings file
        try:
            with open(result_args.json) as json_file:
                json_obj = json.load(json_file, object_hook=Settings)
                if _debug: JSONArgumentParser._debug("    - json_obj: %r", json_obj)
        except FileNotFoundError:
            raise RuntimeError("settings file not found: %r\n" % (settings.json,))

        # look for settings
        if "bacpypes" in json_obj:
            dict_settings(**json_obj.bacpypes)
            if _debug: JSONArgumentParser._debug("    - settings: %r", settings)

        # add the object to the parsed arguments
        setattr(result_args, 'json', json_obj)

        # continue with normal expansion
        ArgumentParser.expand_args(self, result_args)
