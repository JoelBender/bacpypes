#!/usr/bin/python3

"""
Autodiscover

This is an application to assist with the "discovery" process of finding
BACnet routers, devices, objects, and property values.  It reads and/or writes
a tab-delimited property values text file of the values that it has received.
"""

import sys
import time
import json

from collections import defaultdict, OrderedDict

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.pdu import Address, LocalBroadcast, GlobalBroadcast
from bacpypes.comm import bind
from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.task import FunctionTask
from bacpypes.iocb import IOCB, IOQController

# application layer
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array, ArrayOf
from bacpypes.basetypes import (
    PropertyIdentifier,
    ServicesSupported,
    )
from bacpypes.object import (
    get_object_class,
    get_datatype,
    DeviceObject,
    )

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

# device information
device_profile = defaultdict(DeviceObject)

# print statements just for interactive
interactive = sys.stdin.isatty()

# lists of things to do
network_path_to_do_list = None
who_is_to_do_list = None
application_to_do_list = None

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
#   ToDoItem
#

@bacpypes_debugging
class ToDoItem:

    def __init__(self, _thread=None, _delay=None):
        if _debug: ToDoItem._debug("__init__")

        # basic status information
        self._completed = False

        # may depend on another item to complete, may have a delay
        self._thread = _thread
        self._delay = _delay

    def prepare(self):
        if _debug: ToDoItem._debug("prepare")
        raise NotImplementedError

    def complete(self, iocb):
        if _debug: ToDoItem._debug("complete %r", iocb)
        self._completed = True

#
#   ToDoList
#

@bacpypes_debugging
class ToDoList:

    def __init__(self, controller, active_limit=1):
        if _debug: ToDoList._debug("__init__")

        # save a reference to the controller for workers
        self.controller = controller

        # limit to the number of active workers
        self.active_limit = active_limit

        # no workers, nothing active
        self.pending = []
        self.active = set()

        # launch already deferred
        self.launch_deferred = False

    def append(self, item):
        if _debug: ToDoList._debug("append %r", item)

        # add the item to the list of pending items
        self.pending.append(item)

        # if an item can be started, schedule to launch it
        if len(self.active) < self.active_limit and not self.launch_deferred:
            if _debug: ToDoList._debug("    - will launch")

            self.launch_deferred = True
            deferred(self.launch)

    def launch(self):
        if _debug: ToDoList._debug("launch")

        # find some workers and launch them
        while self.pending and (len(self.active) < self.active_limit):
            # look for the next to_do_item that can be started
            for i, item in enumerate(self.pending):
                if not item._thread:
                    break
                if item._thread._completed:
                    break
            else:
                if _debug: ToDoList._debug("    - waiting")
                break
            if _debug: ToDoList._debug("    - item: %r", item)

            # remove it from the pending list, add it to active
            del self.pending[i]
            self.active.add(item)

            # prepare it and capture the IOCB
            iocb = item.prepare()
            if _debug: ToDoList._debug("    - iocb: %r", iocb)

            # break the reference to the completed to_do_item
            item._thread = None
            iocb._to_do_item = item

            # add our completion routine
            iocb.add_callback(self.complete)

            # submit it to our controller
            self.controller.request_io(iocb)

        # clear the deferred flag
        self.launch_deferred = False
        if _debug: ToDoList._debug("    - done launching")

        # check for idle
        if (not self.active) and (not self.pending):
            self.idle()

    def complete(self, iocb):
        if _debug: ToDoList._debug("complete %r", iocb)

        # extract the to_do_item
        item = iocb._to_do_item
        if _debug: ToDoList._debug("    - item: %r", item)

        # if the item has a delay, schedule to call it later
        if item._delay:
            task = FunctionTask(self._delay_complete, item, iocb)
            task.install_task(delta=item._delay)
            if _debug: ToDoList._debug("    - task: %r", task)
        else:
            self._delay_complete(item, iocb)

    def _delay_complete(self, item, iocb):
        if _debug: ToDoList._debug("_delay_complete %r %r", item, iocb)

        # tell the item it completed, remove it from active
        item.complete(iocb)
        self.active.remove(item)

        # find another to_do_item
        if not self.launch_deferred:
            if _debug: ToDoList._debug("    - will launch")

            self.launch_deferred = True
            deferred(self.launch)

    def idle(self):
        if _debug: ToDoList._debug("idle")

