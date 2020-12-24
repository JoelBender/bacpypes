#!/usr/bin/env python

"""
This sample application presents itself as a router sitting on an IP network
to a VLAN.  The VLAN has one or more devices on it with an analog
value object that returns a random value for the present value.

Note that the device instance number of the virtual device will be 100 times
the network number plus its address (net2 * 100 + n).

This is a clone of the IP2VLANRouter application that includes a console
interface with the whois, iam, read and write commands.
"""

import sys
import random
import argparse

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.comm import bind
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, LocalBroadcast, GlobalBroadcast
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPSimple, AnnexJCodec, UDPMultiplexer

from bacpypes.app import Application, ApplicationIOController
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.object import CurrentPropertyList
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import (
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
)

from bacpypes.vlan import Network, Node
from bacpypes.errors import ExecutionError

from bacpypes.object import (
    get_datatype,
    register_object_type,
    AnalogValueObject,
    Property,
)

from bacpypes.apdu import (
    SimpleAckPDU,
    ReadPropertyRequest,
    ReadPropertyACK,
    WritePropertyRequest,
)
from bacpypes.primitivedata import (
    Null,
    Atomic,
    Boolean,
    Unsigned,
    Integer,
    Real,
    Double,
    OctetString,
    CharacterString,
    BitString,
    Date,
    Time,
    ObjectIdentifier,
)
from bacpypes.constructeddata import Array, Any, AnyAtomic

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None
this_application = None

#
#   RandomValueProperty
#


@bacpypes_debugging
class RandomValueProperty(Property):
    def __init__(self, identifier):
        if _debug:
            RandomValueProperty._debug("__init__ %r", identifier)
        Property.__init__(
            self, identifier, Real, default=None, optional=True, mutable=False
        )

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug:
            RandomValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)

        # access an array
        if arrayIndex is not None:
            raise ExecutionError(
                errorClass="property", errorCode="propertyIsNotAnArray"
            )

        # return a random value
        value = random.random() * 100.0
        if _debug:
            RandomValueProperty._debug("    - value: %r", value)

        # save the value that was generated
        super(RandomValueProperty, self).WriteProperty(obj, value, direct=True)

        # now return it to the client
        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug:
            RandomValueProperty._debug(
                "WriteProperty %r %r arrayIndex=%r priority=%r direct=%r",
                obj,
                value,
                arrayIndex,
                priority,
                direct,
            )
        if not direct:
            raise ExecutionError(errorClass="property", errorCode="writeAccessDenied")
        if arrayIndex is not None:
            raise ExecutionError(
                errorClass="property", errorCode="propertyIsNotAnArray"
            )

        # continue along
        super(RandomValueProperty, self).WriteProperty(obj, value, direct=True)


#
#   Random Value Object Type
#


@bacpypes_debugging
class RandomAnalogValueObject(AnalogValueObject):

    properties = [
        RandomValueProperty("presentValue"),
    ]

    def __init__(self, **kwargs):
        if _debug:
            RandomAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)

        # if a value hasn't already been provided, initialize with a random one
        if "presentValue" not in kwargs:
            self.presentValue = random.random() * 100.0


#
#   VLANApplication
#


@bacpypes_debugging
class VLANApplication(
    Application, WhoIsIAmServices, ReadWritePropertyServices,
):
    def __init__(self, vlan_device, vlan_address, aseID=None):
        if _debug:
            VLANApplication._debug(
                "__init__ %r %r aseID=%r", vlan_device, vlan_address, aseID
            )
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
        if _debug:
            VLANApplication._debug("[%s]request %r", self.vlan_node.address, apdu)
        Application.request(self, apdu)

    def indication(self, apdu):
        if _debug:
            VLANApplication._debug("[%s]indication %r", self.vlan_node.address, apdu)
        Application.indication(self, apdu)

    def response(self, apdu):
        if _debug:
            VLANApplication._debug("[%s]response %r", self.vlan_node.address, apdu)
        Application.response(self, apdu)

    def confirmation(self, apdu):
        if _debug:
            VLANApplication._debug("[%s]confirmation %r", self.vlan_node.address, apdu)
        Application.confirmation(self, apdu)


#
#   VLANRouter
#


@bacpypes_debugging
class VLANRouter:
    def __init__(self, local_address, local_network):
        if _debug:
            VLANRouter._debug("__init__ %r %r", local_address, local_network)

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
#   VLANConsoleApplication
#


