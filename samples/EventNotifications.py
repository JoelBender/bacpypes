#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking to save and
restore a recipient list from a notification class object, or re-write one to
the local device.  It also listens and acknowledges incoming event notifications.
"""

import os
import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.apdu import SimpleAckPDU, \
    ReadPropertyRequest, ReadPropertyACK, WritePropertyRequest
from bacpypes.basetypes import Destination, Recipient
from bacpypes.constructeddata import ListOf, Any

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None
saved_recipent_list = None

# shortcut type
ListOfDestination = ListOf(Destination)

#
#   EventNotificationApplication
#

@bacpypes_debugging
class EventNotificationApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: EventNotificationApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

    def do_ConfirmedEventNotificationRequest(self, apdu):
        if _debug: EventNotificationApplication._debug("do_ConfirmedEventNotificationRequest %r", apdu)

        # dump the APDU contents
        apdu.debug_contents(file=sys.stdout)

        # double check the process identifier
        if apdu.processIdentifier != os.getpid():
            print("note: not for this process")

        # success
        self.response(SimpleAckPDU(context=apdu))

    def do_UnconfirmedEventNotificationRequest(self, apdu):
        if _debug: EventNotificationApplication._debug("do_UnconfirmedEventNotificationRequest %r %r", apdu)

        # dump the APDU contents
        apdu.debug_contents(file=sys.stdout)

        # double check the process identifier
        if apdu.processIdentifier != os.getpid():
            print("note: not for this process")

#
#   EventNotificationConsoleCmd
#

@bacpypes_debugging
class EventNotificationConsoleCmd(ConsoleCmd):

    def do_saverl(self, args):
        """saverl <addr> <inst>"""
        args = args.split()
        if _debug: EventNotificationConsoleCmd._debug("do_saverl %r", args)
        global saved_recipent_list

        try:
            addr, obj_inst = args
            obj_inst = int(obj_inst)

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=('notificationClass', obj_inst),
                propertyIdentifier='recipientList',
                )
            request.pduDestination = Address(addr)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: EventNotificationConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

            # do something for success
            elif iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, ReadPropertyACK):
                    if _debug: EventNotificationConsoleCmd._debug("    - not an ack")
                    return

                # turn the property tag list blob into a list of destinations
                saved_recipent_list = apdu.propertyValue.cast_out(ListOfDestination)

                for destination in saved_recipent_list:
                    destination.debug_contents(file=sys.stdout)

            # do something with nothing?
            else:
                if _debug: EventNotificationConsoleCmd._debug("    - ioError or ioResponse expected")

        except Exception as error:
            EventNotificationConsoleCmd._exception("exception: %r", error)

    def do_restorerl(self, args):
        """restorerl <addr> <inst>"""
        args = args.split()
        if _debug: EventNotificationConsoleCmd._debug("do_restorerl %r", args)
        global saved_recipent_list

        # make sure there is one to restore
        if not saved_recipent_list:
            print("no saved recipient list")

        addr, obj_inst = args
        obj_inst = int(obj_inst)

        # pass along to the shared function
        self.write_recipient_list(addr, obj_inst, saved_recipent_list)

    def do_writerl(self, args):
        """writerl <addr> <inst>"""
        args = args.split()
        if _debug: EventNotificationConsoleCmd._debug("do_writerl %r", args)

        addr, obj_inst = args
        obj_inst = int(obj_inst)

        # make a destination for the device identifier
        destination = Destination(
            validDays=[1, 1, 1, 1, 1, 1, 1],    # all days
            fromTime=[0, 0, 0, 0],              # midnight
            toTime=[23, 59, 59, 99],            # all day
            recipient=Recipient(device=this_device.objectIdentifier),   # this device
            processIdentifier=os.getpid(),      # this process
            issueConfirmedNotifications=True,   # confirmed service please
            transitions=[1, 1, 1],              # all transitions
            )

        # pass along to the shared function
        self.write_recipient_list(addr, obj_inst, [destination])

    def write_recipient_list(addr, obj_inst, recipent_list):
        if _debug: EventNotificationConsoleCmd._debug("write_recipient_list %r %r %r", addr, obj_inst, recipent_list)

        # the new list has just us
        recipient_list = ListOfDestination(recipent_list)
        if _debug: EventNotificationConsoleCmd._debug("    - recipient_list: %r", recipient_list)

        # build a request
        request = WritePropertyRequest(
            objectIdentifier=('notificationClass', obj_inst),
            propertyIdentifier='recipientList',
            propertyValue=Any(),
            )
        request.pduDestination = Address(addr)

        # save the value
        request.propertyValue.cast_in(recipient_list)
        if _debug: EventNotificationConsoleCmd._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        if _debug: EventNotificationConsoleCmd._debug("    - iocb: %r", iocb)

        # give it to the application
        deferred(this_application.request_io, iocb)

        # wait for it to complete
        iocb.wait()

        # do something for success
        if iocb.ioResponse:
            # should be an ack
            if not isinstance(iocb.ioResponse, SimpleAckPDU):
                if _debug: EventNotificationConsoleCmd._debug("    - not an ack")
                return

            sys.stdout.write("ack\n")

        # do something for error/reject/abort
        if iocb.ioError:
            sys.stdout.write(str(iocb.ioError) + '\n')

    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug: EventNotificationConsoleCmd._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        this_application.nsap.add_router_references(None, router_address, network_list)


#
#   main
#

def main():
    global this_device, this_application, saved_recipent_list

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = EventNotificationApplication(
        this_device, args.ini.address,
        )
    if _debug: _log.debug("    - this_application: %r", this_application)

    # make a console
    this_console = EventNotificationConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
