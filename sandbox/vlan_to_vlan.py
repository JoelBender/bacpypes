#!/usr/bin/env python

"""
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run, deferred
from bacpypes.comm import bind

from bacpypes.pdu import Address
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPBBMD, AnnexJCodec, UDPMultiplexer

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.service.device import LocalDeviceObject, WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices

from bacpypes.apdu import ReadPropertyRequest

from bacpypes.vlan import Network, Node
from bacpypes.errors import ExecutionError

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# more than one test
which_test = 4

#
#   VLANApplication
#

@bacpypes_debugging
class VLANApplication(Application, WhoIsIAmServices, ReadWritePropertyServices):

    def __init__(self, vlan_device, vlan_address, aseID=None):
        if _debug: VLANApplication._debug("__init__ %r %r aseID=%r", vlan_device, vlan_address, aseID)
        Application.__init__(self, vlan_device, vlan_address, aseID)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(vlan_device)

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

        # create a vlan node at the assigned address
        self.vlan_node = Node(vlan_address)
        if _debug: VLANApplication._debug("    - vlan_node: %r", self.vlan_node)

        # bind the stack to the node, no network number
        self.nsap.bind(self.vlan_node)
        if _debug: VLANApplication._debug("    - node bound")

    def request(self, apdu):
        if _debug: VLANApplication._debug("[%s]request %r", self.localDevice.objectName, apdu)
        Application.request(self, apdu)

    def indication(self, apdu):
        if _debug: VLANApplication._debug("[%s]indication %r", self.localDevice.objectName, apdu)
        Application.indication(self, apdu)

    def response(self, apdu):
        if _debug: VLANApplication._debug("[%s]response %r", self.localDevice.objectName, apdu)
        Application.response(self, apdu)

    def confirmation(self, apdu):
        if _debug: VLANApplication._debug("[%s]confirmation %r", self.localDevice.objectName, apdu)

#
#   VLANRouter
#

@bacpypes_debugging
class VLANRouter:

    def __init__(self):
        if _debug: VLANRouter._debug("__init__")

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

#
#   __main__
#

def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)

    # now parse the arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    #
    #   Router1
    #

    # create the router
    router1 = VLANRouter()
    if _debug: _log.debug("    - router1: %r", router1)

    #
    #   VLAN-1
    #

    # create VLAN-1
    vlan1 = Network()
    if _debug: _log.debug("    - vlan1: %r", vlan1)

    # create a node for the router, address 1 on the VLAN
    vlan1_router1_node = Node(Address(1))
    vlan1.add_node(vlan1_router1_node)

    # bind the router stack to the vlan network through this node
    router1.nsap.bind(vlan1_router1_node, 1)
    if _debug: _log.debug("    - router1 bound to VLAN-1")

    # make a vlan device object
    vlan1_device = \
        LocalDeviceObject(
            objectName="VLAN Node 102",
            objectIdentifier=('device', 102),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=15,
            )
    _log.debug("    - vlan1_device: %r", vlan1_device)

    # make the application, add it to the network
    vlan1_app = VLANApplication(vlan1_device, Address(2))
    vlan1.add_node(vlan1_app.vlan_node)
    _log.debug("    - vlan1_app: %r", vlan1_app)

    #
    #   VLAN-2
    #

    # create VLAN-2
    vlan2 = Network()
    if _debug: _log.debug("    - vlan2: %r", vlan2)

    # create a node for the router, address 1 on the VLAN
    vlan2_router1_node = Node(Address(1))
    vlan2.add_node(vlan2_router1_node)

    # bind the router stack to the vlan network through this node
    router1.nsap.bind(vlan2_router1_node, 2)
    if _debug: _log.debug("    - router1 bound to VLAN-2")

    # make a vlan device object
    vlan2_device = \
        LocalDeviceObject(
            objectName="VLAN Node 202",
            objectIdentifier=('device', 202),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=15,
            )
    _log.debug("    - vlan2_device: %r", vlan2_device)

    # make the application, add it to the network
    vlan2_app = VLANApplication(vlan2_device, Address(2))
    vlan2.add_node(vlan2_app.vlan_node)
    _log.debug("    - vlan2_app: %r", vlan2_app)

    #
    #   VLAN-3
    #

    # create VLAN-3
    vlan3 = Network()
    if _debug: _log.debug("    - vlan3: %r", vlan3)

    # create a node for the router, address 1 on the VLAN
    vlan3_router1_node = Node(Address(1))
    vlan3.add_node(vlan3_router1_node)

    # bind the router stack to the vlan network through this node
    router1.nsap.bind(vlan3_router1_node, 3)
    if _debug: _log.debug("    - router1 bound to VLAN-3")

    # make a vlan device object
    vlan3_device = \
        LocalDeviceObject(
            objectName="VLAN Node 302",
            objectIdentifier=('device', 302),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=15,
            )
    _log.debug("    - vlan3_device: %r", vlan3_device)

    # make the application, add it to the network
    vlan3_app = VLANApplication(vlan3_device, Address(2))
    vlan3.add_node(vlan3_app.vlan_node)
    _log.debug("    - vlan3_app: %r", vlan3_app)


    #
    #   Router2
    #

    # create the router
    router2 = VLANRouter()
    if _debug: _log.debug("    - router2: %r", router2)

    # create a node for the router, address 255 on the VLAN-3
    vlan3_router2_node = Node(Address(255))
    vlan3.add_node(vlan3_router2_node)

    # bind the router stack to the vlan network through this node
    router2.nsap.bind(vlan3_router2_node, 3)
    if _debug: _log.debug("    - router2 bound to VLAN-3")

    #
    #   VLAN-4
    #

    # create VLAN-4
    vlan4 = Network()
    if _debug: _log.debug("    - vlan4: %r", vlan4)

    # create a node for the router, address 1 on the VLAN
    vlan4_router2_node = Node(Address(1))
    vlan4.add_node(vlan4_router2_node)

    # bind the router stack to the vlan network through this node
    router2.nsap.bind(vlan4_router2_node, 4)
    if _debug: _log.debug("    - router2 bound to VLAN-4")

    # make a vlan device object
    vlan4_device = \
        LocalDeviceObject(
            objectName="VLAN Node 402",
            objectIdentifier=('device', 402),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=15,
            )
    _log.debug("    - vlan4_device: %r", vlan4_device)

    # make the application, add it to the network
    vlan4_app = VLANApplication(vlan4_device, Address(2))
    vlan4.add_node(vlan4_app.vlan_node)
    _log.debug("    - vlan4_app: %r", vlan4_app)


    #
    #   Test 1
    #

    if which_test == 1:
        # ask the first device to Who-Is everybody
        deferred(vlan1_app.who_is)


    #
    #   Test 2
    #

    if which_test == 2:
        # make a read request
        read_property_request = ReadPropertyRequest(
            destination=Address("2:2"),
            objectIdentifier=('device', 202),
            propertyIdentifier='objectName',
            )

        # ask the first device to send it
        deferred(vlan1_app.request, read_property_request)


    #
    #   Test 3
    #

    if which_test == 3:
        # make a read request
        read_property_request = ReadPropertyRequest(
            destination=Address("3:2"),
            objectIdentifier=('device', 302),
            propertyIdentifier='objectName',
            )

        # ask the first device to send it
        deferred(vlan1_app.request, read_property_request)


    #
    #   Test 4
    #

    if which_test == 4:
        # make a read request
        read_property_request = ReadPropertyRequest(
            destination=Address("4:2"),
            objectIdentifier=('device', 402),
            propertyIdentifier='objectName',
            )

        # ask the first device to send it
        deferred(vlan1_app.request, read_property_request)


    #
    #   Let the test run
    #

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