@bacpypes_debugging
class VLANConsoleApplication(
    ApplicationIOController, WhoIsIAmServices, ReadWritePropertyServices,
):
    def __init__(self, vlan_device, vlan_address, aseID=None):
        if _debug:
            VLANConsoleApplication._debug(
                "__init__ %r %r aseID=%r", vlan_device, vlan_address, aseID
            )
        global args

        # normal initialization
        ApplicationIOController.__init__(self, vlan_device, aseID=aseID)

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


#
#   VLANConsoleCmd
#


@bacpypes_debugging
class VLANConsoleCmd(ConsoleCmd):
    def do_whois(self, args):
        """whois [ <addr> ] [ <lolimit> <hilimit> ]"""
        args = args.split()
        if _debug:
            VLANConsoleCmd._debug("do_whois %r", args)

        try:
            # gather the parameters
            if (len(args) == 1) or (len(args) == 3):
                addr = Address(args[0])
                del args[0]
            else:
                addr = GlobalBroadcast()

            if len(args) == 2:
                lolimit = int(args[0])
                hilimit = int(args[1])
            else:
                lolimit = hilimit = None

            # code lives in the device service
            this_application.who_is(lolimit, hilimit, addr)

        except Exception as error:
            VLANConsoleCmd._exception("exception: %r", error)

    def do_iam(self, args):
        """iam"""
        args = args.split()
        if _debug:
            VLANConsoleCmd._debug("do_iam %r", args)

        # code lives in the device service
        this_application.i_am()

    def do_read(self, args):
        """read <addr> <objid> <prop> [ <indx> ]"""
        args = args.split()
        if _debug:
            VLANConsoleCmd._debug("do_read %r", args)

        try:
            addr, obj_id, prop_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value
            if prop_id.isdigit():
                prop_id = int(prop_id)

            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id, propertyIdentifier=prop_id,
            )
            request.pduDestination = Address(addr)

            if len(args) == 4:
                request.propertyArrayIndex = int(args[3])
            if _debug:
                VLANConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                VLANConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, ReadPropertyACK):
                    if _debug:
                        VLANConsoleCmd._debug("    - not an ack")
                    return

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    VLANConsoleCmd._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (
                    apdu.propertyArrayIndex is not None
                ):
                    if apdu.propertyArrayIndex == 0:
                        value = apdu.propertyValue.cast_out(Unsigned)
                    else:
                        value = apdu.propertyValue.cast_out(datatype.subtype)
                else:
                    value = apdu.propertyValue.cast_out(datatype)
                if _debug:
                    VLANConsoleCmd._debug("    - value: %r", value)

                sys.stdout.write(str(value) + "\n")
                if hasattr(value, "debug_contents"):
                    value.debug_contents(file=sys.stdout)
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + "\n")

        except Exception as error:
            VLANConsoleCmd._exception("exception: %r", error)

    def do_write(self, args):
        """write <addr> <objid> <prop> <value> [ <indx> ] [ <priority> ]"""
        args = args.split()
        VLANConsoleCmd._debug("do_write %r", args)

        try:
            addr, obj_id, prop_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value
            value = args[3]

            indx = None
            if len(args) >= 5:
                if args[4] != "-":
                    indx = int(args[4])
            if _debug:
                VLANConsoleCmd._debug("    - indx: %r", indx)

            priority = None
            if len(args) >= 6:
                priority = int(args[5])
            if _debug:
                VLANConsoleCmd._debug("    - priority: %r", priority)

            # get the datatype
            datatype = get_datatype(obj_id[0], prop_id)
            if _debug:
                VLANConsoleCmd._debug("    - datatype: %r", datatype)

            # change atomic values into something encodeable, null is a special case
            if value == "null":
                value = Null()
            elif issubclass(datatype, AnyAtomic):
                dtype, dvalue = value.split(":", 1)
                if _debug:
                    VLANConsoleCmd._debug("    - dtype, dvalue: %r, %r", dtype, dvalue)

                datatype = {
                    "b": Boolean,
                    "u": lambda x: Unsigned(int(x)),
                    "i": lambda x: Integer(int(x)),
                    "r": lambda x: Real(float(x)),
                    "d": lambda x: Double(float(x)),
                    "o": OctetString,
                    "c": CharacterString,
                    "bs": BitString,
                    "date": Date,
                    "time": Time,
                    "id": ObjectIdentifier,
                }[dtype]
                if _debug:
                    VLANConsoleCmd._debug("    - datatype: %r", datatype)

                value = datatype(dvalue)
                if _debug:
                    VLANConsoleCmd._debug("    - value: %r", value)

            elif issubclass(datatype, Atomic):
                if datatype is Integer:
                    value = int(value)
                elif datatype is Real:
                    value = float(value)
                elif datatype is Unsigned:
                    value = int(value)
                value = datatype(value)
            elif issubclass(datatype, Array) and (indx is not None):
                if indx == 0:
                    value = Integer(value)
                elif issubclass(datatype.subtype, Atomic):
                    value = datatype.subtype(value)
                elif not isinstance(value, datatype.subtype):
                    raise TypeError(
                        "invalid result datatype, expecting %s"
                        % (datatype.subtype.__name__,)
                    )
            elif not isinstance(value, datatype):
                raise TypeError(
                    "invalid result datatype, expecting %s" % (datatype.__name__,)
                )
            if _debug:
                VLANConsoleCmd._debug(
                    "    - encodeable value: %r %s", value, type(value)
                )

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=obj_id, propertyIdentifier=prop_id
            )
            request.pduDestination = Address(addr)

            # save the value
            request.propertyValue = Any()
            try:
                request.propertyValue.cast_in(value)
            except Exception as error:
                VLANConsoleCmd._exception("WriteProperty cast error: %r", error)

            # optional array index
            if indx is not None:
                request.propertyArrayIndex = indx

            # optional priority
            if priority is not None:
                request.priority = priority

            if _debug:
                VLANConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                VLANConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                # should be an ack
                if not isinstance(iocb.ioResponse, SimpleAckPDU):
                    if _debug:
                        VLANConsoleCmd._debug("    - not an ack")
                    return

                sys.stdout.write("ack\n")

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + "\n")

        except Exception as error:
            VLANConsoleCmd._exception("exception: %r", error)

    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug:
            VLANConsoleCmd._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        this_application.nsap.update_router_references(
            None, router_address, network_list
        )


