#!/usr/bin/env python

"""
B/IP VLAN Helper Classes
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.comm import Client, Server, bind
from bacpypes.pdu import Address, LocalBroadcast, PDU, unpack_ip_addr
from bacpypes.vlan import IPNode

from ..state_machine import ClientStateMachine

from bacpypes.bvllservice import BIPSimple, BIPForeign, BIPBBMD, AnnexJCodec


# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   FauxMultiplexer
#

@bacpypes_debugging
class FauxMultiplexer(Client, Server):

    def __init__(self, addr, network=None, cid=None, sid=None):
        if _debug: FauxMultiplexer._debug("__init__")

        Client.__init__(self, cid)
        Server.__init__(self, sid)

        # allow the address to be cast
        if isinstance(addr, Address):
            self.address = addr
        else:
            self.address = Address(addr)

        # get the unicast and broadcast tuples
        self.unicast_tuple = addr.addrTuple
        self.broadcast_tuple = addr.addrBroadcastTuple

        # make an internal node and bind to it, this takes the place of
        # both the direct port and broadcast port of the real UDPMultiplexer
        self.node = IPNode(addr, network)
        bind(self, self.node)

    def indication(self, pdu):
        if _debug: FauxMultiplexer._debug("indication %r", pdu)

        # check for a broadcast message
        if pdu.pduDestination.addrType == Address.localBroadcastAddr:
            dest = self.broadcast_tuple
            if _debug: FauxMultiplexer._debug("    - requesting local broadcast: %r", dest)

        elif pdu.pduDestination.addrType == Address.localStationAddr:
            dest = unpack_ip_addr(pdu.pduDestination.addrAddr)
            if _debug: FauxMultiplexer._debug("    - requesting local station: %r", dest)

        else:
            raise RuntimeError("invalid destination address type")

        # continue downstream
        self.request(PDU(pdu, source=self.unicast_tuple, destination=dest))

    def confirmation(self, pdu):
        if _debug: FauxMultiplexer._debug("confirmation %r", pdu)

        # the PDU source and destination are tuples, convert them to Address instances
        src = Address(pdu.pduSource)

        # see if the destination was our broadcast address
        if pdu.pduDestination == self.broadcast_tuple:
            dest = LocalBroadcast()
        else:
            dest = Address(pdu.pduDestination)

        # continue upstream
        self.response(PDU(pdu, source=src, destination=dest))

#
#   SnifferNode
#

@bacpypes_debugging
class SnifferNode(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: SnifferNode._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # create a promiscuous node, added to the network
        self.node = IPNode(self.address, vlan, promiscuous=True)
        if _debug: SnifferNode._debug("    - node: %r", self.node)

        # bind this to the node
        bind(self, self.node)


#
#   CodecNode
#

@bacpypes_debugging
class CodecNode(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: CodecNode._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # BACnet/IP interpreter
        self.annexj = AnnexJCodec()

        # fake multiplexer has a VLAN node in it
        self.mux = FauxMultiplexer(self.address, vlan)

        # bind the stack together
        bind(self, self.annexj, self.mux)


#
#   SimpleNode
#

@bacpypes_debugging
class SimpleNode(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: SimpleNode._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # BACnet/IP interpreter
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()

        # fake multiplexer has a VLAN node in it
        self.mux = FauxMultiplexer(self.address, vlan)

        # bind the stack together
        bind(self, self.bip, self.annexj, self.mux)


#
#   ForeignNode
#

@bacpypes_debugging
class ForeignNode(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: ForeignNode._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # BACnet/IP interpreter
        self.bip = BIPForeign()
        self.annexj = AnnexJCodec()

        # fake multiplexer has a VLAN node in it
        self.mux = FauxMultiplexer(self.address, vlan)

        # bind the stack together
        bind(self, self.bip, self.annexj, self.mux)

#
#   BBMDNode
#

@bacpypes_debugging
class BBMDNode(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: BBMDNode._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # BACnet/IP interpreter
        self.bip = BIPBBMD(self.address)
        self.annexj = AnnexJCodec()

        # build an address, full mask
        bdt_address = "%s/32:%d" % self.address.addrTuple
        if _debug: BBMDNode._debug("    - bdt_address: %r", bdt_address)

        # add itself as the first entry in the BDT
        self.bip.add_peer(Address(bdt_address))

        # fake multiplexer has a VLAN node in it
        self.mux = FauxMultiplexer(self.address, vlan)

        # bind the stack together
        bind(self, self.bip, self.annexj, self.mux)

