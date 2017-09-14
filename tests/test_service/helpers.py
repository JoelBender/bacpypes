#!/usr/bin/env python

"""
Service Helper Classes
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.comm import Client, Server, bind
from bacpypes.pdu import Address, LocalBroadcast, PDU
from bacpypes.vlan import Network, Node

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement

from ..state_machine import StateMachine


# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   SnifferNode
#

@bacpypes_debugging
class SnifferNode(Client, StateMachine):

    def __init__(self, localAddress, vlan):
        if _debug: SnifferNode._debug("__init__ %r %r", localAddress, vlan)
        Client.__init__(self)
        StateMachine.__init__(self)

        # save the name and address
        self.name = "sniffer"
        self.address = localAddress

        # create a promiscuous node, added to the network
        self.node = Node(self.address, vlan, promiscuous=True)
        if _debug: SnifferNode._debug("    - node: %r", self.node)

        # bind this to the node
        bind(self, self.node)

    def send(self, pdu):
        if _debug: SnifferNode._debug("send(%s) %r", self.name, pdu)
        raise RuntimeError("sniffers don't send")

    def confirmation(self, pdu):
        if _debug: SnifferNode._debug("confirmation(%s) %r", self.name, pdu)

        # pass to the state machine
        self.receive(pdu)


#
#   ApplicationNode
#

@bacpypes_debugging
class ApplicationNode(Application, StateMachine):

    def __init__(self, localDevice, localAddress, vlan):
        if _debug: ApplicationNode._debug("__init__ %r %r %r", localDevice, localAddress, vlan)
        Application.__init__(self, localDevice, localAddress)
        StateMachine.__init__(self)

        # save the name and address
        self.name = localDevice.objectName
        self.address = localAddress

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

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

        # bind the network service to the node, no network number
        self.nsap.bind(self.node)

    def send(self, apdu):
        if _debug: ApplicationNode._debug("send(%s) %r", self.name, apdu)

        # send the apdu down the stack
        self.request(apdu)

    def indication(self, apdu):
        if _debug: ApplicationNode._debug("indication(%s) %r", self.name, apdu)

        # let the state machine know the request was received
        self.receive(apdu)

        # allow the application to process it
        super(ApplicationNode, self).indication(apdu)

    def confirmation(self, apdu):
        if _debug: ApplicationNode._debug("confirmation(%s) %r", self.name, apdu)

        # forward the confirmation to the state machine
        self.receive(apdu)

