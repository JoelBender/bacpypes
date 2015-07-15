#!/usr/bin/python

"""
Virtual Local Area Network
"""

import random
from copy import deepcopy

from .errors import ConfigurationError
from .debugging import ModuleLogger, bacpypes_debugging

from .core import deferred
from .pdu import Address
from .comm import Server

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Network
#

@bacpypes_debugging
class Network:

    def __init__(self, dropPercent=0.0):
        if _debug: Network._debug("__init__ dropPercent=%r", dropPercent)

        self.nodes = []
        self.dropPercent = dropPercent

    def add_node(self, node):
        """ Add a node to this network, let the node know which network it's on. """
        if _debug: Network._debug("add_node %r", node)

        self.nodes.append(node)
        node.lan = self

    def remove_node(self, node):
        """ Remove a node from this network. """
        if _debug: Network._debug("remove_node %r", node)

        self.nodes.remove(node)
        node.lan = None

    def process_pdu(self, pdu):
        """ Process a PDU by sending a copy to each node as dictated by the
            addressing and if a node is promiscuous.
        """
        if _debug: Network._debug("process_pdu %r", pdu)

        if self.dropPercent != 0.0:
            if (random.random() * 100.0) < self.dropPercent:
                if _debug: Network._debug("    - packet dropped")
                return

        if not pdu.pduDestination or not isinstance(pdu.pduDestination, Address):
            raise RuntimeError("invalid destination address")

        elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
            for n in self.nodes:
                if (pdu.pduSource != n.address):
                    n.response(deepcopy(pdu))

        elif pdu.pduDestination.addrType == Address.localStationAddr:
            for n in self.nodes:
                if n.promiscuous or (pdu.pduDestination == n.address):
                    n.response(deepcopy(pdu))

        else:
            raise RuntimeError("invalid destination address type")

    def __len__(self):
        """ Simple way to determine the number of nodes in the network. """
        if _debug: Network._debug("__len__")
        return len(self.nodes)

#
#   Node
#

@bacpypes_debugging
class Node(Server):

    def __init__(self, addr, lan=None, promiscuous=False, spoofing=False, sid=None):
        if _debug:
            Node._debug("__init__ %r lan=%r promiscuous=%r spoofing=%r sid=%r",
                addr, lan, promiscuous, spoofing, sid
                )
        Server.__init__(self, sid)

        if not isinstance(addr, Address):
            raise TypeError("addr must be an address")

        self.lan = None
        self.address = addr

        # bind to a lan if it was provided
        if lan:
            self.bind(lan)

        # might receive all packets and might spoof
        self.promiscuous = promiscuous
        self.spoofing = spoofing

    def bind(self, lan):
        """bind to a LAN."""
        if _debug: Node._debug("bind %r", lan)

        lan.add_node(self)

    def indication(self, pdu):
        """Send a message."""
        if _debug: Node._debug("indication %r", pdu)

        # make sure we're connected
        if not self.lan:
            raise ConfigurationError("unbound node")

        # if the pduSource is unset, fill in our address, otherwise
        # leave it alone to allow for simulated spoofing
        if pdu.pduSource is None:
            pdu.pduSource = self.address
        elif (not self.spoofing) and (pdu.pduSource != self.address):
            raise RuntimeError("spoofing address conflict")

        # actual network delivery is deferred
        deferred(self.lan.process_pdu, pdu)