#
#   DiscoverNetworkServiceElement
#

@bacpypes_debugging
class DiscoverNetworkServiceElement(NetworkServiceElement, IOQController):

    def __init__(self):
        if _debug: DiscoverNetworkServiceElement._debug("__init__")
        NetworkServiceElement.__init__(self)
        IOQController.__init__(self)

    def process_io(self, iocb):
        if _debug: DiscoverNetworkServiceElement._debug("process_io %r", iocb)

        # this request is active
        self.active_io(iocb)

        # reference the service access point
        sap = self.elementService
        if _debug: NetworkServiceElement._debug("    - sap: %r", sap)

        # the iocb contains an NPDU, pass it along to the local adapter
        self.request(sap.local_adapter, iocb.args[0])

    def indication(self, adapter, npdu):
        if _debug: DiscoverNetworkServiceElement._debug("indication %r %r", adapter, npdu)
        global network_path_to_do_list

        if not self.active_iocb:
            pass

        elif isinstance(npdu, IAmRouterToNetwork):
            if interactive:
                print("{} router to {}".format(npdu.pduSource, npdu.iartnNetworkList))

            # reference the request
            request = self.active_iocb.args[0]
            if isinstance(request, WhoIsRouterToNetwork):
                if request.wirtnNetwork in npdu.iartnNetworkList:
                    self.complete_io(self.active_iocb, npdu.pduSource)

        elif isinstance(npdu, InitializeRoutingTableAck):
            if interactive:
                print("{} routing table".format(npdu.pduSource))
                for rte in npdu.irtaTable:
                    print("    {} {} {}".format(rte.rtDNET, rte.rtPortID, rte.rtPortInfo))

            # reference the request
            request = self.active_iocb.args[0]
            if isinstance(request, InitializeRoutingTable):
                if npdu.pduSource == request.pduDestination:
                    self.complete_io(self.active_iocb, npdu.irtaTable)

        elif isinstance(npdu, NetworkNumberIs):
            if interactive:
                print("{} network number is {}".format(npdu.pduSource, npdu.nniNet))

            # reference the request
            request = self.active_iocb.args[0]
            if isinstance(request, WhatIsNetworkNumber):
                self.complete_io(self.active_iocb, npdu.nniNet)

        # forward it along
        NetworkServiceElement.indication(self, adapter, npdu)

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

    def close_socket(self):
        if _debug: DiscoverApplication._debug("close_socket")

        # pass to the multiplexer, then down to the sockets
        self.mux.close_socket()

    def do_IAmRequest(self, apdu):
        if _debug: DiscoverApplication._debug("do_IAmRequest %r", apdu)
        global who_is_to_do_list

        # pass it along to line up with active requests
        who_is_to_do_list.received_i_am(apdu)

#
#   WhoIsToDo
#

@bacpypes_debugging
class WhoIsToDo(ToDoItem):

    def __init__(self, addr, lolimit, hilimit):
        if _debug: WhoIsToDo._debug("__init__ %r %r %r", addr, lolimit, hilimit)
        ToDoItem.__init__(self, _delay=3.0)

        # save the parameters
        self.addr = addr
        self.lolimit = lolimit
        self.hilimit = hilimit

        # hold on to the request and make a placeholder for responses
        self.request = None
        self.i_am_responses = []

        # give it to the list
        who_is_to_do_list.append(self)

    def prepare(self):
        if _debug: WhoIsToDo._debug("prepare(%r %r %r)", self.addr, self.lolimit, self.hilimit)

        # build a request
        self.request = WhoIsRequest(
            destination=self.addr,
            deviceInstanceRangeLowLimit=self.lolimit,
            deviceInstanceRangeHighLimit=self.hilimit,
            )
        if _debug: WhoIsToDo._debug("    - request: %r", self.request)

        # build an IOCB
        iocb = IOCB(self.request)
        if _debug: WhoIsToDo._debug("    - iocb: %r", iocb)

        return iocb

    def complete(self, iocb):
        if _debug: WhoIsToDo._debug("complete %r", iocb)

        # process the responses
        for apdu in self.i_am_responses:
            device_instance = apdu.iAmDeviceIdentifier[1]

            # print out something
            if interactive:
                print("{} @ {}".format(device_instance, apdu.pduSource))

            # update the snapshot database
            snapshot.upsert(
                device_instance, '-', 'address',
                str(apdu.pduSource),
                )
            snapshot.upsert(
                device_instance, '-', 'maxAPDULengthAccepted',
                str(apdu.maxAPDULengthAccepted),
                )
            snapshot.upsert(
                device_instance, '-', 'segmentationSupported',
                apdu.segmentationSupported,
                )

            # read stuff
            ReadServicesSupported(device_instance)
            ReadObjectList(device_instance)

        # pass along
        ToDoItem.complete(self, iocb)

