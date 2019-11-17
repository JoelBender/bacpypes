#!/usr/bin/python3

"""
Discover

This is a console application to assist with the "discovery" process of finding
BACnet routers, devices, objects, and property values.  It reads and/or writes
a tab-delimited property values text file of the values that it has received.

The console commands are:

    wirtn       - who is router to network
    irt         - initialize routing table
    winn        - what is network number
    whois       - who is
    iam         - i am
    rp          - read property
    rpm         - read property multiple

The property values text file contains these fields:

    devid       - device identifier
    objid       - object identifier
    propid      - property identifier
    version     - version number
    value       - value

When the object identifier field is "-" the properties are from I-Am messages
that are received:

    address                 - the BACpypes address of the device
    maxAPDULengthAccepted   - maximum APDU length accepted
    segmentationSupported   - segmentation supported

To facilitate finding out what has changed between two different times the
application has been run the property values text file is always sorted.
Whenever a property value is different than the previous value, the version
number is incremented.

For example, the first time the presentValue of analogValue:1 is read the
file could look like this:

    202     analogValue:1	presentValue    1   14.02

Then when the application is run again, it could look like this:

    202     analogValue:1   presentValue    2   9.52

The application accepts stdin from non-interactive sessions, for example:

    $ echo "whois" | python Discover.py stuff

or from a script file:

    $ python discover.py stuff << EOF
    > whois
    > rpm 201 device:201 all
    > rpm 201 analogValue:1 all
    > EOF

The application prints content during interactive sessions.
"""

import sys
import time
import json
from collections import OrderedDict

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.pdu import Address, LocalBroadcast, GlobalBroadcast
from bacpypes.comm import bind
from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.iocb import IOCB

# application layer
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.object import get_datatype

from bacpypes.app import ApplicationIOController
from bacpypes.appservice import (
    StateMachineAccessPoint,
    ApplicationServiceAccessPoint,
    )
from bacpypes.apdu import (
    WhoIsRequest,
    IAmRequest,
    ReadPropertyRequest,
    ReadPropertyACK,
    ReadPropertyMultipleRequest,
    PropertyReference,
    ReadAccessSpecification,
    ReadPropertyMultipleACK,
    )

# network layer
from bacpypes.netservice import (
    NetworkServiceAccessPoint,
    NetworkServiceElement,
    )
from bacpypes.npdu import (
    WhoIsRouterToNetwork,
    IAmRouterToNetwork,
    InitializeRoutingTable,
    InitializeRoutingTableAck,
    WhatIsNetworkNumber,
    NetworkNumberIs,
    )

# IPv4 virtual link layer
from bacpypes.bvllservice import BIPSimple, AnnexJCodec, UDPMultiplexer

# basic objects
from bacpypes.local.device import LocalDeviceObject

# basic services
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
args = None
this_device = None
this_application = None
snapshot = None

# print statements just for interactive
interactive = sys.stdin.isatty()

#
#   Snapshot
#

@bacpypes_debugging
class Snapshot:

    def __init__(self):
        if _debug: Snapshot._debug("__init__")

        # empty database
        self.data = {}

    def read_file(self, filename):
        if _debug: Snapshot._debug("read_file %r", filename)

        # empty database
        self.data = {}

        try:
            with open(filename) as infile:
                lines = infile.readlines()
                for line in lines:
                    devid, objid, propid, version, value = line[:-1].split('\t')

                    devid = int(devid)
                    version = int(version)

                    key = (devid, objid, propid)
                    self.data[key] = (version, value)
        except IOError:
            if _debug: Snapshot._debug("    - file not found")
            pass

    def write_file(self, filename):
        if _debug: Snapshot._debug("write_file %r", filename)

        data = list(k + v for k, v in self.data.items())
        data.sort()

        with open(filename, 'w') as outfile:
            for row in data:
                outfile.write('\t'.join(str(x) for x in row) + '\n')

    def upsert(self, devid, objid, propid, value):
        if _debug: Snapshot._debug("upsert %r %r %r %r", devid, objid, propid, value)

        key = (devid, objid, propid)
        if key not in self.data:
            if _debug: Snapshot._debug("    - new key")
            self.data[key] = (1, value)
        else:
            version, old_value = self.data[key]
            if value != old_value:
                if _debug: Snapshot._debug("    - new value")
                self.data[key] = (version+1, value)

    def get_value(self, devid, objid, propid):
        if _debug: Snapshot._debug("get_value %r %r %r", devid, objid, propid)

        key = (devid, objid, propid)
        if key not in self.data:
            return None
        else:
            return self.data[key][1]

