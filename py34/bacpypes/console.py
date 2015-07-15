#!/usr/bin/env python

"""
Console Communications
"""

import sys
import asyncore

from .debugging import Logging, ModuleLogger

from .core import deferred
from .comm import PDU, Client, Server

# some debugging
_debug = 0
_log = ModuleLogger(globals())

try:
    asyncore.file_dispatcher
except:
    class _barf: pass
    asyncore.file_dispatcher = _barf

#
#   ConsoleClient
#

class ConsoleClient(asyncore.file_dispatcher, Client, Logging):

    def __init__(self, cid=None):
        ConsoleClient._debug("__init__ cid=%r", cid)
        asyncore.file_dispatcher.__init__(self, sys.stdin)
        Client.__init__(self, cid)

    def readable(self):
        return True     # We are always happy to read

    def writable(self):
        return False    # we don't have anything to write

    def handle_read(self):
        deferred(ConsoleClient._debug, "handle_read")
        data = sys.stdin.read()
        deferred(ConsoleClient._debug, "    - data: %r", data)
        deferred(self.request, PDU(data))

    def confirmation(self, pdu):
        deferred(ConsoleClient._debug, "confirmation %r", pdu)
        try:
            sys.stdout.write(pdu.pduData)
        except Exception as err:
            ConsoleClient._exception("Confirmation sys.stdout.write exception: %r", err)

#
#   ConsoleServer
#

class ConsoleServer(asyncore.file_dispatcher, Server, Logging):

    def __init__(self, sid=None):
        ConsoleServer._debug("__init__ sid=%r", sid)
        asyncore.file_dispatcher.__init__(self, sys.stdin)
        Server.__init__(self, sid)

    def readable(self):
        return True     # We are always happy to read

    def writable(self):
        return False    # we don't have anything to write

    def handle_read(self):
        deferred(ConsoleServer._debug, "handle_read")
        data = sys.stdin.read()
        deferred(ConsoleServer._debug, "    - data: %r", data)
        deferred(self.response, PDU(data))

    def indication(self, pdu):
        deferred(ConsoleServer._debug, "Indication %r", pdu)
        try:
            sys.stdout.write(pdu.pduData)
        except Exception as err:
            ConsoleServer._exception("Indication sys.stdout.write exception: %r", err)
