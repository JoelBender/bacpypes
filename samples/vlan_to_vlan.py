#!/usr/bin/env python

"""
VLAN to VLAN

This application started out being a way to test various combinations of
traffic before the tests were written.  All of the traffic patterns in this
application are in the test suite but this is simpler.

It doesn't generate any output, turn on debugging to see what each node is
sending (the request() calls) and receiving (the indication() calls).

    $ python vlan_to_vlan.py 1 --debug __main__.VLANApplication

Note how the source and destination addresses change as packets go through
routers.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run, deferred
from bacpypes.comm import bind

from bacpypes.pdu import Address, LocalBroadcast
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices
from bacpypes.local.device import LocalDeviceObject

from bacpypes.apdu import ReadPropertyRequest

from bacpypes.vlan import Network, Node

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   VLANApplication
#


@bacpypes_debugging
class VLANApplication(Application, WhoIsIAmServices, ReadWritePropertyServices):
    def __init__(self, objectName, deviceInstance, address, aseID=None):
        if _debug:
            VLANApplication._debug(
                "__init__ %r %r %r aseID=%r", objectName, deviceInstance, address, aseID
            )

        # make an address
        vlan_address = Address(address)
        _log.debug("    - vlan_address: %r", vlan_address)

        # make a device object
        vlan_device = LocalDeviceObject(
            objectName=objectName,
            objectIdentifier=("device", deviceInstance),
            maxApduLengthAccepted=1024,
            segmentationSupported="noSegmentation",
            vendorIdentifier=15,
        )
        _log.debug("    - vlan_device: %r", vlan_device)

        # continue with the initialization
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
        if _debug:
            VLANApplication._debug("    - vlan_node: %r", self.vlan_node)

        # bind the stack to the node, no network number
        self.nsap.bind(self.vlan_node)
        if _debug:
            VLANApplication._debug("    - node bound")

    def request(self, apdu):
        if _debug:
            VLANApplication._debug("[%s]request %r", self.localDevice.objectName, apdu)
        Application.request(self, apdu)

    def indication(self, apdu):
        if _debug:
            VLANApplication._debug(
                "[%s]indication %r", self.localDevice.objectName, apdu
            )
        Application.indication(self, apdu)

    def response(self, apdu):
        if _debug:
            VLANApplication._debug("[%s]response %r", self.localDevice.objectName, apdu)
        Application.response(self, apdu)

    def confirmation(self, apdu):
        if _debug:
            VLANApplication._debug(
                "[%s]confirmation %r", self.localDevice.objectName, apdu
            )


#
#   VLANRouter
#


@bacpypes_debugging
class VLANRouter:
    def __init__(self):
        if _debug:
            VLANRouter._debug("__init__")

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

    def bind(self, vlan, address, net):
        if _debug:
            VLANRouter._debug("bind %r %r %r", vlan, address, net)

        # create a VLAN node for the router with the given address
        vlan_node = Node(Address(address))

        # add it to the VLAN
        vlan.add_node(vlan_node)

        # bind the router stack to the vlan network through this node
        self.nsap.bind(vlan_node, net)
        if _debug:
            _log.debug("    - bound to vlan")


def main():
    # parse the command line arguments
    parser = ArgumentParser(description=__doc__)

    # add an argument for which test to run
    parser.add_argument("test_id", type=int, help="test number")

    # now parse the arguments
    args = parser.parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # VLAN needs to know what a broadcast address looks like
    vlan_broadcast_address = LocalBroadcast()

    #
    #   Router1
    #

    # create the router
    router1 = VLANRouter()
    if _debug:
        _log.debug("    - router1: %r", router1)

    #
    #   VLAN-1
    #

    # create VLAN-1
    vlan1 = Network(name="1", broadcast_address=vlan_broadcast_address)
    if _debug:
        _log.debug("    - vlan1: %r", vlan1)

    # bind the router to the vlan
    router1.bind(vlan1, 1, 1)
    if _debug:
        _log.debug("    - router1 bound to VLAN-1")

    # make the application, add it to the network
    vlan1_app = VLANApplication(
        objectName="VLAN Node 102", deviceInstance=102, address=2
    )
    vlan1.add_node(vlan1_app.vlan_node)
    _log.debug("    - vlan1_app: %r", vlan1_app)

    #
    #   VLAN-2
    #

    # create VLAN-2
    vlan2 = Network(name="2", broadcast_address=vlan_broadcast_address)
    if _debug:
        _log.debug("    - vlan2: %r", vlan2)

    # bind the router stack to the vlan network through this node
    router1.bind(vlan2, 1, 2)
    if _debug:
        _log.debug("    - router1 bound to VLAN-2")

    # make the application, add it to the network
    vlan2_app = VLANApplication(
        objectName="VLAN Node 202", deviceInstance=202, address=2
    )
    vlan2.add_node(vlan2_app.vlan_node)
    _log.debug("    - vlan2_app: %r", vlan2_app)

    #
    #   VLAN-3
    #

    # create VLAN-3
    vlan3 = Network(name="3", broadcast_address=vlan_broadcast_address)
    if _debug:
        _log.debug("    - vlan3: %r", vlan3)

    # bind the router stack to the vlan network through this node
    router1.bind(vlan3, 1, 3)
    if _debug:
        _log.debug("    - router1 bound to VLAN-3")

    # make a vlan device object
    vlan3_device = LocalDeviceObject(
        objectName="VLAN Node 302",
        objectIdentifier=("device", 302),
        maxApduLengthAccepted=1024,
        segmentationSupported="noSegmentation",
        vendorIdentifier=15,
    )
    _log.debug("    - vlan3_device: %r", vlan3_device)

    # make the application, add it to the network
    vlan3_app = VLANApplication(
        objectName="VLAN Node 302", deviceInstance=302, address=2
    )
    vlan3.add_node(vlan3_app.vlan_node)
    _log.debug("    - vlan3_app: %r", vlan3_app)

    #
    #   Router2
    #

    # create the router
    router2 = VLANRouter()
    if _debug:
        _log.debug("    - router2: %r", router2)

    # bind the router stack to the vlan network through this node
    router2.bind(vlan3, 255, 3)
    if _debug:
        _log.debug("    - router2 bound to VLAN-3")

    #
    #   VLAN-4
    #

    # create VLAN-4
    vlan4 = Network(name="4", broadcast_address=vlan_broadcast_address)
    if _debug:
        _log.debug("    - vlan4: %r", vlan4)

    # bind the router stack to the vlan network through this node
    router2.bind(vlan4, 1, 4)
    if _debug:
        _log.debug("    - router2 bound to VLAN-4")

    # make the application, add it to the network
    vlan4_app = VLANApplication(
        objectName="VLAN Node 402", deviceInstance=402, address=2
    )
    vlan4.add_node(vlan4_app.vlan_node)
    _log.debug("    - vlan4_app: %r", vlan4_app)

    #
    #   Test 1
    #

    if args.test_id == 1:
        # ask the first device to Who-Is everybody
        deferred(vlan1_app.who_is)

    #
    #   Test 2
    #

    if args.test_id == 2:
        # make a read request
        read_property_request = ReadPropertyRequest(
            destination=Address("2:2"),
            objectIdentifier=("device", 202),
            propertyIdentifier="objectName",
        )

        # ask the first device to send it
        deferred(vlan1_app.request, read_property_request)

    #
    #   Test 3
    #

    if args.test_id == 3:
        # make a read request
        read_property_request = ReadPropertyRequest(
            destination=Address("3:2"),
            objectIdentifier=("device", 302),
            propertyIdentifier="objectName",
        )

        # ask the first device to send it
        deferred(vlan1_app.request, read_property_request)

    #
    #   Test 4
    #

    if args.test_id == 4:
        # make a read request
        read_property_request = ReadPropertyRequest(
            destination=Address("4:2"),
            objectIdentifier=("device", 402),
            propertyIdentifier="objectName",
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
