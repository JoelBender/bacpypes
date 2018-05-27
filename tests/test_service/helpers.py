#!/usr/bin/env python

"""
Service Helper Classes
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.comm import Client, bind
from bacpypes.pdu import Address, LocalBroadcast
from bacpypes.vlan import Network, Node

from bacpypes.app import Application
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.local.device import LocalDeviceObject

from ..state_machine import StateMachine, StateMachineGroup
from ..time_machine import reset_time_machine, run_time_machine


# some debugging
_debug = 0
_log = ModuleLogger(globals())


#
#   ApplicationNetwork
#

@bacpypes_debugging
class ApplicationNetwork(StateMachineGroup):

    def __init__(self):
        if _debug: ApplicationNetwork._debug("__init__")
        StateMachineGroup.__init__(self)

        # reset the time machine
        reset_time_machine()
        if _debug: ApplicationNetwork._debug("    - time machine reset")

        # make a little LAN
        self.vlan = Network(broadcast_address=LocalBroadcast())

        # test device object
        self.td_device_object = LocalDeviceObject(
            objectName="td",
            objectIdentifier=("device", 10),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=999,
            )

        # test device
        self.td = ApplicationStateMachine(self.td_device_object, self.vlan)
        self.append(self.td)

        # implementation under test device object
        self.iut_device_object = LocalDeviceObject(
            objectName="iut",
            objectIdentifier=("device", 20),
            maxApduLengthAccepted=1024,
            segmentationSupported='noSegmentation',
            vendorIdentifier=999,
            )

        # implementation under test
        self.iut = ApplicationStateMachine(self.iut_device_object, self.vlan)
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

        # check for success
        all_success, some_failed = super(ApplicationNetwork, self).check_for_success()
        ApplicationNetwork._debug("    - all_success, some_failed: %r, %r", all_success, some_failed)
        assert all_success


#
#   SnifferNode
#

@bacpypes_debugging
class SnifferNode(Client, StateMachine):

    def __init__(self, vlan):
        if _debug: SnifferNode._debug("__init__ %r", vlan)

        # save the name and give it a blank address
        self.name = "sniffer"
        self.address = Address()

        # continue with initialization
        Client.__init__(self)
        StateMachine.__init__(self)

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

