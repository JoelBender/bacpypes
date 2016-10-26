#!/usr/bin/env python

"""
Console Communications
"""

import sys
import asyncore

from .debugging import bacpypes_debugging, ModuleLogger

from .core import deferred
from .comm import PDU, Client, Server

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   asyncore.file_dispatcher is only available in Unix.  This is a hack that
#   allows the ConsoleClient and ConsoleServer to initialize on Windows.
#

try:
    asyncore.file_dispatcher
except:
    class _barf:
        def __init__(self, *args):
            pass
    asyncore.file_dispatcher = _barf


#
#   ConsoleClient
#

@bacpypes_debugging
class ConsoleClient(asyncore.file_dispatcher, Client):

    def __init__(self, cid=None):
        if _debug: ConsoleClient._debug("__init__ cid=%r", cid)
        asyncore.file_dispatcher.__init__(self, sys.stdin)
        Client.__init__(self, cid)

    def readable(self):
        return True     # We are always happy to read

    def writable(self):
        return False    # we don't have anything to write

    def handle_read(self):
        if _debug: deferred(ConsoleClient._debug, "handle_read")

        # read from stdin and encode it
        data = sys.stdin.read().encode('utf-8')
        if _debug: deferred(ConsoleClient._debug, "    - data: %r", data)

        # make a PDU and send it downstream
        deferred(self.request, PDU(data))

    def confirmation(self, pdu):
        if _debug: deferred(ConsoleClient._debug, "confirmation %r", pdu)
        try:
            # decode the data
            data = pdu.pduData.decode('utf-8')
            if _debug: deferred(ConsoleClient._debug, "    - data: %r", data)

            # send it out
            sys.stdout.write(data)
        except Exception as err:
            ConsoleClient._exception("Confirmation sys.stdout.write exception: %r", err)

#
#   ConsoleServer
#

@bacpypes_debugging
class ConsoleServer(asyncore.file_dispatcher, Server):

    def __init__(self, sid=None):
        if _debug: ConsoleServer._debug("__init__ sid=%r", sid)
        asyncore.file_dispatcher.__init__(self, sys.stdin)
        Server.__init__(self, sid)

    def readable(self):
        return True     # We are always happy to read

    def writable(self):
        return False    # we don't have anything to write

    def handle_read(self):
        if _debug: deferred(ConsoleServer._debug, "handle_read")

        # read from stdin and encode it
        data = sys.stdin.read().encode('utf-8')
        if _debug: deferred(ConsoleServer._debug, "    - data: %r", data)

        # make a PDU and send it upstream
        deferred(self.response, PDU(data))

    def indication(self, pdu):
        if _debug: deferred(ConsoleServer._debug, "indication %r", pdu)
        try:
            # decode the data
            data = pdu.pduData.decode('utf-8')
            if _debug: deferred(ConsoleServer._debug, "    - data: %r", data)

            # send it out
            sys.stdout.write(data)
        except Exception as err:
            ConsoleServer._exception("indication sys.stdout.write exception: %r", err)
