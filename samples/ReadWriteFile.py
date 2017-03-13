#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for commands.

The 'readrecord' and 'writerecord' commands are used with record oriented files,
and the 'readstream' and 'writestream' commands are used with stream oriented
files.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.apdu import Error, AbortPDU, \
    AtomicReadFileRequest, \
        AtomicReadFileRequestAccessMethodChoice, \
            AtomicReadFileRequestAccessMethodChoiceRecordAccess, \
            AtomicReadFileRequestAccessMethodChoiceStreamAccess, \
    AtomicReadFileACK, \
    AtomicWriteFileRequest, \
        AtomicWriteFileRequestAccessMethodChoice, \
            AtomicWriteFileRequestAccessMethodChoiceRecordAccess, \
            AtomicWriteFileRequestAccessMethodChoiceStreamAccess, \
    AtomicWriteFileACK

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# reference a simple application
this_application = None

#
#   TestConsoleCmd
#

@bacpypes_debugging
class TestConsoleCmd(ConsoleCmd):

    def do_readrecord(self, args):
        """readrecord <addr> <inst> <start> <count>"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_readrecord %r", args)

        try:
            addr, obj_inst, start_record, record_count = args

            obj_type = 'file'
            obj_inst = int(obj_inst)
            start_record = int(start_record)
            record_count = int(record_count)

            # build a request
            request = AtomicReadFileRequest(
                fileIdentifier=(obj_type, obj_inst),
                accessMethod=AtomicReadFileRequestAccessMethodChoice(
                    recordAccess=AtomicReadFileRequestAccessMethodChoiceRecordAccess(
                        fileStartRecord=start_record,
                        requestedRecordCount=record_count,
                        ),
                    ),
                )
            request.pduDestination = Address(addr)
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: TestConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, AtomicReadFileACK):
                    if _debug: TestConsoleCmd._debug("    - not an ack")
                    return

                # suck out the record data
                if apdu.accessMethod.recordAccess:
                    value = apdu.accessMethod.recordAccess.fileRecordData
                elif apdu.accessMethod.streamAccess:
                    value = apdu.accessMethod.streamAccess.fileData
                if _debug: TestConsoleCmd._debug("    - value: %r", value)

                sys.stdout.write(repr(value) + '\n')
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            TestConsoleCmd._exception("exception: %r", error)

    def do_readstream(self, args):
        """readstream <addr> <inst> <start> <count>"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_readstream %r", args)

        try:
            addr, obj_inst, start_position, octet_count = args

            obj_type = 'file'
            obj_inst = int(obj_inst)
            start_position = int(start_position)
            octet_count = int(octet_count)

            # build a request
            request = AtomicReadFileRequest(
                fileIdentifier=(obj_type, obj_inst),
                accessMethod=AtomicReadFileRequestAccessMethodChoice(
                    streamAccess=AtomicReadFileRequestAccessMethodChoiceStreamAccess(
                        fileStartPosition=start_position,
                        requestedOctetCount=octet_count,
                        ),
                    ),
                )
            request.pduDestination = Address(addr)
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: TestConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, AtomicReadFileACK):
                    if _debug: TestConsoleCmd._debug("    - not an ack")
                    return

                # suck out the record data
                if apdu.accessMethod.recordAccess:
                    value = apdu.accessMethod.recordAccess.fileRecordData
                elif apdu.accessMethod.streamAccess:
                    value = apdu.accessMethod.streamAccess.fileData
                if _debug: TestConsoleCmd._debug("    - value: %r", value)

                sys.stdout.write(repr(value) + '\n')
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            TestConsoleCmd._exception("exception: %r", error)

    def do_writerecord(self, args):
        """writerecord <addr> <inst> <start> <count> [ <data> ... ]"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_writerecord %r", args)

        try:
            addr, obj_inst, start_record, record_count = args[0:4]

            obj_type = 'file'
            obj_inst = int(obj_inst)
            start_record = int(start_record)
            record_count = int(record_count)
            record_data = [arg.encode('utf-8') for arg in list(args[4:])]

            # build a request
            request = AtomicWriteFileRequest(
                fileIdentifier=(obj_type, obj_inst),
                accessMethod=AtomicWriteFileRequestAccessMethodChoice(
                    recordAccess=AtomicWriteFileRequestAccessMethodChoiceRecordAccess(
                        fileStartRecord=start_record,
                        recordCount=record_count,
                        fileRecordData=record_data,
                        ),
                    ),
                )
            request.pduDestination = Address(addr)
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: TestConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, AtomicWriteFileACK):
                    if _debug: TestConsoleCmd._debug("    - not an ack")
                    return

                # suck out the record data
                if apdu.fileStartPosition is not None:
                    value = apdu.fileStartPosition
                elif apdu.fileStartRecord is not None:
                    value = apdu.fileStartRecord
                TestConsoleCmd._debug("    - value: %r", value)

                sys.stdout.write(repr(value) + '\n')
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            TestConsoleCmd._exception("exception: %r", error)

    def do_writestream(self, args):
        """writestream <addr> <inst> <start> <data>"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_writestream %r", args)

        try:
            addr, obj_inst, start_position, data = args

            obj_type = 'file'
            obj_inst = int(obj_inst)
            start_position = int(start_position)
            data = data.encode('utf-8')

            # build a request
            request = AtomicWriteFileRequest(
                fileIdentifier=(obj_type, obj_inst),
                accessMethod=AtomicWriteFileRequestAccessMethodChoice(
                    streamAccess=AtomicWriteFileRequestAccessMethodChoiceStreamAccess(
                        fileStartPosition=start_position,
                        fileData=data,
                        ),
                    ),
                )
            request.pduDestination = Address(addr)
            if _debug: TestConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: TestConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, AtomicWriteFileACK):
                    if _debug: TestConsoleCmd._debug("    - not an ack")
                    return

                # suck out the record data
                if apdu.fileStartPosition is not None:
                    value = apdu.fileStartPosition
                elif apdu.fileStartRecord is not None:
                    value = apdu.fileStartRecord
                TestConsoleCmd._debug("    - value: %r", value)

                sys.stdout.write(repr(value) + '\n')
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            TestConsoleCmd._exception("exception: %r", error)

#
#   __main__
#

def main():
    global this_application

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

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = TestConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
