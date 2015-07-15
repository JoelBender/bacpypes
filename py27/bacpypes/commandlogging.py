#!/usr/bin/python

"""
Command Logging
"""

import logging

from .debugging import Logging, LoggingFormatter, ModuleLogger
from .comm import PDU, Client, Server

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   CommandLoggingHandler
#

class CommandLoggingHandler(logging.Handler):

    def __init__(self, commander, addr, loggerName):
        logging.Handler.__init__(self, logging.DEBUG)
        self.setFormatter(LoggingFormatter())

        # save where this stuff goes
        self.commander = commander
        self.addr = addr
        self.loggerName = loggerName

    def emit(self, record):
        # use the basic formatting
        msg = self.format(record) + '\n'

        # tell the commander
        self.commander.emit(msg, self.addr)

#
#   CommandLogging
#

class CommandLogging(Logging):

    def __init__(self):
        if _debug: CommandLogging._debug("__init__")

        # handlers, self.handlers[addr][logger] = handler
        self.handlers = {}

    def process_command(self, cmd, addr):
        if _debug: CommandLogging._debug("process_command %r", cmd, addr)

        # get the address, find (or build) its list of handlers
        if addr not in self.handlers:
            handlers = self.handlers[addr] = {}
        else:
            handlers = self.handlers[addr]

        # split the command into a list of args
        args = cmd.strip().split()

        # get the logger name and logger
        logger = None

        # second arg is optional, but always a logger name
        if len(args) > 1:
            loggerName = args[1]
            if loggerName in logging.Logger.manager.loggerDict:
                logger = logging.getLogger(loggerName)

        if not args:
            response = '-'

        elif args[0] == '?':
            if len(args) == 1:
                if not handlers:
                    response = 'no handlers'
                else:
                    response = "handlers: " + ', '.join(loggerName for loggerName in handlers)
            elif not logger:
                response = 'not a valid logger name'
            elif loggerName in handlers:
                response = 'yes'
            else:
                response = 'no'

        elif args[0] == '+':
            if not logger:
                response = 'not a valid logger name'
            elif loggerName in handlers:
                response = loggerName + ' already has a handler'
            else:
                handler = CommandLoggingHandler(self, addr, loggerName)
                handlers[loggerName] = handler

                # add it to the logger
                logger.addHandler(handler)
                if not addr:
                    response = "handler to %s added" % (loggerName,)
                else:
                    response = "handler from %s to %s added" % (addr, loggerName)

        elif args[0] == '-':
            if not logger:
                response = 'not a valid logger name'
            elif loggerName not in handlers:
                response = 'no handler for ' + loggerName
            else:
                handler = handlers[loggerName]
                del handlers[loggerName]

                # remove it from the logger
                logger.removeHandler(handler)
                if not addr:
                    response = "handler to %s removed" % (loggerName,)
                else:
                    response = "handler from %s to %s removed" % (addr, loggerName)

        else:
            if _debug: CommandLogging._warning("bad command %r", cmd)
            response = 'bad command'

        # return the response
        return response + '\n'

    def emit(self, msg, addr):
        if _debug: CommandLogging._debug("emit %r %r", msg, addr)

        raise NotImplementedError("emit must be overridden")

#
#   CommandLoggingServer
#

class CommandLoggingServer(CommandLogging, Server, Logging):

    def __init__(self):
        if _debug: CommandLoggingServer._debug("__init__")
        CommandLogging.__init__(self)

    def indication(self, pdu):
        if _debug: CommandLoggingServer._debug("indication %r", pdu)
        addr = pdu.pduSource
        resp = self.process_command(pdu.pduData, addr)
        self.response(PDU(resp, source=addr))

    def emit(self, msg, addr):
        if _debug: CommandLoggingServer._debug("emit %r %r", msg, addr)

        # pass upstream to the client
        self.response(PDU(msg, source=addr))

#
#   CommandLoggingClient
#

class CommandLoggingClient(CommandLogging, Client, Logging):

    def __init__(self):
        if _debug: CommandLoggingClient._debug("__init__")
        CommandLogging.__init__(self)

    def confirmation(self, pdu):
        if _debug: CommandLoggingClient._debug("confirmation %r", pdu)
        addr = pdu.pduSource
        resp = self.process_command(pdu.pduData, addr)
        self.request(PDU(resp, destination=addr))

    def emit(self, msg, addr):
        if _debug: CommandLoggingClient._debug("emit %r %r", msg, addr)

        # pass downstream to the server
        self.request(PDU(msg, destination=addr))
