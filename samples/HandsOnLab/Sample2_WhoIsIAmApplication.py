#!/usr/bin/env python

"""
This sample application builds on the first sample by overriding the default
processing for Who-Is and I-Am requests, counting them, then continuing on
with the regular processing.  After the run() function has completed it will
dump a formatted summary of the requests it has received.
"""

from collections import defaultdict

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# counters
who_is_counter = defaultdict(int)
i_am_counter = defaultdict(int)

#
#   WhoIsIAmApplication
#

@bacpypes_debugging
class WhoIsIAmApplication(BIPSimpleApplication):

    def __init__(self, device, address):
        if _debug: WhoIsIAmApplication._debug("__init__ %r %r", device, address)
        BIPSimpleApplication.__init__(self, device, address)

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        if _debug: WhoIsIAmApplication._debug("do_WhoIsRequest %r", apdu)

        # build a key from the source and parameters
        key = (str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
            )

        # count the times this has been received
        who_is_counter[key] += 1

        # continue with the default implementation
        BIPSimpleApplication.do_WhoIsRequest(self, apdu)

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        if _debug: WhoIsIAmApplication._debug("do_IAmRequest %r", apdu)

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource),
            apdu.iAmDeviceIdentifier[1],
            )

        # count the times this has been received
        i_am_counter[key] += 1

        # continue with the default implementation
        BIPSimpleApplication.do_IAmRequest(self, apdu)

#
#   __main__
#

def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    this_application = WhoIsIAmApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    _log.debug("running")

    run()

    _log.debug("fini")

    print("----- Who Is -----")
    for (src, lowlim, hilim), count in sorted(who_is_counter.items()):
        print("%-20s %8s %8s %4d" % (src, lowlim, hilim, count))
    print("")

    print("----- I Am -----")
    for (src, devid), count in sorted(i_am_counter.items()):
        print("%-20s %8d %4d" % (src, devid, count))
    print("")

if __name__ == "__main__":
    main()