#
#   WhoIsToDoList
#

@bacpypes_debugging
class WhoIsToDoList(ToDoList):

    def received_i_am(self, apdu):
        if _debug: WhoIsToDoList._debug("received_i_am %r", apdu)

        # line it up with an active item
        for item in self.active:
            if _debug: WhoIsToDoList._debug("    - item: %r", item)

            # check the source against the request
            if item.addr.addrType == Address.localBroadcastAddr:
                if apdu.pduSource.addrType != Address.localStationAddr:
                    if _debug: WhoIsToDoList._debug("    - not a local station")
                    continue

            elif item.addr.addrType == Address.localStationAddr:
                if apdu.pduSource != item.addr:
                    if _debug: WhoIsToDoList._debug("    - not from station")
                    continue

            elif item.addr.addrType == Address.remoteBroadcastAddr:
                if apdu.pduSource.addrType != Address.remoteStationAddr:
                    if _debug: WhoIsToDoList._debug("    - not a remote station")
                    continue
                if apdu.pduSource.addrNet != item.addr.addrNet:
                    if _debug: WhoIsToDoList._debug("    - not from remote net")
                    continue

            elif item.addr.addrType == Address.remoteStationAddr:
                if apdu.pduSource != item.addr:
                    if _debug: WhoIsToDoList._debug("    - not correct remote station")
                    continue

            # check the range restriction
            device_instance = apdu.iAmDeviceIdentifier[1]
            if (item.lolimit is not None) and (device_instance < item.lolimit):
                if _debug: WhoIsToDoList._debug("    - lo limit")
                continue
            if (item.hilimit is not None) and (device_instance > item.hilimit):
                if _debug: WhoIsToDoList._debug("    - hi limit")
                continue

            # debug in case something kicked it out
            if _debug: WhoIsToDoList._debug("    - passed")

            # save this response
            item.i_am_responses.append(apdu)

    def idle(self):
        if _debug: WhoIsToDoList._debug("idle")

#
#   ApplicationToDoList
#

@bacpypes_debugging
class ApplicationToDoList(ToDoList):

    def __init__(self):
        if _debug: ApplicationToDoList._debug("__init__")
        global this_application

        ToDoList.__init__(self, this_application)

#
#   ReadPropertyToDo
#

