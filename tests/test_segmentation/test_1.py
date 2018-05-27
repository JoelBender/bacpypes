#!/urs/bin/python3

"""
Test Segmentation
"""

import random
import string
import unittest

from bacpypes.debugging import ModuleLogger, bacpypes_debugging, btox, xtob
from bacpypes.consolelogging import ArgumentParser

from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import Any

from bacpypes.comm import Client, bind
from bacpypes.pdu import Address, LocalBroadcast
from bacpypes.vlan import Network, Node

from bacpypes.npdu import NPDU, npdu_types
from bacpypes.apdu import APDU, apdu_types, \
    confirmed_request_types, unconfirmed_request_types, complex_ack_types, error_types, \
    ConfirmedRequestPDU, UnconfirmedRequestPDU, \
    SimpleAckPDU, ComplexAckPDU, SegmentAckPDU, ErrorPDU, RejectPDU, AbortPDU

from bacpypes.apdu import APDU, ErrorPDU, RejectPDU, AbortPDU, \
    ConfirmedPrivateTransferRequest, ConfirmedPrivateTransferACK

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.local.device import LocalDeviceObject

from ..state_machine import StateMachine, StateMachineGroup, TrafficLog
from ..time_machine import reset_time_machine, run_time_machine

# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   ApplicationNetwork
#

@bacpypes_debugging
class ApplicationNetwork(StateMachineGroup):

    def __init__(self, td_device_object, iut_device_object):
        if _debug: ApplicationNetwork._debug("__init__ %r %r", td_device_object, iut_device_object)
        StateMachineGroup.__init__(self)

        # reset the time machine
        reset_time_machine()
        if _debug: ApplicationNetwork._debug("    - time machine reset")

        # create a traffic log
        self.traffic_log = TrafficLog()

        # make a little LAN
        self.vlan = Network(broadcast_address=LocalBroadcast())
        self.vlan.traffic_log = self.traffic_log

        # sniffer
        self.sniffer = SnifferNode(self.vlan)

        # test device
        self.td = ApplicationStateMachine(td_device_object, self.vlan)
        self.append(self.td)

        # implementation under test
        self.iut = ApplicationStateMachine(iut_device_object, self.vlan)
        self.append(self.iut)

    def run(self, time_limit=60.0):
        if _debug: ApplicationNetwork._debug("run %r", time_limit)

        # run the group
        super(ApplicationNetwork, self).run()
        if _debug: ApplicationNetwork._debug("    - group running")

        # run it for some time
        run_time_machine(time_limit)
        if _debug:
            ApplicationNetwork._debug("    - time machine finished")
            for state_machine in self.state_machines:
                ApplicationNetwork._debug("    - machine: %r", state_machine)
                for direction, pdu in state_machine.transaction_log:
                    ApplicationNetwork._debug("        %s %s", direction, str(pdu))

            # traffic log has what was processed on each vlan
            self.traffic_log.dump(ApplicationNetwork._debug)

        # check for success
        all_success, some_failed = super(ApplicationNetwork, self).check_for_success()
        ApplicationNetwork._debug("    - all_success, some_failed: %r, %r", all_success, some_failed)
        assert all_success


#
#   SnifferNode
#

@bacpypes_debugging
class SnifferNode(Client): ### , StateMachine):

    def __init__(self, vlan):
        if _debug: SnifferNode._debug("__init__ %r", vlan)

        # save the name and give it a blank address
        self.name = "sniffer"
        self.address = Address()

        # continue with initialization
        Client.__init__(self)
        ### StateMachine.__init__(self)

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

        # it's an NPDU
        npdu = NPDU()
        npdu.decode(pdu)

        # decode as a generic APDU
        apdu = APDU()
        apdu.decode(npdu)

        # "lift" the source and destination address
        if npdu.npduSADR:
            apdu.pduSource = npdu.npduSADR
        else:
            apdu.pduSource = npdu.pduSource
        if npdu.npduDADR:
            apdu.pduDestination = npdu.npduDADR
        else:
            apdu.pduDestination = npdu.pduDestination

        # make a more focused interpretation
        atype = apdu_types.get(apdu.apduType)
        if _debug: SnifferNode._debug("    - atype: %r", atype)

        xpdu = apdu
        apdu = atype()
        apdu.decode(xpdu)

        print(repr(apdu))
        apdu.debug_contents()
        print("")

#
#   ApplicationStateMachine
#

