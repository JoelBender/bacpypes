#!/usr/bin/python

"""
BACpypes Test
-------------
"""

import os
import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ArgumentParser

from bacpypes.pdu import Address
from bacpypes.comm import bind

from bacpypes.apdu import APDU, ReadPropertyRequest, \
    ComplexAckPDU, RejectPDU, AbortPDU

from bacpypes.app import LocalDeviceObject, Application
from bacpypes.appservice import ApplicationServiceAccessPoint, StateMachineAccessPoint

from tests.state_machine import Server, StateMachine

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# defaults for testing
BACPYPES_TEST = ""
BACPYPES_TEST_OPTION = ""

# parsed test options
test_options = None


#
#   TestApplication
#

@bacpypes_debugging
class TestApplication(Application):

    def __init__(self, localDevice, localAddress, aseID=None):
        if _debug: TestApplication._debug("__init__ %r %r aseID=%r", localDevice, localAddress, aseID)
        Application.__init__(self, localDevice, localAddress, aseID)

#
#   setUp
#

@bacpypes_debugging
def setUp(argv=None):
    global test_options

    # create an argument parser
    parser = ArgumentParser(description=__doc__)

    # add an option
    parser.add_argument(
        '--option', help="this is an option",
        default=os.getenv("BACPYPES_TEST_OPTION") or BACPYPES_TEST_OPTION,
        )

    # get the debugging args and parse them
    arg_str = os.getenv("BACPYPES_TEST") or BACPYPES_TEST
    test_options = parser.parse_args(argv or arg_str.split())

    if _debug: setUp._debug("setUp")
    if _debug: setUp._debug("    - test_options: %r", test_options)

#
#   tearDown
#

@bacpypes_debugging
def tearDown():
    if _debug: tearDown._debug("tearDown")


#
#   MatchingStateMachine
#


@bacpypes_debugging
class MatchingStateMachine(Server, StateMachine):

    def __init__(self):
        if _debug: MatchingStateMachine._debug("__init__")

        Server.__init__(self)
        StateMachine.__init__(self)

    def send(self, pdu):
        if _debug: MatchingStateMachine._debug("send %r", pdu)
        self.response(pdu)

    def indication(self, pdu):
        if _debug: MatchingStateMachine._debug("indication %r", pdu)
        self.receive(pdu)

    def match_pdu(self, pdu, transition_pdu):
        if _debug: MatchingStateMachine._debug("match_pdu %r %r", pdu, transition_pdu)

        # instance types match is enough
        is_instance = isinstance(pdu, transition_pdu)
        if _debug: MatchingStateMachine._debug("    - is_instance: %r", is_instance)

        return is_instance

#
#   main
#

setUp(sys.argv[1:])

# make a device object
test_device = LocalDeviceObject(
    objectName='test_device',
    objectIdentifier=100,
    maxApduLengthAccepted=1024,
    segmentationSupported='segmentedBoth',
    vendorIdentifier=15,
    )

# make a test address
test_address = Address(1)

# create a client state machine, trapped server, and bind them together
test_application = TestApplication(test_device, test_address)

print("objects: " + str(test_application.objectIdentifier))

# get the services supported
services_supported = test_application.get_services_supported()
if _debug: _log.debug("    - services_supported: %r", services_supported)

# let the device object know
test_device.protocolServicesSupported = services_supported.value

# include a application decoder
test_asap = ApplicationServiceAccessPoint()

# pass the device object to the state machine access point so it
# can know if it should support segmentation
test_smap = StateMachineAccessPoint(test_device)

# state machine
test_server = MatchingStateMachine()

# bind everything together
bind(test_application, test_asap, test_smap, test_server)

# ==============================================================================

read_property_request = ReadPropertyRequest(
    objectIdentifier=('device', 100),
    propertyIdentifier='objectName',
    )
read_property_request.pduSource = Address(2)
# read_property_request.pduDestination = Address(1)
read_property_request.apduInvokeID = 1

print("read_property_request")
read_property_request.debug_contents()
print("")

test_apdu = APDU()
read_property_request.encode(test_apdu)

print("test_apdu")
test_apdu.debug_contents()
print("")

if 0:
    print("modify test_apdu")
    test_apdu.pduData = test_apdu.pduData[:5]
    test_apdu.debug_contents()
    print("")

# make a send transition from start to success
start_state = test_server.start_state.doc("start_state")
response_state = start_state.send(test_apdu).doc("response_state")
success_state = response_state.receive(ComplexAckPDU).doc("success_state")
success_state.success()

# run the machine
print("running")
test_server.run()
print("")

# ==============================================================================

# check for success
assert not test_server.running
assert test_server.current_state.is_success_state

tearDown()