@bacpypes_debugging
class ReadPropertyToDo(ToDoItem):

    def __init__(self, devid, objid, propid, index=None):
        if _debug: ReadPropertyToDo._debug("__init__ %r %r %r index=%r", devid, objid, propid, index)
        ToDoItem.__init__(self)

        # save the parameters
        self.devid = devid
        self.objid = objid
        self.propid = propid
        self.index = index

        # give it to the list
        application_to_do_list.append(self)

    def prepare(self):
        if _debug: ReadPropertyToDo._debug("prepare(%r %r %r)", self.devid, self.objid, self.propid)

        # map the devid identifier to an address from the database
        addr = snapshot.get_value(self.devid, '-', 'address')
        if not addr:
            raise ValueError("unknown device")
        if _debug: ReadPropertyToDo._debug("    - addr: %r", addr)

        # build a request
        request = ReadPropertyRequest(
            destination=Address(addr),
            objectIdentifier=self.objid,
            propertyIdentifier=self.propid,
            )

        if self.index is not None:
            request.propertyArrayIndex = self.index
        if _debug: ReadPropertyToDo._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        if _debug: ReadPropertyToDo._debug("    - iocb: %r", iocb)

        return iocb

    def complete(self, iocb):
        if _debug: ReadPropertyToDo._debug("complete %r", iocb)

        # do something for error/reject/abort
        if iocb.ioError:
            if interactive:
                print("{} error: {}".format(self.propid, iocb.ioError))

            # do something more
            self.returned_error(iocb.ioError)

        # do something for success
        elif iocb.ioResponse:
            apdu = iocb.ioResponse

            # should be an ack
            if not isinstance(apdu, ReadPropertyACK):
                if _debug: ReadPropertyToDo._debug("    - not an ack")
                return

            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug: ReadPropertyToDo._debug("    - datatype: %r", datatype)
            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    datatype = Unsigned
                else:
                    datatype = datatype.subtype
                if _debug: ReadPropertyToDo._debug("    - datatype: %r", datatype)
            
            value = apdu.propertyValue.cast_out(datatype)
            if _debug: ReadPropertyToDo._debug("    - value: %r", value)

            # convert the value to a string
            if hasattr(value, 'dict_contents'):
                dict_contents = value.dict_contents(as_class=OrderedDict)
                str_value = json.dumps(dict_contents)
            else:
                str_value = str(value)
            if interactive:
                print(str_value)

            # make a pretty property identifier
            str_prop = apdu.propertyIdentifier
            if apdu.propertyArrayIndex is not None:
                str_prop += "[{}]".format(apdu.propertyArrayIndex)

            # save it in the snapshot
            snapshot.upsert(self.devid, '{}:{}'.format(*apdu.objectIdentifier), str_prop, str_value)

            # do something more
            self.returned_value(value)

        # do something with nothing?
        else:
            if _debug: ReadPropertyToDo._debug("    - ioError or ioResponse expected")

    def returned_error(self, error):
        if _debug: ReadPropertyToDo._debug("returned_error %r", error)

    def returned_value(self, value):
        if _debug: ReadPropertyToDo._debug("returned_value %r", value)

#
#   ReadServicesSupported
#

@bacpypes_debugging
class ReadServicesSupported(ReadPropertyToDo):

    def __init__(self, devid):
        if _debug: ReadServicesSupported._debug("__init__ %r", devid)
        ReadPropertyToDo.__init__(self, devid, ('device', devid), 'protocolServicesSupported')

    def returned_value(self, value):
        if _debug: ReadServicesSupported._debug("returned_value %r", value)

        # build a value
        services_supported = ServicesSupported(value)
        print("{} supports rpm: {}".format(self.devid, services_supported['readPropertyMultiple']))

        # device profile
        devobj = device_profile[self.devid]
        devobj.protocolServicesSupported = services_supported

#
#   ReadObjectList
#

@bacpypes_debugging
class ReadObjectList(ReadPropertyToDo):

    def __init__(self, devid):
        if _debug: ReadObjectList._debug("__init__ %r", devid)
        ReadPropertyToDo.__init__(self, devid, ('device', devid), 'objectList')

    def returned_error(self, error):
        if _debug: ReadObjectList._debug("returned_error %r", error)

        # try reading the length of the list
        ReadObjectListLen(self.devid)

    def returned_value(self, value):
        if _debug: ReadObjectList._debug("returned_value %r", value)

        # update the device profile
        devobj = device_profile[self.devid]
        devobj.objectList = ArrayOf(ObjectIdentifier)(value)

        # read the properties of the objects
        for objid in value:
            ReadObjectProperties(self.devid, objid)

#
#   ReadPropertyMultipleToDo
#

