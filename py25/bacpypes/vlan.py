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

class Network:

    def __init__(self, broadcast_address=None, drop_percent=0.0):
        if _debug: Network._debug("__init__ broadcast_address=%r drop_percent=%r", broadcast_address, drop_percent)

        self.nodes = []
        self.broadcast_address = broadcast_address
        self.drop_percent = drop_percent

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

        # randomly drop a packet
        if self.drop_percent != 0.0:
            if (random.random() * 100.0) < self.drop_percent:
                if _debug: Network._debug("    - packet dropped")
                return

        if pdu.pduDestination == self.broadcast_address:
            for n in self.nodes:
                if (pdu.pduSource != n.address):
                    n.response(deepcopy(pdu))
        else:
            for n in self.nodes:
                if n.promiscuous or (pdu.pduDestination == n.address):
                    n.response(deepcopy(pdu))

    def __len__(self):
        """ Simple way to determine the number of nodes in the network. """
        if _debug: Network._debug("__len__")
        return len(self.nodes)

bacpypes_debugging(Network)

#
#   Node
#

class Node(Server):

    def __init__(self, addr, lan=None, promiscuous=False, spoofing=False, sid=None):
        if _debug:
            Node._debug("__init__ %r lan=%r promiscuous=%r spoofing=%r sid=%r",
                addr, lan, promiscuous, spoofing, sid
                )
        Server.__init__(self, sid)

        self.lan = None
        self.address = addr

        # bind to a lan if it was provided
        if lan is not None:
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

bacpypes_debugging(Node)

#
#   IPNetwork
#

class IPNetwork(Network):

    """
    IPNetwork instances are Network objects where the addresses on the
    network are tuples that would be used for sockets like ('1.2.3.4', 5).
    The first node added to the network sets the broadcast address, like
    ('1.2.3.255', 5) and the other nodes must have the same tuple.
    """

    def __init__(self):
        if _debug: IPNetwork._debug("__init__")
        Network.__init__(self)

    def add_node(self, node):
        if _debug: IPNetwork._debug("add_node %r", node)

        # first node sets the broadcast tuple, other nodes much match
        if not self.nodes:
            self.broadcast_address = node.addrBroadcastTuple
        elif node.addrBroadcastTuple != self.broadcast_address:
            raise ValueError("nodes must all have the same broadcast tuple")

        # continue along
        Network.add_node(self, node)

bacpypes_debugging(IPNetwork)

#
#   IPNode
#

class IPNode(Node):

    """
    An IPNode is a Node where the address is an Address that has an address
    tuple and a broadcast tuple that would be used for socket communications.
    """

    def __init__(self, addr, lan=None):
        if _debug: IPNode._debug("__init__ %r lan=%r", addr, lan)

        # make sure it's an Address that has appropriate pieces
        if not isinstance(addr, Address) or (not hasattr(addr, 'addrTuple')) \
            or (not hasattr(addr, 'addrBroadcastTuple')):
            raise ValueError("malformed address")

        # save the address information
        self.addrTuple = addr.addrTuple
        self.addrBroadcastTuple = addr.addrBroadcastTuple

        # continue initializing
        Node.__init__(self, addr.addrTuple, lan=lan)

bacpypes_debugging(IPNode)

