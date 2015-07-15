#!/usr/bin/python

"""
UDP Communications Module
"""

import asyncore
import socket
import cPickle as pickle
import Queue as queue

from time import time as _time

from .debugging import ModuleLogger, bacpypes_debugging

from .core import deferred
from .task import FunctionTask
from .comm import PDU, Server
from .comm import ServiceAccessPoint

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   UDPActor
#
#   Actors are helper objects for a director.  There is one actor for
#   each peer.
#

@bacpypes_debugging
class UDPActor:

    def __init__(self, director, peer):
        if _debug: UDPActor._debug("__init__ %r %r", director, peer)

        # keep track of the director
        self.director = director

        # associated with a peer
        self.peer = peer

        # add a timer
        self.timeout = director.timeout
        if self.timeout > 0:
            self.timer = FunctionTask(self.IdleTimeout)
            self.timer.install_task(_time() + self.timeout)
        else:
            self.timer = None

        # tell the director this is a new actor
        self.director.AddActor(self)

    def IdleTimeout(self):
        if _debug: UDPActor._debug("IdleTimeout")

        # tell the director this is gone
        self.director.RemoveActor(self)

    def indication(self, pdu):
        if _debug: UDPActor._debug("indication %r", pdu)

        # reschedule the timer
        if self.timer:
            self.timer.install_task(_time() + self.timeout)

        # put it in the outbound queue for the director
        self.director.request.put(pdu)

    def response(self, pdu):
        if _debug: UDPActor._debug("response %r", pdu)

        # reschedule the timer
        if self.timer:
            self.timer.install_task(_time() + self.timeout)

        # process this as a response from the director
        self.director.response(pdu)

#
#   UDPPickleActor
#

@bacpypes_debugging
class UDPPickleActor(UDPActor):

    def __init__(self, *args):
        if _debug: UDPPickleActor._debug("__init__ %r", args)
        UDPActor.__init__(self, *args)

    def indication(self, pdu):
        if _debug: UDPPickleActor._debug("indication %r", pdu)

        # pickle the data
        pdu.pduData = pickle.dumps(pdu.pduData)

        # continue as usual
        UDPActor.indication(self, pdu)

    def response(self, pdu):
        if _debug: UDPPickleActor._debug("response %r", pdu)

        # unpickle the data
        try:
            pdu.pduData = pickle.loads(pdu.pduData)
        except:
            UDPPickleActor._exception("pickle error")
            return

        # continue as usual
        UDPActor.response(self, pdu)

#
#   UDPDirector
#

@bacpypes_debugging
class UDPDirector(asyncore.dispatcher, Server, ServiceAccessPoint):

    def __init__(self, address, timeout=0, reuse=False, actorClass=UDPActor, sid=None, sapID=None):
        if _debug: UDPDirector._debug("__init__ %r timeout=%r reuse=%r actorClass=%r sid=%r sapID=%r", address, timeout, reuse, actorClass, sid, sapID)
        Server.__init__(self, sid)
        ServiceAccessPoint.__init__(self, sapID)

        # check the actor class
        if not issubclass(actorClass, UDPActor):
            raise TypeError("actorClass must be a subclass of UDPActor")
        self.actorClass = actorClass

        # save the timeout for actors
        self.timeout = timeout

        # save the address
        self.address = address

        asyncore.dispatcher.__init__(self)

        # ask the dispatcher for a socket
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)

        # if the reuse parameter is provided, set the socket option
        if reuse:
            self.set_reuse_addr()

        # proceed with the bind
        self.bind(address)
        if _debug: UDPDirector._debug("    - getsockname: %r", self.socket.getsockname())

        # allow it to send broadcasts
        self.socket.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )

        # create the request queue
        self.request = queue.Queue()

        # start with an empty peer pool
        self.peers = {}

    def AddActor(self, actor):
        """Add an actor when a new one is connected."""
        if _debug: UDPDirector._debug("AddActor %r", actor)

        self.peers[actor.peer] = actor

        # tell the ASE there is a new client
        if self.serviceElement:
            self.sap_request(addPeer=actor.peer)

    def RemoveActor(self, actor):
        """Remove an actor when the socket is closed."""
        if _debug: UDPDirector._debug("RemoveActor %r", actor)

        del self.peers[actor.peer]

        # tell the ASE the client has gone away
        if self.serviceElement:
            self.sap_request(delPeer=actor.peer)

    def GetActor(self, address):
        return self.peers.get(address, None)

    def handle_connect(self):
        if _debug: deferred(UDPDirector._debug, "handle_connect")

    def readable(self):
        return 1

    def handle_read(self):
        if _debug: deferred(UDPDirector._debug, "handle_read")

        try:
            msg, addr = self.socket.recvfrom(65536)
            if _debug: deferred(UDPDirector._debug, "    - received %d octets from %s", len(msg), addr)

            # send the PDU up to the client
            deferred(self._response, PDU(msg, source=addr))

        except socket.timeout as err:
            deferred(UDPDirector._error, "handle_read socket timeout: %s", err)
        except OSError as err:
            if err.args[0] == 11:
                pass
            else:
                deferred(UDPDirector._error, "handle_read socket error: %s", err)

    def writable(self):
        """Return true iff there is a request pending."""
        return (not self.request.empty())

    def handle_write(self):
        """get a PDU from the queue and send it."""
        if _debug: deferred(UDPDirector._debug, "handle_write")

        try:
            pdu = self.request.get()

            sent = self.socket.sendto(pdu.pduData, pdu.pduDestination)
            if _debug: deferred(UDPDirector._debug, "    - sent %d octets to %s", sent, pdu.pduDestination)

        except OSError as err:
            deferred(UDPDirector._error, "handle_write socket error: %s", err)

    def handle_close(self):
        """Remove this from the monitor when it's closed."""
        if _debug: deferred(UDPDirector._debug, "handle_close")

        self.close()
        self.socket = None

    def indication(self, pdu):
        """Client requests are queued for delivery."""
        if _debug: UDPDirector._debug("indication %r", pdu)

        # get the destination
        addr = pdu.pduDestination

        # get the peer
        peer = self.peers.get(addr, None)
        if not peer:
            peer = self.actorClass(self, addr)

        # send the message
        peer.indication(pdu)

    def _response(self, pdu):
        """Incoming datagrams are routed through an actor."""
        if _debug: UDPDirector._debug("_response %r", pdu)

        # get the destination
        addr = pdu.pduSource

        # get the peer
        peer = self.peers.get(addr, None)
        if not peer:
            peer = self.actorClass(self, addr)

        # send the message
        peer.response(pdu)