@bacpypes_debugging
class ReadPropertyMultipleToDo(ToDoItem):

    def __init__(self, devid, objid, proplist):
        if _debug: ReadPropertyMultipleToDo._debug("__init__ %r %r %r", devid, objid, proplist)
        ToDoItem.__init__(self)

        # save the parameters
        self.devid = devid
        self.objid = objid
        self.proplist = proplist

        # give it to the list
        application_to_do_list.append(self)

    def prepare(self):
        if _debug: ReadPropertyMultipleToDo._debug("prepare(%r %r %r)", self.devid, self.objid, self.proplist)

        # map the devid identifier to an address from the database
        addr = snapshot.get_value(self.devid, '-', 'address')
        if not addr:
            raise ValueError("unknown device")
        if _debug: ReadPropertyMultipleToDo._debug("    - addr: %r", addr)

        prop_reference_list = [PropertyReference(propertyIdentifier=propid) for propid in self.proplist]

        # build a read access specification
        read_access_spec = ReadAccessSpecification(
            objectIdentifier=self.objid,
            listOfPropertyReferences=prop_reference_list,
            )

        # build the request
        request = ReadPropertyMultipleRequest(
            destination=Address(addr),
            listOfReadAccessSpecs=[read_access_spec],
            )
        if _debug: ReadPropertyMultipleToDo._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        if _debug: ReadPropertyMultipleToDo._debug("    - iocb: %r", iocb)

        return iocb

    def complete(self, iocb):
        if _debug: ReadPropertyMultipleToDo._debug("complete %r", iocb)

        # do something for error/reject/abort
        if iocb.ioError:
            if interactive:
                print(str(iocb.ioError))

            # do something more
            self.returned_error(iocb.ioError)

        # do something for success
        elif iocb.ioResponse:
            apdu = iocb.ioResponse

            # should be an ack
            if not isinstance(apdu, ReadPropertyMultipleACK):
                if _debug: ReadPropertyMultipleToDo._debug("    - not an ack")
                return

            # loop through the results
            for result in apdu.listOfReadAccessResults:
                # here is the object identifier
                objectIdentifier = result.objectIdentifier
                if _debug: ReadPropertyMultipleToDo._debug("    - objectIdentifier: %r", objectIdentifier)

                # now come the property values per object
                for element in result.listOfResults:
                    # get the property and array index
                    propertyIdentifier = element.propertyIdentifier
                    if _debug: ReadPropertyMultipleToDo._debug("    - propertyIdentifier: %r", propertyIdentifier)
                    propertyArrayIndex = element.propertyArrayIndex
                    if _debug: ReadPropertyMultipleToDo._debug("    - propertyArrayIndex: %r", propertyArrayIndex)

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
                        if _debug: ReadPropertyMultipleToDo._debug("    - datatype: %r", datatype)
                        if not datatype:
                            str_value = '?'
                        else:
                            # special case for array parts, others are managed by cast_out
                            if issubclass(datatype, Array) and (propertyArrayIndex is not None):
                                if propertyArrayIndex == 0:
                                    datatype = Unsigned
                                else:
                                    datatype = datatype.subtype
                                if _debug: ReadPropertyMultipleToDo._debug("    - datatype: %r", datatype)

                            value = propertyValue.cast_out(datatype)
                            if _debug: ReadPropertyMultipleToDo._debug("    - value: %r", value)

                            # convert the value to a string
                            if hasattr(value, 'dict_contents'):
                                dict_contents = value.dict_contents(as_class=OrderedDict)
                                str_value = json.dumps(dict_contents)
                            else:
                                str_value = str(value)

                        if interactive:
                            print("{}: {}".format(propertyIdentifier, str_value))

                        # save it in the snapshot
                        snapshot.upsert(self.devid, '{}:{}'.format(*objectIdentifier), str(propertyIdentifier), str_value)

        # do something with nothing?
        else:
            if _debug: ReadPropertyMultipleToDo._debug("    - ioError or ioResponse expected")

    def returned_error(self, error):
        if _debug: ReadPropertyMultipleToDo._debug("returned_error %r", error)

    def returned_value(self, value):
        if _debug: ReadPropertyMultipleToDo._debug("returned_value %r", value)

#
#   ReadObjectListLen
#

@bacpypes_debugging
class ReadObjectListLen(ReadPropertyToDo):

    def __init__(self, devid):
        if _debug: ReadObjectListLen._debug("__init__ %r", devid)
        ReadPropertyToDo.__init__(self, devid, ('device', devid), 'objectList', 0)

    def returned_error(self, error):
        if _debug: ReadObjectListLen._debug("returned_error %r", error)

    def returned_value(self, value):
        if _debug: ReadObjectListLen._debug("returned_value %r", value)

        # start with an empty list
        devobj = device_profile[self.devid]
        devobj.objectList = ArrayOf(ObjectIdentifier)()

        # read each of the individual items
        for i in range(1, value+1):
            ReadObjectListElement(self.devid, i)

