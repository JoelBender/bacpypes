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
            self.timer = FunctionTask(self.idle_timeout)
            self.timer.install_task(_time() + self.timeout)
        else:
            self.timer = None

        # tell the director this is a new actor
        self.director.add_actor(self)

    def idle_timeout(self):
        if _debug: UDPActor._debug("idle_timeout")

        # tell the director this is gone
        self.director.del_actor(self)

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

    def handle_error(self, error=None):
        if _debug: UDPActor._debug("handle_error %r", error)

        # pass along to the director
        if error is not None:
            self.director.actor_error(self, error)

bacpypes_debugging(UDPActor)

#
#   UDPPickleActor
#

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

bacpypes_debugging(UDPPickleActor)

#
#   UDPDirector
#

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

    def add_actor(self, actor):
        """Add an actor when a new one is connected."""
        if _debug: UDPDirector._debug("add_actor %r", actor)

        self.peers[actor.peer] = actor

        # tell the ASE there is a new client
        if self.serviceElement:
            self.sap_request(add_actor=actor)

    def del_actor(self, actor):
        """Remove an actor when the socket is closed."""
        if _debug: UDPDirector._debug("del_actor %r", actor)

        del self.peers[actor.peer]

        # tell the ASE the client has gone away
        if self.serviceElement:
            self.sap_request(del_actor=actor)

    def actor_error(self, actor, error):
        if _debug: UDPDirector._debug("actor_error %r %r", actor, error)

        # tell the ASE the actor had an error
        if self.serviceElement:
            self.sap_request(actor_error=actor, error=error)

    def get_actor(self, address):
        return self.peers.get(address, None)

    def handle_connect(self):
        if _debug: UDPDirector._debug("handle_connect")

    def readable(self):
        return 1

    def handle_read(self):
        if _debug: UDPDirector._debug("handle_read")

        try:
            msg, addr = self.socket.recvfrom(65536)
            if _debug: UDPDirector._debug("    - received %d octets from %s", len(msg), addr)

            # send the PDU up to the client
            deferred(self._response, PDU(msg, source=addr))

        except socket.timeout, err:
            if _debug: UDPDirector._debug("    - socket timeout: %s", err)

        except socket.error, err:
            if err.args[0] == 11:
                pass
            else:
                if _debug: UDPDirector._debug("    - socket error: %s", err)

                # let the director handle the error
                self.handle_error(err)

    def writable(self):
        """Return true iff there is a request pending."""
        return (not self.request.empty())

    def handle_write(self):
        """get a PDU from the queue and send it."""
        if _debug: UDPDirector._debug("handle_write")

        try:
            pdu = self.request.get()

            sent = self.socket.sendto(pdu.pduData, pdu.pduDestination)
            if _debug: UDPDirector._debug("    - sent %d octets to %s", sent, pdu.pduDestination)

        except socket.error, err:
            if _debug: UDPDirector._debug("    - socket error: %s", err)

            # get the peer
            peer = self.peers.get(pdu.pduDestination, None)
            if peer:
                # let the actor handle the error
                peer.handle_error(err)
            else:
                # let the director handle the error
                self.handle_error(err)

    def handle_close(self):
        """Remove this from the monitor when it's closed."""
        if _debug: UDPDirector._debug("handle_close")

        self.close()
        self.socket = None

    def handle_error(self, error=None):
        """Handle an error..."""
        if _debug: UDPDirector._debug("handle_error %r", error)

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

bacpypes_debugging(UDPDirector)
