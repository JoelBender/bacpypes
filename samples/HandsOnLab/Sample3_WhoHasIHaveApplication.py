#!/usr/bin/env python

"""
This sample application builds on the first sample by overriding the default
processing for Who-Has and I-Have requests, counting them, then continuing on
with the regular processing.  After the run() function has completed it will
dump a formatted summary of the requests it has received.  Note that these
services are relatively rare even in large networks.
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
who_has_counter = defaultdict(int)
i_have_counter = defaultdict(int)

#
#   WhoHasIHaveApplication
#

@bacpypes_debugging
class WhoHasIHaveApplication(BIPSimpleApplication):

    def __init__(self, device, address):
        if _debug: WhoHasIHaveApplication._debug("__init__ %r %r", device, address)
        BIPSimpleApplication.__init__(self, device, address)

    def do_WhoHasRequest(self, apdu):
        """Respond to a Who-Has request."""
        if _debug: WhoHasIHaveApplication._debug("do_WhoHasRequest, %r", apdu)

        key = (str(apdu.pduSource),)
        if apdu.object.objectIdentifier is not None:
            key += (str(apdu.object.objectIdentifier),)
        elif apdu.object.objectName is not None:
            key += (apdu.object.objectName,)
        else:
            print("(rejected APDU:")
            apdu.debug_contents()
            print(")")
            return

        # count the times this has been received
        who_has_counter[key] += 1

    def do_IHaveRequest(self, apdu):
        """Respond to a I-Have request."""
        if _debug: WhoHasIHaveApplication._debug("do_IHaveRequest %r", apdu)

        key = (
            str(apdu.pduSource),
            str(apdu.deviceIdentifier),
            str(apdu.objectIdentifier),
            apdu.objectName
            )

        # count the times this has been received
        i_have_counter[key] += 1

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
    this_application = WhoHasIHaveApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    _log.debug("running")

    # run until stopped, ^C works
    run()

    _log.debug("fini")

    print("----- Who Has -----")
    for (src, objname), count in sorted(who_has_counter.items()):
        print("%-20s %-30s %4d" % (src, objname, count))
    print("")

    print("----- I Have -----")
    for (src, devid, objid, objname), count in sorted(i_have_counter.items()):
        print("%-20s %-20s %-20s %-20s %4d" % (src, devid, objid, objname, count))
    print("")

if __name__ == "__main__":
    main()