#
#   __main__
#


def main():
    global args, this_application

    # parse the command line arguments
    parser = ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # add an argument for interval
    parser.add_argument(
        "addr1", type=str, help="address of first network",
    )

    # add an argument for interval
    parser.add_argument(
        "net1", type=int, help="network number of first network",
    )

    # add an argument for interval
    parser.add_argument(
        "net2", type=int, help="network number of second network",
    )

    # add an argument for how many virtual devices
    parser.add_argument(
        "--count", type=int, help="number of virtual devices", default=1,
    )

    # add an argument for how many virtual devices
    parser.add_argument(
        "--rpm", help="enable read property multiple", action="store_true",
    )

    # add an argument for including the property list
    parser.add_argument(
        "--plist", help="enable property list property", action="store_true",
    )

    # now parse the arguments
    args = parser.parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

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

    # console is the first device
    device_number = 2
    device_instance = vlan_network * 100 + device_number
    _log.debug("    - console device_instance: %r", device_instance)

    # make a vlan device object
    vlan_device = LocalDeviceObject(
        objectName="VLAN Console Node %d" % (device_instance,),
        objectIdentifier=("device", device_instance),
        maxApduLengthAccepted=1024,
        segmentationSupported="noSegmentation",
        vendorIdentifier=15,
    )
    _log.debug("    - vlan_device: %r", vlan_device)

    vlan_address = Address(device_number)
    _log.debug("    - vlan_address: %r", vlan_address)

    # make the console application, add it to the network
    this_application = VLANConsoleApplication(vlan_device, vlan_address)
    vlan.add_node(this_application.vlan_node)
    _log.debug("    - this_application: %r", this_application)

    # make a console
    this_console = VLANConsoleCmd()
    if _debug:
        _log.debug("    - this_console: %r", this_console)

    # make a random value object
    ravo = RandomAnalogValueObject(
        objectIdentifier=("analogValue", 1),
        objectName="Random-1-%d" % (device_instance,),
    )
    _log.debug("    - ravo: %r", ravo)

    # add it to the device
    this_application.add_object(ravo)

    # make some more devices
    for device_number in range(3, 3 + args.count - 1):
        # device identifier is assigned from the address
        device_instance = vlan_network * 100 + device_number
        _log.debug("    - device_instance: %r", device_instance)

        # make a vlan device object
        vlan_device = LocalDeviceObject(
            objectName="VLAN Node %d" % (device_instance,),
            objectIdentifier=("device", device_instance),
            maxApduLengthAccepted=1024,
            segmentationSupported="noSegmentation",
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
            objectIdentifier=("analogValue", 1),
            objectName="Random-1-%d" % (device_instance,),
        )
        _log.debug("    - ravo: %r", ravo)

        # add it to the device
        vlan_app.add_object(ravo)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
