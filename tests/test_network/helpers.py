#!/usr/bin/env python

"""
Network VLAN Helper Classes
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.comm import Client, Server, ApplicationServiceElement, bind
from bacpypes.pdu import Address, PDU
from bacpypes.npdu import npdu_types, NPDU
from bacpypes.vlan import Node

from bacpypes.app import DeviceInfoCache, Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement

from bacpypes.object import register_object_type
from bacpypes.local.device import LocalDeviceObject
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices

from ..state_machine import ClientStateMachine

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


#
#   SnifferStateMachine
#

@bacpypes_debugging
class SnifferStateMachine(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: SnifferStateMachine._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # create a promiscuous node, added to the network
        self.node = Node(self.address, vlan, promiscuous=True)
        if _debug: SnifferStateMachine._debug("    - node: %r", self.node)

        # bind this to the node
        bind(self, self.node)

#
#   NetworkLayerStateMachine
#

@bacpypes_debugging
class NetworkLayerStateMachine(ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: NetworkLayerStateMachine._debug("__init__ %r %r", address, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = address
        self.address = Address(address)

        # create a network layer encoder/decoder
        self.codec = NPDUCodec()
        if _debug: SnifferStateMachine._debug("    - codec: %r", self.codec)

        # create a node, added to the network
        self.node = Node(self.address, vlan)
        if _debug: SnifferStateMachine._debug("    - node: %r", self.node)

        # bind this to the node
        bind(self, self.codec, self.node)

#
#   RouterNode
#

@bacpypes_debugging
class RouterNode:

    def __init__(self):
        if _debug: RouterNode._debug("__init__")

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

    def add_network(self, address, vlan, net):
        if _debug: RouterNode._debug("add_network %r %r %r", address, vlan, net)

        # convert the address to an Address
        address = Address(address)

        # create a node, added to the network
        node = Node(address, vlan)
        if _debug: RouterNode._debug("    - node: %r", node)

        # bind the BIP stack to the local network
        self.nsap.bind(node, net)

#
#   TestDeviceObject
#

@register_object_type(vendor_id=999)
class TestDeviceObject(LocalDeviceObject):

    pass

#
#   ApplicationLayerStateMachine
#

@bacpypes_debugging
class ApplicationLayerStateMachine(ApplicationServiceElement, ClientStateMachine):

    def __init__(self, address, vlan):
        if _debug: ApplicationLayerStateMachine._debug("__init__ %r %r", address, vlan)

        # build a name, save the address
        self.name = "app @ %s" % (address,)
        self.address = Address(address)

        # build a local device object
        local_device = TestDeviceObject(
            objectName=self.name,
            objectIdentifier=('device', int(address)),
            vendorIdentifier=999,
            )

        # build an address and save it
        self.address = Address(address)
        if _debug: ApplicationLayerStateMachine._debug("    - address: %r", self.address)

        # continue with initialization
        ApplicationServiceElement.__init__(self)
        ClientStateMachine.__init__(self, name=local_device.objectName)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(local_device)

        # the segmentation state machines need access to some device
        # information cache, usually shared with the application
        self.smap.deviceInfoCache = DeviceInfoCache()

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a node, added to the network
        self.node = Node(self.address, vlan)
        if _debug: ApplicationLayerStateMachine._debug("    - node: %r", self.node)

        # bind the stack to the local network
        self.nsap.bind(self.node)

    def indication(self, apdu):
        if _debug: ApplicationLayerStateMachine._debug("indication %r", apdu)
        self.receive(apdu)

    def confirmation(self, apdu):
        if _debug: ApplicationLayerStateMachine._debug("confirmation %r %r", apdu)
        self.receive(apdu)

#
#   ApplicationNode
#

class ApplicationNode(Application, WhoIsIAmServices, ReadWritePropertyServices):

    def __init__(self, address, vlan):
        if _debug: ApplicationNode._debug("__init__ %r %r", address, vlan)

        # build a name, save the address
        self.name = "app @ %s" % (address,)
        self.address = Address(address)

        # build a local device object
        local_device = TestDeviceObject(
            objectName=self.name,
            objectIdentifier=('device', int(address)),
            vendorIdentifier=999,
            )

        # build an address and save it
        self.address = Address(address)
        if _debug: ApplicationNode._debug("    - address: %r", self.address)

        # continue with initialization
        Application.__init__(self, local_device, self.address)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(local_device)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a node, added to the network
        self.node = Node(self.address, vlan)
        if _debug: ApplicationNode._debug("    - node: %r", self.node)

        # bind the stack to the local network
        self.nsap.bind(self.node)

