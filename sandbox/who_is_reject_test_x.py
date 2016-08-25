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

from bacpypes.apdu import APDU, WhoIsRequest

from bacpypes.app import LocalDeviceObject, Application
from bacpypes.appservice import ApplicationServiceAccessPoint, StateMachineAccessPoint

from tests.state_machine import ServerStateMachine

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

# include a application decoder
test_asap = ApplicationServiceAccessPoint()

# pass the device object to the state machine access point so it
# can know if it should support segmentation
test_smap = StateMachineAccessPoint(test_device)

# state machine
test_server = ServerStateMachine()

# bind everything together
bind(test_application, test_asap, test_smap, test_server)

# ==============================================================================

who_is_request = WhoIsRequest(
    deviceInstanceRangeLowLimit=0,
    deviceInstanceRangeHighLimit=4194303,
    )
print("who_is_request")
who_is_request.debug_contents()
print("")

test_apdu = APDU()
who_is_request.encode(test_apdu)

print("test_apdu")
test_apdu.debug_contents()
print("")

print("modify test_apdu")
test_apdu.pduData = test_apdu.pduData[:-1]
# test_apdu.pduData = xtob('7509006869207468657265') # CharacterString("hi there")
test_apdu.debug_contents()
print("")

# make a send transition from start to success
test_server.start_state.send(test_apdu).success()

# run the machine
print("running")
test_server.run()
print("")

# ==============================================================================

# check for success
assert not test_server.running
assert test_server.current_state.is_success_state

tearDown()