#
#   DiscoverNetworkServiceElement
#

@bacpypes_debugging
class DiscoverNetworkServiceElement(NetworkServiceElement):

    def __init__(self):
        if _debug: DiscoverNetworkServiceElement._debug("__init__")
        NetworkServiceElement.__init__(self)

        # no pending request
        self._request = None

    def request(self, adapter, npdu):
        if _debug: DiscoverNetworkServiceElement._debug("request %r %r", adapter, npdu)

        # save a copy of the request
        self._request = npdu

        # forward it along
        NetworkServiceElement.request(self, adapter, npdu)

    def indication(self, adapter, npdu):
        if _debug: DiscoverNetworkServiceElement._debug("indication %r %r", adapter, npdu)

        if isinstance(npdu, IAmRouterToNetwork):
            if interactive:
                print("{} router to {}".format(npdu.pduSource, npdu.iartnNetworkList))

        elif isinstance(npdu, InitializeRoutingTableAck):
            if interactive:
                print("{} routing table".format(npdu.pduSource))
                for rte in npdu.irtaTable:
                    print("    {} {} {}".format(rte.rtDNET, rte.rtPortID, rte.rtPortInfo))

        elif isinstance(npdu, NetworkNumberIs):
            if interactive:
                print("{} network number is {}".format(npdu.pduSource, npdu.nniNet))

        # forward it along
        NetworkServiceElement.indication(self, adapter, npdu)

    def response(self, adapter, npdu):
        if _debug: DiscoverNetworkServiceElement._debug("response %r %r", adapter, npdu)

        # forward it along
        NetworkServiceElement.response(self, adapter, npdu)

    def confirmation(self, adapter, npdu):
        if _debug: DiscoverNetworkServiceElement._debug("confirmation %r %r", adapter, npdu)

        # forward it along
        NetworkServiceElement.confirmation(self, adapter, npdu)

#
#   DiscoverApplication
#

@bacpypes_debugging
class DiscoverApplication(ApplicationIOController, WhoIsIAmServices, ReadWritePropertyServices):

    def __init__(self, localDevice, localAddress, deviceInfoCache=None, aseID=None):
        if _debug: DiscoverApplication._debug("__init__ %r %r deviceInfoCache=%r aseID=%r", localDevice, localAddress, deviceInfoCache, aseID)
        ApplicationIOController.__init__(self, localDevice, localAddress, deviceInfoCache, aseID=aseID)

        # local address might be useful for subclasses
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)

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
        self.nse = DiscoverNetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the BIP stack to the network, no network number
        self.nsap.bind(self.bip, address=self.localAddress)

        # keep track of requests to line up responses
        self._request = None

    def close_socket(self):
        if _debug: DiscoverApplication._debug("close_socket")

        # pass to the multiplexer, then down to the sockets
        self.mux.close_socket()

    def request(self, apdu):
        if _debug: DiscoverApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu

        # forward it along
        super(DiscoverApplication, self).request(apdu)

    def indication(self, apdu):
        if _debug: DiscoverApplication._debug("indication %r", apdu)

        # forward it along
        super(DiscoverApplication, self).indication(apdu)

    def response(self, apdu):
        if _debug: DiscoverApplication._debug("response %r", apdu)

        # forward it along
        super(DiscoverApplication, self).response(apdu)

    def confirmation(self, apdu):
        if _debug: DiscoverApplication._debug("confirmation %r", apdu)

        # forward it along
        super(DiscoverApplication, self).confirmation(apdu)

    def do_IAmRequest(self, apdu):
        if _debug: DiscoverApplication._debug("do_IAmRequest %r", apdu)

        if not isinstance(self._request, WhoIsRequest):
            if _debug: DiscoverApplication._debug("    - no pending who-is")
            return

        device_instance = apdu.iAmDeviceIdentifier[1]
        if (self._request.deviceInstanceRangeLowLimit is not None) and \
                (device_instance < self._request.deviceInstanceRangeLowLimit):
            return
        if (self._request.deviceInstanceRangeHighLimit is not None) and \
                (device_instance > self._request.deviceInstanceRangeHighLimit):
            return

        # print out something
        if interactive:
            print("{} @ {}".format(device_instance, apdu.pduSource))

        # update the snapshot database
        snapshot.upsert(
            apdu.iAmDeviceIdentifier[1], '-', 'address',
            str(apdu.pduSource),
            )
        snapshot.upsert(
            apdu.iAmDeviceIdentifier[1], '-', 'maxAPDULengthAccepted',
            str(apdu.maxAPDULengthAccepted),
            )
        snapshot.upsert(
            apdu.iAmDeviceIdentifier[1], '-', 'segmentationSupported',
            apdu.segmentationSupported,
            )

