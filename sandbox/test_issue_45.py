#!/usr/bin/python

"""
test_issue_45

This sample application builds a VLAN with two application layer nodes and
uses a console prompt to send packets.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run
from bacpypes.comm import bind

from bacpypes.pdu import Address, GlobalBroadcast

from bacpypes.vlan import Network, Node

from bacpypes.app import LocalDeviceObject, Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement

from bacpypes.apdu import WhoIsRequest, IAmRequest, ReadPropertyRequest, WritePropertyRequest

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real
from bacpypes.constructeddata import Array, Any
from bacpypes.object import get_object_class, get_datatype

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
vlan_app_1 = None
vlan_app_2 = None

#
#   VLANApplication
#

@bacpypes_debugging
class VLANApplication(Application):

    def __init__(self, vlan_device, vlan_address, aseID=None):
        if _debug: VLANApplication._debug("__init__ %r %r aseID=%r", vlan_device, vlan_address, aseID)
        Application.__init__(self, vlan_device, vlan_address, aseID)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(vlan_device)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a vlan node at the assigned address
        self.vlan_node = Node(vlan_address)

        # bind the stack to the node, no network number
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
#   TestConsoleCmd
#

class TestConsoleCmd(ConsoleCmd):

    def do_whois(self, args):
        """whois [ <addr>] [ <lolimit> <hilimit> ]"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_whois %r", args)

        try:
            # build a request
            request = WhoIsRequest()
            if (len(args) == 1) or (len(args) == 3):
                request.pduDestination = Address(args[0])
                del args[0]
            else:
                request.pduDestination = GlobalBroadcast()

            if len(args) == 2:
                request.deviceInstanceRangeLowLimit = int(args[0])
                request.deviceInstanceRangeHighLimit = int(args[1])
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            vlan_app_1.request(request)

        except Exception, e:
            TestConsoleCmd._exception("exception: %r", e)

    def do_iam(self, args):
        """iam"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_iam %r", args)

        try:
            # build a request
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = vlan_device_1.objectIdentifier
            request.maxAPDULengthAccepted = vlan_device_1.maxApduLengthAccepted
            request.segmentationSupported = vlan_device_1.segmentationSupported
            request.vendorID = vlan_device_1.vendorIdentifier
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            vlan_app_1.request(request)

        except Exception, e:
            TestConsoleCmd._exception("exception: %r", e)

    def do_read(self, args):
        """read <addr> <type> <inst> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_read %r", args)

        try:
            addr, obj_type, obj_inst, prop_id = args[:4]

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif not get_object_class(obj_type):
                raise ValueError, "unknown object type"

            obj_inst = int(obj_inst)

            datatype = get_datatype(obj_type, prop_id)
            if not datatype:
                raise ValueError, "invalid property for object type"

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            vlan_app_1.request(request)

        except Exception, e:
            TestConsoleCmd._exception("exception: %r", e)

    def do_write(self, args):
        """write <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_write %r", args)

        try:
            addr, obj_type, obj_inst, prop_id = args[:4]
            if obj_type.isdigit():
                obj_type = int(obj_type)
            obj_inst = int(obj_inst)
            value = args[4]

            indx = None
            if len(args) >= 6:
                if args[5] != "-":
                    indx = int(args[5])
            if _debug: TestConsoleCmd._debug("    - indx: %r", indx)

            priority = None
            if len(args) >= 7:
                priority = int(args[6])
            if _debug: TestConsoleCmd._debug("    - priority: %r", priority)

            # get the datatype
            datatype = get_datatype(obj_type, prop_id)
            if _debug: TestConsoleCmd._debug("    - datatype: %r", datatype)

            # change atomic values into something encodeable, null is a special case
            if (value == 'null'):
                value = Null()
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
                    raise TypeError, "invalid result datatype, expecting %s" % (datatype.subtype.__name__,)
            elif not isinstance(value, datatype):
                raise TypeError, "invalid result datatype, expecting %s" % (datatype.__name__,)
            if _debug: TestConsoleCmd._debug("    - encodeable value: %r %s", value, type(value))

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id
                )
            request.pduDestination = Address(addr)

            # save the value
            request.propertyValue = Any()
            try:
                request.propertyValue.cast_in(value)
            except Exception, e:
                TestConsoleCmd._exception("WriteProperty cast error: %r", e)

            # optional array index
            if indx is not None:
                request.propertyArrayIndex = indx

            # optional priority
            if priority is not None:
                request.priority = priority

            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # give it to the application
            vlan_app_1.request(request)

        except Exception, e:
            TestConsoleCmd._exception("exception: %r", e)

bacpypes_debugging(TestConsoleCmd)

#
#   __main__
#

try:
    # parse the command line arguments
    args = ArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # create a VLAN
    vlan = Network()

    # create the first device
    vlan_device_1 = \
        LocalDeviceObject(
            objectName="VLAN Node 1",
            objectIdentifier=('device', 1),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=15,
            )

    # create the application stack, add it to the network
    vlan_app_1 = VLANApplication(vlan_device_1, Address(1))
    vlan.add_node(vlan_app_1.vlan_node)

    # create the second device
    vlan_device_2 = \
        LocalDeviceObject(
            objectName="VLAN Node 2",
            objectIdentifier=('device', 2),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=15,
            )

    # create the application stack, add it to the network
    vlan_app_2 = VLANApplication(vlan_device_2, Address(2))
    vlan.add_node(vlan_app_2.vlan_node)

    # make a console
    this_console = TestConsoleCmd()

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")