#
#   ReadObjectListElement
#

@bacpypes_debugging
class ReadObjectListElement(ReadPropertyToDo):

    def __init__(self, devid, indx):
        if _debug: ReadObjectListElement._debug("__init__ %r", devid, indx)
        ReadPropertyToDo.__init__(self, devid, ('device', devid), 'objectList', indx)

    def returned_error(self, error):
        if _debug: ReadObjectListElement._debug("returned_error %r", error)

    def returned_value(self, value):
        if _debug: ReadObjectListElement._debug("returned_value %r", value)

        # update the list
        devobj = device_profile[self.devid]
        devobj.objectList.append(value)

        # read the properties of the object
        ReadObjectProperties(self.devid, value)


#
#   ReadObjectProperties
#

@bacpypes_debugging
def ReadObjectProperties(devid, objid):
    if _debug: ReadObjectProperties._debug("ReadObjectProperties %r %r", devid, objid)

    # get the profile, it contains the protocol services supported
    devobj = device_profile[devid]
    supports_rpm = devobj.protocolServicesSupported['readPropertyMultiple']
    if _debug: ReadObjectProperties._debug("    - supports rpm: %r", supports_rpm)

    # read all the properties at once if it's an option
    if supports_rpm:
        ReadPropertyMultipleToDo(devid, objid, ['all'])
    else:
        ReadObjectPropertyList(devid, objid)


#
#   ReadObjectPropertyList
#

@bacpypes_debugging
class ReadObjectPropertyList(ReadPropertyToDo):

    def __init__(self, devid, objid):
        if _debug: ReadObjectPropertyList._debug("__init__ %r", devid)
        ReadPropertyToDo.__init__(self, devid, objid, 'propertyList')

    def returned_error(self, error):
        if _debug: ReadObjectPropertyList._debug("returned_error %r", error)

        # get the class
        object_class = get_object_class(self.objid[0])
        if _debug: ReadObjectPropertyList._debug("    - object_class: %r", object_class)

        # get a list of properties, including optional ones
        object_properties = object_class._properties.keys()
        if _debug: ReadObjectPropertyList._debug("    - object_properties: %r", object_properties)

        # dont bother reading the property list, it already failed
        object_properties.remove('propertyList')

        # try to read all the properties
        for propid in object_properties:
            ReadPropertyToDo(self.devid, self.objid, propid)

    def returned_value(self, value):
        if _debug: ReadObjectPropertyList._debug("returned_value %r", value)

        # add the other properties that are always present but not
        # returned in property list
        value.extend(('objectName', 'objectType', 'objectIdentifier'))

        # read each of the individual properties
        for propid in value:
            ReadPropertyToDo(self.devid, self.objid, propid)

#
#   DiscoverConsoleCmd
#

@bacpypes_debugging
class DiscoverConsoleCmd(ConsoleCmd):

    def do_sleep(self, args):
        """
        sleep <secs>
        """
        args = args.split()
        if _debug: DiscoverConsoleCmd._debug("do_sleep %r", args)

        time.sleep(float(args[0]))

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
            # parse parameters
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

            # make an item
            item = WhoIsToDo(addr, lolimit, hilimit)
            if _debug: DiscoverConsoleCmd._debug("    - item: %r", item)

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
        global application_to_do_list

        try:
            devid, objid, propid = args[:3]

            devid = int(devid)
            objid = ObjectIdentifier(objid).value

            datatype = get_datatype(objid[0], propid)
            if not datatype:
                raise ValueError("invalid property for object type")

            if len(args) == 4:
                index = int(args[3])
            else:
                index = None

            # make something to do
            ReadPropertyToDo(devid, objid, propid, index)

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
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

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
                            snapshot.upsert(devid, '{}:{}'.format(*objectIdentifier), str(propertyIdentifier), str_value)

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
    global args, this_device, this_application, snapshot, \
        who_is_to_do_list, application_to_do_list

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

    # special lists
    # network_path_to_do_list = NetworkPathToDoList(this_application.nse)
    who_is_to_do_list = WhoIsToDoList(this_application)
    application_to_do_list = ApplicationToDoList()

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