#
#   DiscoverConsoleCmd
#

@bacpypes_debugging
class DiscoverConsoleCmd(ConsoleCmd):

    def do_wirtn(self, args):
        """
        wirtn [ <addr> ] [ <net> ]

        Send a Who-Is-Router-To-Network message.  If <addr> is not specified
        the message is locally broadcast.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_wirtn %r", args)

        # build a request
        try:
            request = WhoIsRouterToNetwork()
            if not args:
                request.pduDestination = LocalBroadcast()
            elif args[0].isdigit():
                request.pduDestination = LocalBroadcast()
                request.wirtnNetwork = int(args[0])
            else:
                request.pduDestination = Address(args[0])
                if (len(args) > 1):
                    request.wirtnNetwork = int(args[1])
        except:
            print("invalid arguments")
            return

        # give it to the network service element
        this_application.nse.request(this_application.nsap.local_adapter, request)

        # sleep for responses
        time.sleep(3.0)

    def do_irt(self, args):
        """
        irt <addr>

        Send an empty Initialize-Routing-Table message to an address, a router
        will return an acknowledgement with its routing table configuration.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_irt %r", args)

        # build a request
        try:
            request = InitializeRoutingTable()
            request.pduDestination = Address(args[0])
        except:
            print("invalid arguments")
            return

        # give it to the network service element
        this_application.nse.request(this_application.nsap.local_adapter, request)

    def do_winn(self, args):
        """
        winn [ <addr> ]

        Send a What-Is-Network-Number message.  If the address is unspecified
        the message is locally broadcast.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_winn %r", args)

        # build a request
        try:
            request = WhatIsNetworkNumber()
            if (len(args) > 0):
                request.pduDestination = Address(args[0])
            else:
                request.pduDestination = LocalBroadcast()
        except:
            print("invalid arguments")
            return

        # give it to the network service element
        this_application.nse.request(this_application.nsap.local_adapter, request)

        # sleep for responses
        time.sleep(3.0)

    def do_whois(self, args):
        """
        whois [ <addr> ] [ <lolimit> <hilimit> ]

        Send a Who-Is Request and wait 3 seconds for the I-Am "responses" to
        be returned.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_whois %r", args)

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
            if _debug: DiscoverConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: DiscoverConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # sleep for responses
            time.sleep(3.0)

        except Exception as err:
            DiscoverConsoleCmd._exception("exception: %r", err)

    def do_iam(self, args):
        """
        iam [ <addr> ]

        Send an I-Am request.  If the address is unspecified the message is
        locally broadcast.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_iam %r", args)

        try:
            # build a request
            request = IAmRequest()
            if (len(args) == 1):
                request.pduDestination = Address(args[0])
            else:
                request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = this_device.objectIdentifier
            request.maxAPDULengthAccepted = this_device.maxApduLengthAccepted
            request.segmentationSupported = this_device.segmentationSupported
            request.vendorID = this_device.vendorIdentifier
            if _debug: DiscoverConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: DiscoverConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

        except Exception as err:
            DiscoverConsoleCmd._exception("exception: %r", err)

    def do_rp(self, args):
        """
        rp <devid> <objid> <prop> [ <indx> ]

        Send a Read-Property request to a device identified by its device
        identifier.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_rp %r", args)

        try:
            devid, obj_id, prop_id = args[:3]

            devid = int(devid)
            obj_id = ObjectIdentifier(obj_id).value

            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # map the devid identifier to an address from the database
            addr = snapshot.get_value(devid, '-', 'address')
            if not addr:
                raise ValueError("unknown device")
            if _debug: DiscoverConsoleCmd._debug("    - addr: %r", addr)

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 4:
                request.propertyArrayIndex = int(args[3])
            if _debug: DiscoverConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: DiscoverConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for error/reject/abort
            if iocb.ioError:
                if interactive:
                    print(str(iocb.ioError))

            # do something for success
            elif iocb.ioResponse:
                apdu = iocb.ioResponse
                if _debug: DiscoverConsoleCmd._debug("    - apdu: %r", apdu)

                # should be an ack
                if not isinstance(apdu, ReadPropertyACK):
                    if _debug: DiscoverConsoleCmd._debug("    - not an ack")
                    return

                # find the datatype
                datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
                if _debug: DiscoverConsoleCmd._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                    if apdu.propertyArrayIndex == 0:
                        datatype = Unsigned
                    else:
                        datatype = datatype.subtype
                    if _debug: DiscoverConsoleCmd._debug("    - datatype: %r", datatype)
                
                value = apdu.propertyValue.cast_out(datatype)
                if _debug: DiscoverConsoleCmd._debug("    - value: %r", value)

                # convert the value to a string
                if hasattr(value, 'dict_contents'):
                    dict_contents = value.dict_contents(as_class=OrderedDict)
                    str_value = json.dumps(dict_contents)
                else:
                    str_value = str(value)
                if interactive:
                    print(str_value)

                # save it in the snapshot
                snapshot.upsert(devid, '{}:{}'.format(*obj_id), prop_id, str_value)

            # do something with nothing?
            else:
                if _debug: DiscoverConsoleCmd._debug("    - ioError or ioResponse expected")

        except Exception as error:
            DiscoverConsoleCmd._exception("exception: %r", error)

    def do_rpm(self, args):
        """
        rpm <devid> ( <objid> ( <prop> [ <indx> ] )... )...

        Send a Read-Property-Multiple request to a device identified by its
        device identifier.
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_rpm %r", args)

        try:
            i = 0
            devid = int(args[i])
            if _debug: DiscoverConsoleCmd._debug("    - devid: %r", devid)
            i += 1

            # map the devid identifier to an address from the database
            addr = snapshot.get_value(devid, '-', 'address')
            if not addr:
                raise ValueError("unknown device")
            if _debug: DiscoverConsoleCmd._debug("    - addr: %r", addr)

            read_access_spec_list = []
            while i < len(args):
                obj_id = ObjectIdentifier(args[i]).value
                if _debug: DiscoverConsoleCmd._debug("    - obj_id: %r", obj_id)
                i += 1

                prop_reference_list = []
                while i < len(args):
                    prop_id = args[i]
                    if _debug: DiscoverConsoleCmd._debug("    - prop_id: %r", prop_id)
                    if prop_id not in PropertyIdentifier.enumerations:
                        break

                    i += 1
                    if prop_id in ('all', 'required', 'optional'):
                        pass
                    else:
                        datatype = get_datatype(obj_id[0], prop_id)
                        if not datatype:
                            raise ValueError("invalid property for object type")

                    # build a property reference
                    prop_reference = PropertyReference(
                        propertyIdentifier=prop_id,
                        )

                    # check for an array index
                    if (i < len(args)) and args[i].isdigit():
                        prop_reference.propertyArrayIndex = int(args[i])
                        i += 1

                    # add it to the list
                    prop_reference_list.append(prop_reference)

                # check for at least one property
                if not prop_reference_list:
                    raise ValueError("provide at least one property")

                # build a read access specification
                read_access_spec = ReadAccessSpecification(
                    objectIdentifier=obj_id,
                    listOfPropertyReferences=prop_reference_list,
                    )

                # add it to the list
                read_access_spec_list.append(read_access_spec)

            # check for at least one
            if not read_access_spec_list:
                raise RuntimeError("at least one read access specification required")

            # build the request
            request = ReadPropertyMultipleRequest(
                listOfReadAccessSpecs=read_access_spec_list,
                )
            request.pduDestination = Address(addr)
            if _debug: DiscoverConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: DiscoverConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse
                if _debug: DiscoverConsoleCmd._debug("    - apdu: %r", apdu)

                # should be an ack
                if not isinstance(apdu, ReadPropertyMultipleACK):
                    if _debug: DiscoverConsoleCmd._debug("    - not an ack")
                    return

                # loop through the results
                for result in apdu.listOfReadAccessResults:
                    # here is the object identifier
                    objectIdentifier = result.objectIdentifier
                    if _debug: DiscoverConsoleCmd._debug("    - objectIdentifier: %r", objectIdentifier)

                    # now come the property values per object
                    for element in result.listOfResults:
                        # get the property and array index
                        propertyIdentifier = element.propertyIdentifier
                        if _debug: DiscoverConsoleCmd._debug("    - propertyIdentifier: %r", propertyIdentifier)
                        propertyArrayIndex = element.propertyArrayIndex
                        if _debug: DiscoverConsoleCmd._debug("    - propertyArrayIndex: %r", propertyArrayIndex)

                        # here is the read result
                        readResult = element.readResult

                        property_label = str(propertyIdentifier)
                        if propertyArrayIndex is not None:
                            property_label += "[" + str(propertyArrayIndex) + "]"

                        # check for an error
                        if readResult.propertyAccessError is not None:
                            if interactive:
                                print("{} ! {}".format(property_label, readResult.propertyAccessError))

                        else:
                            # here is the value
                            propertyValue = readResult.propertyValue

                            # find the datatype
                            datatype = get_datatype(objectIdentifier[0], propertyIdentifier)
                            if _debug: DiscoverConsoleCmd._debug("    - datatype: %r", datatype)
                            if not datatype:
                                str_value = '?'
                            else:
                                # special case for array parts, others are managed by cast_out
                                if issubclass(datatype, Array) and (propertyArrayIndex is not None):
                                    if propertyArrayIndex == 0:
                                        datatype = Unsigned
                                    else:
                                        datatype = datatype.subtype
                                    if _debug: DiscoverConsoleCmd._debug("    - datatype: %r", datatype)

                                value = propertyValue.cast_out(datatype)
                                if _debug: DiscoverConsoleCmd._debug("    - value: %r", value)

                                # convert the value to a string
                                if hasattr(value, 'dict_contents'):
                                    dict_contents = value.dict_contents(as_class=OrderedDict)
                                    str_value = json.dumps(dict_contents)
                                else:
                                    str_value = str(value)

                            if interactive:
                                print("{}: {}".format(property_label, str_value))

                            # save it in the snapshot
                            snapshot.upsert(devid, '{}:{}'.format(*objectIdentifier), property_label, str_value)

            # do something for error/reject/abort
            if iocb.ioError:
                if interactive:
                    print(str(iocb.ioError))

        except Exception as error:
            DiscoverConsoleCmd._exception("exception: %r", error)

#
#   __main__
#

def main():
    global args, this_device, this_application, snapshot

    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # input file for exiting configuration
    parser.add_argument("infile",
        default="-",
        help="input file",
        )

    # output file for discovered configuration
    parser.add_argument("outfile", nargs='?',
        default='-unspecified-',
        help="output file",
        )

    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = DiscoverApplication(
        this_device, args.ini.address,
        )
    if _debug: _log.debug("    - this_application: %r", this_application)

    # make a snapshot 'database'
    snapshot = Snapshot()

    # read in an existing snapshot
    if args.infile != '-':
        snapshot.read_file(args.infile)

    # make a console
    this_console = DiscoverConsoleCmd()
    _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

    # write out the snapshot, outfile defaults to infile if not specified
    if args.outfile == '-unspecified-':
        args.outfile = args.infile
    if args.outfile != '-':
        snapshot.write_file(args.outfile)

if __name__ == "__main__":
    main()
