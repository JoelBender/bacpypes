#!/usr/bin/env python

"""
This sample application presents itself as a router sitting on an IP network
to a VLAN.  The VLAN has one or more devices on it with an analog
value object that returns a random value for the present value.

Note that the device instance number of the virtual device will be 100 times
the network number plus its address (net2 * 100 + n).
"""

import random
import argparse

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.core import run, deferred
from bacpypes.comm import bind

from bacpypes.pdu import Address, LocalBroadcast
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPSimple, AnnexJCodec, UDPMultiplexer

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.object import CurrentPropertyList
from bacpypes.service.device import (
    WhoIsIAmServices,
    )
from bacpypes.service.object import (
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
    )

from bacpypes.primitivedata import Real
from bacpypes.object import register_object_type, AnalogValueObject, Property

from bacpypes.vlan import Network, Node
from bacpypes.errors import ExecutionError

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None

#
#   RandomValueProperty
#

@bacpypes_debugging
class RandomValueProperty(Property):

    def __init__(self, identifier):
        if _debug: RandomValueProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, Real, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: RandomValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # return a random value
        value = random.random() * 100.0
        if _debug: RandomValueProperty._debug("    - value: %r", value)

        # save the value that was generated
        super(RandomValueProperty, self).WriteProperty(obj, value, direct=True)

        # now return it to the client
        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: RandomValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)
        if not direct:
            raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # continue along
        super(RandomValueProperty, self).WriteProperty(obj, value, direct=True)

#
#   Random Value Object Type
#

@bacpypes_debugging
class RandomAnalogValueObject(AnalogValueObject):

    properties = [
        RandomValueProperty('presentValue'),
        ]

    def __init__(self, **kwargs):
        if _debug: RandomAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

        # if a value hasn't already been provided, initialize with a random one
        if 'presentValue' not in kwargs:
            self.presentValue = random.random() * 100.0

#
#   VLANApplication
#

@bacpypes_debugging
class VLANApplication(
    Application,
    WhoIsIAmServices,
    ReadWritePropertyServices,
    ):

    def __init__(self, vlan_device, vlan_address, aseID=None):
        if _debug: VLANApplication._debug("__init__ %r %r aseID=%r", vlan_device, vlan_address, aseID)
        global args

        # normal initialization
        Application.__init__(self, vlan_device, aseID=aseID)

        # optional read property multiple
        if args.rpm:
            self.add_capability(ReadWritePropertyMultipleServices)

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

        # bind the stack to the node, no network number, no addresss
        self.nsap.bind(self.vlan_node)

    def request(self, apdu):
        if _debug: VLANApplication._debug("[%s]request %r", self.vlan_node.address, apdu)
        Application.request(self, apdu)

    def indication(self, apdu):
        if _debug: VLANApplication._debug("[%s]indication %r", self.vlan_node.address, apdu)
        Application.indication(self, apdu)

    def response(self, apdu):
        if _debug: VLANApplication._debug("[%s]response %r", self.vlan_node.address, apdu)
        Application.response(self, apdu)

    def confirmation(self, apdu):
        if _debug: VLANApplication._debug("[%s]confirmation %r", self.vlan_node.address, apdu)
        Application.confirmation(self, apdu)

#
#   VLANRouter
#

@bacpypes_debugging
class VLANRouter:

    def __init__(self, local_address, local_network):
        if _debug: VLANRouter._debug("__init__ %r %r", local_address, local_network)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # create a BIPSimple, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPSimple(local_address)
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(local_address)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the BIP stack to the local network
        self.nsap.bind(self.bip, local_network, local_address)

#
#   __main__
#

def main():
    global args

    # parse the command line arguments
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    # add an argument for interval
    parser.add_argument('addr1', type=str,
        help='address of first network',
        )

    # add an argument for interval
    parser.add_argument('net1', type=int,
        help='network number of first network',
        )

    # add an argument for interval
    parser.add_argument('net2', type=int,
        help='network number of second network',
        )

    # add an argument for how many virtual devices
    parser.add_argument('--count', type=int,
        help='number of virtual devices',
        default=1,
        )

    # add an argument for how many virtual devices
    parser.add_argument('--rpm',
        help='enable read property multiple',
        action="store_true",
        )

    # add an argument for including the property list
    parser.add_argument('--plist',
        help='enable property list property',
        action="store_true",
        )

    # now parse the arguments
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    local_address = Address(args.addr1)
    local_network = args.net1
    vlan_network = args.net2

    # create the VLAN router, bind it to the local network
    router = VLANRouter(local_address, local_network)

    # create a VLAN
    vlan = Network(broadcast_address=LocalBroadcast())

    # create a node for the router, address 1 on the VLAN
    router_addr = Address(1)
    router_node = Node(router_addr)
    vlan.add_node(router_node)

    # bind the router stack to the vlan network through this node
    router.nsap.bind(router_node, vlan_network, router_addr)

    # send network topology
    deferred(router.nse.i_am_router_to_network)

    # add the dynamic property list
    if args.plist:
        RandomAnalogValueObject.properties.append(CurrentPropertyList())

    # register it now that all its properties are defined
    register_object_type(RandomAnalogValueObject, vendor_id=999)

    # make some devices
    for device_number in range(2, 2 + args.count):
        # device identifier is assigned from the address
        device_instance = vlan_network * 100 + device_number
        _log.debug("    - device_instance: %r", device_instance)

        # make a vlan device object
        vlan_device = \
            LocalDeviceObject(
                objectName="VLAN Node %d" % (device_instance,),
                objectIdentifier=('device', device_instance),
                maxApduLengthAccepted=1024,
                segmentationSupported='noSegmentation',
                vendorIdentifier=15,
                )
        _log.debug("    - vlan_device: %r", vlan_device)

        vlan_address = Address(device_number)
        _log.debug("    - vlan_address: %r", vlan_address)

        # make the application, add it to the network
        vlan_app = VLANApplication(vlan_device, vlan_address)
        vlan.add_node(vlan_app.vlan_node)
        _log.debug("    - vlan_app: %r", vlan_app)

        # make a random value object
        ravo = RandomAnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName='Random-1-%d' % (device_instance,),
            )
        _log.debug("    - ravo: %r", ravo)

        # add it to the device
        vlan_app.add_object(ravo)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
