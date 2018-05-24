#!/usr/bin/python

"""
Virtual Local Area Network
"""

import random
import socket
import struct
from copy import deepcopy

from .errors import ConfigurationError
from .debugging import ModuleLogger, bacpypes_debugging

from .pdu import Address
from .comm import Client, Server, bind
from .task import OneShotFunction

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Network
#

@bacpypes_debugging
class Network:

    def __init__(self, name='', broadcast_address=None, drop_percent=0.0):
        if _debug: Network._debug("__init__ name=%r broadcast_address=%r drop_percent=%r", name, broadcast_address, drop_percent)

        self.name = name
        self.nodes = []

        self.broadcast_address = broadcast_address
        self.drop_percent = drop_percent

        # point to a TrafficLog instance
        self.traffic_log = None

    def add_node(self, node):
        """ Add a node to this network, let the node know which network it's on. """
        if _debug: Network._debug("add_node %r", node)

        self.nodes.append(node)
        node.lan = self

        # update the node name
        if not node.name:
            node.name = '%s:%s' % (self.name, node.address)

    def remove_node(self, node):
        """ Remove a node from this network. """
        if _debug: Network._debug("remove_node %r", node)

        self.nodes.remove(node)
        node.lan = None

    def process_pdu(self, pdu):
        """ Process a PDU by sending a copy to each node as dictated by the
            addressing and if a node is promiscuous.
        """
        if _debug: Network._debug("process_pdu(%s) %r", self.name, pdu)

        # if there is a traffic log, call it with the network name and pdu
        if self.traffic_log:
            self.traffic_log(self.name, pdu)

        # randomly drop a packet
        if self.drop_percent != 0.0:
            if (random.random() * 100.0) < self.drop_percent:
                if _debug: Network._debug("    - packet dropped")
                return

        if pdu.pduDestination == self.broadcast_address:
            if _debug: Network._debug("    - broadcast")
            for node in self.nodes:
                if (pdu.pduSource != node.address):
                    if _debug: Network._debug("    - match: %r", node)
                    node.response(deepcopy(pdu))
        else:
            if _debug: Network._debug("    - unicast")
            for node in self.nodes:
                if node.promiscuous or (pdu.pduDestination == node.address):
                    if _debug: Network._debug("    - match: %r", node)
                    node.response(deepcopy(pdu))

    def __len__(self):
        """ Simple way to determine the number of nodes in the network. """
        return len(self.nodes)

#
#   Node
#

@bacpypes_debugging
class Node(Server):

    def __init__(self, addr, lan=None, name='', promiscuous=False, spoofing=False, sid=None):
        if _debug:
            Node._debug("__init__ %r lan=%r name=%r, promiscuous=%r spoofing=%r sid=%r",
                addr, lan, name, promiscuous, spoofing, sid
                )
        Server.__init__(self, sid)

        self.lan = None
        self.address = addr
        self.name = name

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
        if _debug: Node._debug("indication(%s) %r", self.name, pdu)

        # make sure we're connected
        if not self.lan:
            raise ConfigurationError("unbound node")

        # if the pduSource is unset, fill in our address, otherwise
        # leave it alone to allow for simulated spoofing
        if pdu.pduSource is None:
            pdu.pduSource = self.address
        elif (not self.spoofing) and (pdu.pduSource != self.address):
            raise RuntimeError("spoofing address conflict")

        # actual network delivery is a zero-delay task
        OneShotFunction(self.lan.process_pdu, pdu)

    def __repr__(self):
        return "<%s(%s) at %s>" % (
            self.__class__.__name__,
            self.name,
            hex(id(self)),
            )


#
#   IPNetwork
#

@bacpypes_debugging
class IPNetwork(Network):

    """
    IPNetwork instances are Network objects where the addresses on the
    network are tuples that would be used for sockets like ('1.2.3.4', 5).
    The first node added to the network sets the broadcast address, like
    ('1.2.3.255', 5) and the other nodes must have the same tuple.
    """

    def __init__(self, name=''):
        if _debug: IPNetwork._debug("__init__")
        Network.__init__(self, name=name)

    def add_node(self, node):
        if _debug: IPNetwork._debug("add_node %r", node)

        # first node sets the broadcast tuple, other nodes much match
        if not self.nodes:
            self.broadcast_address = node.addrBroadcastTuple
        elif node.addrBroadcastTuple != self.broadcast_address:
            raise ValueError("nodes must all have the same broadcast tuple")

        # continue along
        Network.add_node(self, node)


#
#   IPNode
#

@bacpypes_debugging
class IPNode(Node):

    """
    An IPNode is a Node where the address is an Address that has an address
    tuple and a broadcast tuple that would be used for socket communications.
    """

    def __init__(self, addr, lan=None, promiscuous=False, spoofing=False, sid=None):
        if _debug: IPNode._debug("__init__ %r lan=%r", addr, lan)

        # make sure it's an Address that has appropriate pieces
        if not isinstance(addr, Address) or (not hasattr(addr, 'addrTuple')) \
            or (not hasattr(addr, 'addrBroadcastTuple')):
            raise ValueError("malformed address")

        # save the address information
        self.addrTuple = addr.addrTuple
        self.addrBroadcastTuple = addr.addrBroadcastTuple

        # continue initializing
        Node.__init__(self, addr.addrTuple, lan=lan, promiscuous=promiscuous, spoofing=spoofing, sid=sid)


#
#   IPRouterNode
#

@bacpypes_debugging
class IPRouterNode(Client):

    def __init__(self, router, addr, lan):
        if _debug: IPRouterNode._debug("__init__ %r %r lan=%r", router, addr, lan)

        # save the references to the router for packets and the lan for debugging
        self.router = router
        self.lan = lan

        # make ourselves an IPNode and bind to it
        self.node = IPNode(addr, lan=lan, promiscuous=True, spoofing=True)
        bind(self, self.node)

        # save our mask and subnet
        self.addrMask = addr.addrMask
        self.addrSubnet = addr.addrSubnet

    def confirmation(self, pdu):
        if _debug: IPRouterNode._debug("confirmation %r", pdu)

        self.router.process_pdu(self, pdu)

    def process_pdu(self, pdu):
        if _debug: IPRouterNode._debug("process_pdu %r", pdu)

        # pass it downstream
        self.request(pdu)

    def __repr__(self):
        return "<%s for %s>" % (self.__class__.__name__, self.lan.name)


#
#   IPRouter
#

@bacpypes_debugging
class IPRouter:

    def __init__(self):
        if _debug: IPRouter._debug("__init__")

        # connected network nodes
        self.nodes = []

    def add_network(self, addr, lan):
        if _debug: IPRouter._debug("add_network %r %r", addr, lan)

        node = IPRouterNode(self, addr, lan)
        if _debug: IPRouter._debug("    - node: %r", node)

        self.nodes.append(node)

    def process_pdu(self, node, pdu):
        if _debug: IPRouter._debug("process_pdu %r %r", node, pdu)

        # unpack the address part of the destination
        addrstr = socket.inet_aton(pdu.pduDestination[0])
        ipaddr = struct.unpack('!L', addrstr)[0]
        if _debug: IPRouter._debug("    - ipaddr: %r", ipaddr)

        # loop through the other nodes
        for inode in self.nodes:
            if inode is not node:
                if (ipaddr & inode.addrMask) == inode.addrSubnet:
                    if _debug: IPRouter._debug("    - inode: %r", inode)
                    inode.process_pdu(pdu)

