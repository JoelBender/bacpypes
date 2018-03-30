#!/usr/bin/env python

"""
Network NPDU Helper Classes
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.comm import Client, Server
from bacpypes.pdu import PDU
from bacpypes.npdu import npdu_types, NPDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class NPDUCodec(Client, Server):

    def __init__(self):
        if _debug: NPDUCodec._debug("__init__")

        Client.__init__(self)
        Server.__init__(self)

    def indication(self, npdu):
        if _debug: NPDUCodec._debug("indication %r", npdu)

        # first as a generic NPDU
        xpdu = NPDU()
        npdu.encode(xpdu)

        # now as a vanilla PDU
        ypdu = PDU()
        xpdu.encode(ypdu)
        if _debug: NPDUCodec._debug("    - encoded: %r", ypdu)

        # send it downstream
        self.request(ypdu)

    def confirmation(self, pdu):
        if _debug: NPDUCodec._debug("confirmation %r", pdu)

        # decode as a generic NPDU
        xpdu = NPDU()
        xpdu.decode(pdu)

        # drop application layer messages
        if xpdu.npduNetMessage is None:
            return

        # do a deeper decode of the NPDU
        ypdu = npdu_types[xpdu.npduNetMessage]()
        ypdu.decode(xpdu)

        # send it upstream
        self.response(ypdu)

