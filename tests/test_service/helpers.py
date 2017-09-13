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

from ..state_machine import StateMachine, ClientStateMachine


# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   _repr
#

class _repr:

    def __repr__(self):
        if not self.running:
            state_text = "idle "
        else:
            state_text = "in "
        state_text += repr(self.current_state)

        return "<%s(%s) %s at %s>" % (
            self.__class__.__name__,
            getattr(self, 'address', '?'),
            state_text,
            hex(id(self)),
        )


#
#   SnifferNode
#

@bacpypes_debugging
class SnifferNode(_repr, ClientStateMachine):

    def __init__(self, localAddress, vlan):
        if _debug: SnifferNode._debug("__init__ %r %r", localAddress, vlan)
        ClientStateMachine.__init__(self)

        # save the name and address
        self.name = "sniffer"
        self.address = localAddress

        # create a promiscuous node, added to the network
        self.node = Node(self.address, vlan, promiscuous=True)
        if _debug: SnifferNode._debug("    - node: %r", self.node)

        # bind this to the node
        bind(self, self.node)


@bacpypes_debugging
class ClientStateMachine(Client, StateMachine):

    """
    ClientStateMachine
    ~~~~~~~~~~~~~~~~~~

    An instance of this class sits at the top of a stack.  PDU's that the
    state machine sends are sent down the stack and PDU's coming up the
    stack are fed as received PDU's.
    """

    def __init__(self):
        if _debug: ClientStateMachine._debug("__init__")

        Client.__init__(self)
        StateMachine.__init__(self)

#
#   ApplicationNode
#

@bacpypes_debugging
class ApplicationNode(_repr, Application, StateMachine):

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

    def send(self, pdu):
        if _debug: ApplicationNode._debug("send %r", pdu)
        self.request(pdu)

    def confirmation(self, pdu):
        if _debug: ApplicationNode._debug("confirmation %r", pdu)
        self.receive(pdu)