@bacpypes_debugging
class ApplicationStateMachine(Application, StateMachine):

    def __init__(self, localDevice, vlan):
        if _debug: ApplicationStateMachine._debug("__init__ %r %r", localDevice, vlan)

        # build an address and save it
        self.address = Address(localDevice.objectIdentifier[1])
        if _debug: ApplicationStateMachine._debug("    - address: %r", self.address)

        # continue with initialization
        Application.__init__(self, localDevice, self.address)
        StateMachine.__init__(self, name=localDevice.objectName)

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

        # placeholder for the result block
        self.confirmed_private_result = None

    def send(self, apdu):
        if _debug: ApplicationStateMachine._debug("send(%s) %r", self.name, apdu)

        # send the apdu down the stack
        self.request(apdu)

    def indication(self, apdu):
        if _debug: ApplicationStateMachine._debug("indication(%s) %r", self.name, apdu)

        # let the state machine know the request was received
        self.receive(apdu)

        # allow the application to process it
        super(ApplicationStateMachine, self).indication(apdu)

    def confirmation(self, apdu):
        if _debug: ApplicationStateMachine._debug("confirmation(%s) %r", self.name, apdu)

        # forward the confirmation to the state machine
        self.receive(apdu)

    def do_ConfirmedPrivateTransferRequest(self, apdu):
        if _debug: ApplicationStateMachine._debug("do_ConfirmedPrivateTransferRequest(%s) %r", self.name, apdu)

        # simple ack
        xapdu = ConfirmedPrivateTransferACK(context=apdu)
        xapdu.vendorID = 999
        xapdu.serviceNumber = 1
        xapdu.resultBlock = self.confirmed_private_result

        if _debug: ApplicationStateMachine._debug("    - xapdu: %r", xapdu)

        # send the response back
        self.response(xapdu)


@bacpypes_debugging
class TestSegmentation(unittest.TestCase):

    def test_1(self):
        """9.39.1 Unsupported Confirmed Services Test"""
        if _debug: TestSegmentation._debug("test_1")

        # client device object
        td_device_object = LocalDeviceObject(
            objectName="td",
            objectIdentifier=("device", 10),
            maxApduLengthAccepted=206,
            segmentationSupported='segmentedBoth',
            maxSegmentsAccepted=4,
            vendorIdentifier=999,
            )

        # server device object
        iut_device_object = LocalDeviceObject(
            objectName="iut",
            objectIdentifier=("device", 20),
            maxApduLengthAccepted=206,
            segmentationSupported='segmentedBoth',
            maxSegmentsAccepted=99,
            vendorIdentifier=999,
            )

        # create a network
        anet = ApplicationNetwork(td_device_object, iut_device_object)

        # client settings
        c_ndpu_len = 50
        c_len = 0

        # server settings
        s_ndpu_len = 50
        s_len = 0

        # tell the device info cache of the client about the server
        if 0:
            iut_device_info = anet.td.deviceInfoCache.get_device_info(anet.iut.address)

            # update the rest of the values
            iut_device_info.maxApduLengthAccepted = iut_device_object.maxApduLengthAccepted
            iut_device_info.segmentationSupported = iut_device_object.segmentationSupported
            iut_device_info.vendorID = iut_device_object.vendorIdentifier
            iut_device_info.maxSegmentsAccepted = iut_device_object.maxSegmentsAccepted
            iut_device_info.maxNpduLength = s_ndpu_len

        # tell the device info cache of the server device about the client
        if 0:
            td_device_info = anet.iut.deviceInfoCache.get_device_info(anet.td.address)

            # update the rest of the values
            td_device_info.maxApduLengthAccepted = td_device_object.maxApduLengthAccepted
            td_device_info.segmentationSupported = td_device_object.segmentationSupported
            td_device_info.vendorID = td_device_object.vendorIdentifier
            td_device_info.maxSegmentsAccepted = td_device_object.maxSegmentsAccepted
            td_device_info.maxNpduLength = c_ndpu_len

        # build a request string
        if c_len:
            request_string = Any(
                CharacterString(
                    ''.join(random.choice(string.lowercase) for _ in range(c_len))
                    )
                )
        else:
            request_string = None

        # response string is stuffed into the server
        if s_len:
            anet.iut.confirmed_private_result = Any(
                CharacterString(
                    ''.join(random.choice(string.lowercase) for _ in range(s_len))
                    )
                )
        else:
            anet.iut.confirmed_private_result = None

        # send the request, get it rejected
        s761 = anet.td.start_state.doc("7-6-0") \
            .send(ConfirmedPrivateTransferRequest(
                vendorID=999, serviceNumber=1,
                serviceParameters=request_string,
                destination=anet.iut.address,
                )).doc("7-6-1")

        s761.receive(ConfirmedPrivateTransferACK).doc("7-6-2") \
            .success()
        s761.receive(AbortPDU, apduAbortRejectReason=11).doc("7-6-3") \
            .success()

        # no IUT application layer matching
        anet.iut.start_state.success()

        # run the group
        anet.run()

